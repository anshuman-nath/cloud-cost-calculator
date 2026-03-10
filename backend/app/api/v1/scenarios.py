"""
Scenarios API endpoints
Orchestrates: BOM fetch → price fetch → discount calculation → DB persist → response
"""
import asyncio
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.utils.database import get_db
from app.models.bom import BillOfMaterials
from app.models.scenario import CostScenario
from app.services.pricing_fetcher import (
    fetch_aws_pricing,
    fetch_azure_pricing,
    fetch_gcp_pricing,
)
from app.services.pricing_engine import (
    PricingModel,
    calculate_all_scenarios,
)

router = APIRouter(prefix="/api/v1/scenarios", tags=["Cost Scenarios"])

# ---------------------------------------------------------------------------
# Provider dispatch
# ---------------------------------------------------------------------------

FETCHER_MAP = {
    "aws":   fetch_aws_pricing,
    "azure": fetch_azure_pricing,
    "gcp":   fetch_gcp_pricing,
}


async def _fetch_price_for_service(
    provider: str,
    service: dict,
    currency: str = "USD",
) -> dict:
    """
    Dispatch to the correct pricing fetcher for one service.
    Returns the service dict enriched with payg_monthly_cost.
    """
    fetcher = FETCHER_MAP.get(provider)
    if not fetcher:
        raise ValueError(f"Unknown provider: {provider}")

    region     = service["config"].get("region", _default_region(provider))
    service_type = service["service_type"]
    config       = service["config"]

    try:
        price_result = await fetcher(
            service_type = service_type,
            config       = config,
            region       = region,
            currency     = currency,
        )
        return {
            "service_name":      service["service_name"],
            "service_type":      service_type,
            "config":            config,
            "payg_monthly_cost": price_result["monthly_cost_usd"],
            "price_details":     price_result,
        }
    except Exception as e:
        # Surface pricing errors per-service — don't silently zero out
        raise HTTPException(
            status_code=502,
            detail=(
                f"Pricing fetch failed for service '{service['service_name']}' "
                f"({provider} / {service_type} / {region}): {str(e)}"
            )
        )


def _default_region(provider: str) -> str:
    defaults = {"aws": "us-east-1", "azure": "eastus", "gcp": "us-central1"}
    return defaults.get(provider, "us-east-1")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/{bom_id}/generate", status_code=status.HTTP_201_CREATED)
async def generate_scenarios(bom_id: int, db: Session = Depends(get_db)):
    """
    Full pipeline for one BOM:
    1. Load BOM + services from DB
    2. Fetch live PAYG prices for ALL services (parallel)
    3. Apply per-provider, per-service-type discount matrix
    4. Delete existing scenarios for this BOM (regenerate clean)
    5. Persist one CostScenario row per applicable pricing model
    6. Return full comparison payload

    Returns the same structure as GET /{bom_id} for immediate UI render.
    """
    # Step 1: load BOM
    bom = db.query(BillOfMaterials).filter(BillOfMaterials.id == bom_id).first()
    if not bom:
        raise HTTPException(status_code=404, detail=f"BOM {bom_id} not found")

    if not bom.services:
        raise HTTPException(
            status_code=400,
            detail="BOM has no services. Add services before generating scenarios."
        )

    provider = bom.cloud_provider.lower()
    currency = bom.currency or "USD"

    # Step 2: fetch all PAYG prices in parallel
    fetch_tasks = [
        _fetch_price_for_service(provider, service, currency)
        for service in bom.services
    ]
    fetched_prices = await asyncio.gather(*fetch_tasks)

    # Step 3: apply discount engine
    scenario_data = await calculate_all_scenarios(
        bom            = bom,
        fetched_prices = list(fetched_prices),
        currency       = currency,
    )

    # Step 4: delete old scenarios
    db.query(CostScenario).filter(CostScenario.bom_id == bom_id).delete()

    # Step 5: persist one CostScenario per pricing model
    totals = scenario_data["totals"]
    payg_monthly = totals.get(PricingModel.PAYG.value, {}).get("monthly", 0.0)

    saved_scenarios = []
    for model_val, data in totals.items():
        scenario = CostScenario(
            bom_id              = bom_id,
            scenario_name       = _model_display_name(model_val),
            pricing_model       = model_val,
            total_monthly_cost  = data["monthly"],
            total_annual_cost   = data["annual"],
            savings_vs_payg     = data.get("savings_monthly", 0.0),
            savings_percentage  = data.get("savings_pct", 0.0),
            itemized_costs      = scenario_data["itemized"],
        )
        db.add(scenario)
        saved_scenarios.append(scenario)

    db.commit()
    for s in saved_scenarios:
        db.refresh(s)

    # Step 6: return full payload
    return _build_response(bom, scenario_data, saved_scenarios)


@router.get("/{bom_id}", status_code=status.HTTP_200_OK)
async def get_scenarios(bom_id: int, db: Session = Depends(get_db)):
    """
    Return previously generated scenarios for a BOM.
    Returns 404 if no scenarios exist yet (call /generate first).
    """
    bom = db.query(BillOfMaterials).filter(BillOfMaterials.id == bom_id).first()
    if not bom:
        raise HTTPException(status_code=404, detail=f"BOM {bom_id} not found")

    scenarios = (
        db.query(CostScenario)
        .filter(CostScenario.bom_id == bom_id)
        .all()
    )
    if not scenarios:
        raise HTTPException(
            status_code=404,
            detail=f"No scenarios found for BOM {bom_id}. Call POST /{bom_id}/generate first."
        )

    return _build_get_response(bom, scenarios)


@router.delete("/{bom_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scenarios(bom_id: int, db: Session = Depends(get_db)):
    """Delete all scenarios for a BOM (does not delete the BOM itself)."""
    deleted = db.query(CostScenario).filter(CostScenario.bom_id == bom_id).delete()
    db.commit()
    if deleted == 0:
        raise HTTPException(status_code=404, detail=f"No scenarios found for BOM {bom_id}")
    return None


# ---------------------------------------------------------------------------
# Response builders
# ---------------------------------------------------------------------------

def _model_display_name(model_val: str) -> str:
    names = {
        "payg":    "Pay-As-You-Go",
        "ri_1yr":  "1-Year Reserved",
        "ri_3yr":  "3-Year Reserved",
        "sp_1yr":  "1-Year Savings Plan",
        "sp_3yr":  "3-Year Savings Plan",
        "cud_1yr": "1-Year Committed Use",
        "cud_3yr": "3-Year Committed Use",
        "sud":     "Sustained Use Discount",
        "ahb":     "Azure Hybrid Benefit",
    }
    return names.get(model_val, model_val.upper())


def _build_response(bom, scenario_data: dict, saved_scenarios: list) -> dict:
    """Build the response payload after generate."""
    totals = scenario_data["totals"]
    payg_monthly = totals.get(PricingModel.PAYG.value, {}).get("monthly", 0.0)

    pricing_models_summary = []
    for model_val, data in totals.items():
        pricing_models_summary.append({
            "model":            model_val,
            "display_name":     _model_display_name(model_val),
            "monthly_cost":     data["monthly"],
            "annual_cost":      data["annual"],
            "savings_monthly":  data.get("savings_monthly", 0.0),
            "savings_annual":   data.get("savings_annual", 0.0),
            "savings_pct":      data.get("savings_pct", 0.0),
        })

    # Sort: PAYG first, then by ascending monthly cost
    pricing_models_summary.sort(
        key=lambda x: (x["model"] != "payg", x["monthly_cost"])
    )

    return {
        "bom_id":               bom.id,
        "bom_name":             bom.name,
        "cloud_provider":       bom.cloud_provider,
        "azure_hybrid_benefit": bom.azure_hybrid_benefit,
        "currency":             bom.currency,
        "recommended_model":    scenario_data["recommended_model"],
        "pricing_models":       pricing_models_summary,
        "itemized_services":    scenario_data["itemized"],
        "generated_at":         saved_scenarios[0].created_at.isoformat()
                                if saved_scenarios else None,
    }


def _build_get_response(bom, scenarios: list[CostScenario]) -> dict:
    """Build the response payload for GET (from DB rows)."""
    pricing_models_summary = []
    payg_monthly = 0.0

    for s in scenarios:
        if s.pricing_model == PricingModel.PAYG.value:
            payg_monthly = s.total_monthly_cost

    for s in scenarios:
        pricing_models_summary.append({
            "model":           s.pricing_model,
            "display_name":    s.scenario_name,
            "monthly_cost":    s.total_monthly_cost,
            "annual_cost":     s.total_annual_cost,
            "savings_monthly": s.savings_vs_payg,
            "savings_annual":  round(s.savings_vs_payg * 12, 4),
            "savings_pct":     s.savings_percentage,
        })

    pricing_models_summary.sort(
        key=lambda x: (x["model"] != "payg", x["monthly_cost"])
    )

    # Recommend highest-savings model
    best = max(scenarios, key=lambda s: s.savings_vs_payg)
    recommended = best.pricing_model

    # Itemized from first scenario (all scenarios share the same itemized_costs)
    itemized = scenarios[0].itemized_costs if scenarios else []

    return {
        "bom_id":               bom.id,
        "bom_name":             bom.name,
        "cloud_provider":       bom.cloud_provider,
        "azure_hybrid_benefit": bom.azure_hybrid_benefit,
        "currency":             bom.currency,
        "recommended_model":    recommended,
        "pricing_models":       pricing_models_summary,
        "itemized_services":    itemized,
        "generated_at":         scenarios[0].created_at.isoformat() if scenarios else None,
    }
