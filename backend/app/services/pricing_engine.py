"""
Pricing Engine Service
Applies per-provider, per-service-type discount logic on top of PAYG base prices.

Key design decisions:
  - Spot / Dev/Test: excluded entirely
  - GCP SUD: always applied at 30% (assumes 730hr/month full utilization)
  - Azure Hybrid Benefit: applied only when bom.azure_hybrid_benefit == True
  - Currency: USD throughout; _convert_currency() is the single forex stub
  - Savings: always calculated vs PAYG baseline
"""
from enum import Enum
from typing import Optional
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Pricing Model Enum
# ---------------------------------------------------------------------------

class PricingModel(str, Enum):
    PAYG      = "payg"         # Pay-As-You-Go / On-Demand (all providers)
    RI_1YR    = "ri_1yr"       # Reserved Instance 1-year (AWS, Azure)
    RI_3YR    = "ri_3yr"       # Reserved Instance 3-year (AWS, Azure)
    SP_1YR    = "sp_1yr"       # Savings Plan 1-year (AWS only)
    SP_3YR    = "sp_3yr"       # Savings Plan 3-year (AWS only)
    CUD_1YR   = "cud_1yr"      # Committed Use Discount 1-year (GCP only)
    CUD_3YR   = "cud_3yr"      # Committed Use Discount 3-year (GCP only)
    SUD       = "sud"          # Sustained Use Discount (GCP only, automatic)
    AHB       = "ahb"          # Azure Hybrid Benefit (Azure only)


# ---------------------------------------------------------------------------
# Discount Matrix
# Each entry: (pricing_model, discount_rate, display_name, notes)
# discount_rate = fraction of PAYG price to pay (e.g. 0.60 = 40% off)
# ---------------------------------------------------------------------------

@dataclass
class DiscountOption:
    model:        PricingModel
    payg_fraction: float   # e.g. 0.60 means "pay 60% of PAYG" → 40% savings
    display_name:  str
    notes:         str = ""


# ---------------------------------------------------------------------------
# AWS discount matrix per service type
# ---------------------------------------------------------------------------

AWS_DISCOUNT_MATRIX: dict[str, list[DiscountOption]] = {

    "compute": [  # EC2
        DiscountOption(PricingModel.PAYG,   1.000, "On-Demand"),
        DiscountOption(PricingModel.RI_1YR, 0.600, "1-Year Reserved",  "No Upfront, Standard RI"),
        DiscountOption(PricingModel.RI_3YR, 0.380, "3-Year Reserved",  "No Upfront, Standard RI"),
        DiscountOption(PricingModel.SP_1YR, 0.620, "1-Year Savings Plan", "Compute Savings Plan"),
        DiscountOption(PricingModel.SP_3YR, 0.450, "3-Year Savings Plan", "Compute Savings Plan"),
    ],

    "database": [  # RDS
        DiscountOption(PricingModel.PAYG,   1.000, "On-Demand"),
        DiscountOption(PricingModel.RI_1YR, 0.650, "1-Year Reserved",  "Single-AZ, No Upfront"),
        DiscountOption(PricingModel.RI_3YR, 0.450, "3-Year Reserved",  "Single-AZ, No Upfront"),
    ],

    "cache": [  # ElastiCache
        DiscountOption(PricingModel.PAYG,   1.000, "On-Demand"),
        DiscountOption(PricingModel.RI_1YR, 0.670, "1-Year Reserved",  "No Upfront"),
        DiscountOption(PricingModel.RI_3YR, 0.480, "3-Year Reserved",  "No Upfront"),
    ],

    "serverless": [  # Lambda
        DiscountOption(PricingModel.PAYG,   1.000, "On-Demand"),
        DiscountOption(PricingModel.SP_1YR, 0.830, "1-Year Savings Plan", "Compute Savings Plan"),
    ],

    "storage": [  # S3
        DiscountOption(PricingModel.PAYG, 1.000, "On-Demand"),
        # No discount mechanisms for S3
    ],

    "container": [  # ECS Fargate / EKS
        DiscountOption(PricingModel.PAYG,   1.000, "On-Demand"),
        DiscountOption(PricingModel.SP_1YR, 0.800, "1-Year Savings Plan", "Compute Savings Plan"),
        DiscountOption(PricingModel.SP_3YR, 0.630, "3-Year Savings Plan", "Compute Savings Plan"),
    ],

    "cdn": [  # CloudFront
        DiscountOption(PricingModel.PAYG, 1.000, "On-Demand"),
        # No standard discount mechanisms
    ],

    "nosql": [  # DynamoDB
        DiscountOption(PricingModel.PAYG, 1.000, "On-Demand"),
        # DynamoDB reserved capacity is complex/deprecated; excluded
    ],
}


# ---------------------------------------------------------------------------
# Azure discount matrix per service type
# ---------------------------------------------------------------------------

# Windows VMs and SQL get AHB; Linux VMs do not
AZURE_DISCOUNT_MATRIX: dict[str, list[DiscountOption]] = {

    "compute_linux": [
        DiscountOption(PricingModel.PAYG,   1.000, "Pay-As-You-Go"),
        DiscountOption(PricingModel.RI_1YR, 0.640, "1-Year Reserved",  "No Upfront"),
        DiscountOption(PricingModel.RI_3YR, 0.480, "3-Year Reserved",  "No Upfront"),
        # AHB not applicable to Linux
    ],

    "compute_windows": [
        DiscountOption(PricingModel.PAYG,   1.000, "Pay-As-You-Go"),
        DiscountOption(PricingModel.RI_1YR, 0.640, "1-Year Reserved",   "No Upfront"),
        DiscountOption(PricingModel.RI_3YR, 0.480, "3-Year Reserved",   "No Upfront"),
        DiscountOption(PricingModel.AHB,    0.600, "Azure Hybrid Benefit",
                       "Requires existing Windows Server license with SA"),
    ],

    "compute": [  # Generic compute (OS determined at runtime — see engine logic)
        DiscountOption(PricingModel.PAYG,   1.000, "Pay-As-You-Go"),
        DiscountOption(PricingModel.RI_1YR, 0.640, "1-Year Reserved"),
        DiscountOption(PricingModel.RI_3YR, 0.480, "3-Year Reserved"),
        # AHB added dynamically based on OS
    ],

    "database": [  # Azure SQL
        DiscountOption(PricingModel.PAYG,   1.000, "Pay-As-You-Go"),
        DiscountOption(PricingModel.RI_1YR, 0.670, "1-Year Reserved"),
        DiscountOption(PricingModel.RI_3YR, 0.500, "3-Year Reserved"),
        DiscountOption(PricingModel.AHB,    0.650, "Azure Hybrid Benefit",
                       "Requires existing SQL Server license with SA"),
    ],

    "nosql": [  # Cosmos DB
        DiscountOption(PricingModel.PAYG,   1.000, "Pay-As-You-Go"),
        DiscountOption(PricingModel.RI_1YR, 0.830, "1-Year Reserved",  "RU/s reservation"),
        # No 3-yr RI for Cosmos DB
    ],

    "container": [  # AKS (nodes are VMs — same as compute)
        DiscountOption(PricingModel.PAYG,   1.000, "Pay-As-You-Go"),
        DiscountOption(PricingModel.RI_1YR, 0.640, "1-Year Reserved"),
        DiscountOption(PricingModel.RI_3YR, 0.480, "3-Year Reserved"),
        # AHB added dynamically for Windows node pools
    ],

    "storage": [  # Blob Storage
        DiscountOption(PricingModel.PAYG, 1.000, "Pay-As-You-Go"),
    ],

    "serverless": [  # Azure Functions
        DiscountOption(PricingModel.PAYG, 1.000, "Pay-As-You-Go"),
    ],

    "cache": [  # Azure Cache for Redis
        DiscountOption(PricingModel.PAYG,   1.000, "Pay-As-You-Go"),
        DiscountOption(PricingModel.RI_1YR, 0.670, "1-Year Reserved"),
        DiscountOption(PricingModel.RI_3YR, 0.500, "3-Year Reserved"),
    ],
}


# ---------------------------------------------------------------------------
# GCP discount matrix per service type
# SUD is modeled as a separate pricing option (not stacked on CUD)
# SUD and CUD are mutually exclusive — customer picks one
# ---------------------------------------------------------------------------

GCP_DISCOUNT_MATRIX: dict[str, list[DiscountOption]] = {

    "compute": [
        DiscountOption(PricingModel.PAYG,    1.000, "On-Demand"),
        DiscountOption(PricingModel.SUD,     0.700, "Sustained Use Discount",
                       "Automatic 30% discount for 730hr/month usage"),
        DiscountOption(PricingModel.CUD_1YR, 0.630, "1-Year Committed Use",
                       "Resource-based CUD"),
        DiscountOption(PricingModel.CUD_3YR, 0.450, "3-Year Committed Use",
                       "Resource-based CUD"),
    ],

    "database": [  # Cloud SQL
        DiscountOption(PricingModel.PAYG,    1.000, "On-Demand"),
        DiscountOption(PricingModel.CUD_1YR, 0.750, "1-Year Committed Use"),
        DiscountOption(PricingModel.CUD_3YR, 0.480, "3-Year Committed Use"),
        # SUD does NOT apply to Cloud SQL
    ],

    "container": [  # GKE nodes (Compute Engine VMs)
        DiscountOption(PricingModel.PAYG,    1.000, "On-Demand"),
        DiscountOption(PricingModel.SUD,     0.700, "Sustained Use Discount",
                       "Automatic 30% discount for 730hr/month usage"),
        DiscountOption(PricingModel.CUD_1YR, 0.630, "1-Year Committed Use"),
        DiscountOption(PricingModel.CUD_3YR, 0.450, "3-Year Committed Use"),
    ],

    "storage": [  # Cloud Storage
        DiscountOption(PricingModel.PAYG, 1.000, "On-Demand"),
    ],

    "serverless": [  # Cloud Functions / Cloud Run
        DiscountOption(PricingModel.PAYG, 1.000, "On-Demand"),
    ],

    "nosql": [  # Firestore
        DiscountOption(PricingModel.PAYG, 1.000, "On-Demand"),
    ],

    "cache": [  # Memorystore for Redis
        DiscountOption(PricingModel.PAYG,    1.000, "On-Demand"),
        DiscountOption(PricingModel.CUD_1YR, 0.750, "1-Year Committed Use"),
        # No 3-yr CUD for Memorystore
    ],

    "analytics": [  # BigQuery
        DiscountOption(PricingModel.PAYG, 1.000, "On-Demand"),
        # Flat-rate slots are a different model entirely; excluded for now
    ],
}


# Master lookup
PROVIDER_DISCOUNT_MATRIX = {
    "aws":   AWS_DISCOUNT_MATRIX,
    "azure": AZURE_DISCOUNT_MATRIX,
    "gcp":   GCP_DISCOUNT_MATRIX,
}


# ---------------------------------------------------------------------------
# Service type resolver
# Normalises a service config's service_type for Azure (linux vs windows split)
# ---------------------------------------------------------------------------

def resolve_azure_service_type(service_type: str, config: dict) -> str:
    """
    For Azure compute/container, disambiguate based on OS.
    All other service types pass through unchanged.
    """
    if service_type in ("compute", "container"):
        os_type = config.get("os", "linux").lower()
        if service_type == "compute":
            return "compute_windows" if os_type == "windows" else "compute_linux"
    return service_type


# ---------------------------------------------------------------------------
# Core: get applicable discount options for a service
# ---------------------------------------------------------------------------

def get_applicable_discounts(
    provider: str,
    service_type: str,
    config: dict,
    azure_hybrid_benefit: bool = False,
) -> list[DiscountOption]:
    """
    Return the list of DiscountOption applicable for this service.

    Rules:
    - Azure: resolve compute_linux vs compute_windows
    - Azure: AHB only included when azure_hybrid_benefit=True AND service supports it
    - GCP: SUD and CUD both shown (mutually exclusive — customer picks)
    - All: PAYG always included
    """
    matrix = PROVIDER_DISCOUNT_MATRIX.get(provider, {})

    # Azure service type resolution
    if provider == "azure":
        resolved_type = resolve_azure_service_type(service_type, config)
    else:
        resolved_type = service_type

    options = matrix.get(resolved_type, [DiscountOption(PricingModel.PAYG, 1.0, "On-Demand")])

    # Filter AHB: only include if BOM has AHB enabled
    if not azure_hybrid_benefit:
        options = [o for o in options if o.model != PricingModel.AHB]

    return options


# ---------------------------------------------------------------------------
# Core: calculate all scenarios for a single service item
# ---------------------------------------------------------------------------

def calculate_service_scenarios(
    service_name:         str,
    service_type:         str,
    payg_monthly_cost:    float,
    provider:             str,
    config:               dict,
    azure_hybrid_benefit: bool = False,
    currency:             str = "USD",
) -> dict:
    """
    Given a PAYG base cost for one service, compute all applicable
    pricing model costs and savings.

    Returns:
    {
        "service_name": str,
        "service_type": str,
        "payg_monthly_cost": float,
        "scenarios": [
            {
                "model":             str,   # PricingModel value
                "display_name":      str,
                "monthly_cost":      float,
                "annual_cost":       float,
                "savings_vs_payg":   float,
                "savings_pct":       float,
                "notes":             str,
                "applicable":        bool,
            },
            ...
        ]
    }
    """
    options = get_applicable_discounts(
        provider, service_type, config, azure_hybrid_benefit
    )
    payg_annual = payg_monthly_cost * 12

    scenarios = []
    for opt in options:
        monthly = round(payg_monthly_cost * opt.payg_fraction, 4)
        annual  = round(monthly * 12, 4)
        savings = round(payg_monthly_cost - monthly, 4)
        savings_pct = round((1 - opt.payg_fraction) * 100, 2) if opt.model != PricingModel.PAYG else 0.0

        scenarios.append({
            "model":           opt.model.value,
            "display_name":    opt.display_name,
            "monthly_cost":    monthly,
            "annual_cost":     annual,
            "savings_vs_payg": savings,
            "savings_pct":     savings_pct,
            "notes":           opt.notes,
            "applicable":      True,
        })

    return {
        "service_name":      service_name,
        "service_type":      service_type,
        "payg_monthly_cost": round(payg_monthly_cost, 4),
        "payg_annual_cost":  round(payg_annual, 4),
        "scenarios":         scenarios,
        "currency":          currency,
    }


# ---------------------------------------------------------------------------
# Core: aggregate BOM-level scenario totals
# ---------------------------------------------------------------------------

def aggregate_bom_scenarios(itemized_results: list[dict]) -> dict:
    """
    Aggregate per-service scenario costs into BOM-level totals.

    Strategy:
    - For each pricing model, sum costs across all services.
    - If a service does not support a given model, use its PAYG cost instead
      (cannot commit what you cannot discount).
    - This gives the total minimum achievable cost under each model.

    Returns:
    {
        "payg": {"monthly": float, "annual": float},
        "ri_1yr": {"monthly": float, "annual": float, "savings_monthly": float, "savings_pct": float},
        ...
    }
    """
    # Collect all model values that appear across any service
    all_models: set[str] = set()
    for item in itemized_results:
        for s in item["scenarios"]:
            all_models.add(s["model"])

    aggregated: dict[str, dict] = {}

    for model_val in all_models:
        total_monthly = 0.0
        for item in itemized_results:
            # Find this model in the service's scenarios
            match = next((s for s in item["scenarios"] if s["model"] == model_val), None)
            if match:
                total_monthly += match["monthly_cost"]
            else:
                # Service doesn't support this model → use PAYG
                payg = next((s for s in item["scenarios"] if s["model"] == PricingModel.PAYG.value), None)
                total_monthly += payg["monthly_cost"] if payg else 0.0

        total_annual = round(total_monthly * 12, 4)
        total_monthly = round(total_monthly, 4)

        aggregated[model_val] = {
            "monthly":    total_monthly,
            "annual":     total_annual,
        }

    # Compute savings vs PAYG for each model
    payg_monthly = aggregated.get(PricingModel.PAYG.value, {}).get("monthly", 0.0)
    for model_val, data in aggregated.items():
        if model_val != PricingModel.PAYG.value:
            savings_m = round(payg_monthly - data["monthly"], 4)
            savings_pct = round((savings_m / payg_monthly * 100), 2) if payg_monthly > 0 else 0.0
            data["savings_monthly"] = savings_m
            data["savings_annual"]  = round(savings_m * 12, 4)
            data["savings_pct"]     = savings_pct
        else:
            data["savings_monthly"] = 0.0
            data["savings_annual"]  = 0.0
            data["savings_pct"]     = 0.0

    return aggregated


# ---------------------------------------------------------------------------
# Main entry: calculate_all_scenarios
# Called by the scenarios API endpoint
# ---------------------------------------------------------------------------

async def calculate_all_scenarios(
    bom: object,                    # BillOfMaterials ORM instance
    fetched_prices: list[dict],     # [{service_name, service_type, config, payg_monthly_cost}]
    currency: str = "USD",
) -> dict:
    """
    Full pipeline:
    1. For each service in the BOM (with its fetched PAYG price),
       compute all applicable pricing model costs.
    2. Aggregate to BOM-level totals.

    Returns the complete payload saved to CostScenario rows.

    Args:
        bom:            BillOfMaterials ORM instance (needs .cloud_provider,
                        .azure_hybrid_benefit, .currency)
        fetched_prices: list of dicts — one per service — containing
                        the PAYG monthly cost from pricing_fetcher.py
        currency:       display currency (USD for now)

    Returns:
    {
        "provider":            str,
        "azure_hybrid_benefit": bool,
        "currency":            str,
        "itemized":            list[dict],  # per-service breakdown
        "totals":              dict,        # aggregated per pricing model
        "recommended_model":   str,         # highest-savings applicable model
    }
    """
    provider = bom.cloud_provider.lower()
    ahb = getattr(bom, "azure_hybrid_benefit", False)

    itemized = []
    for item in fetched_prices:
        result = calculate_service_scenarios(
            service_name         = item["service_name"],
            service_type         = item["service_type"],
            payg_monthly_cost    = item["payg_monthly_cost"],
            provider             = provider,
            config               = item.get("config", {}),
            azure_hybrid_benefit = ahb,
            currency             = currency,
        )
        itemized.append(result)

    totals = aggregate_bom_scenarios(itemized)

    # Recommend the model with highest savings
    payg_m = totals.get(PricingModel.PAYG.value, {}).get("monthly", 0)
    best_model = PricingModel.PAYG.value
    best_savings = 0.0
    for model_val, data in totals.items():
        if data.get("savings_monthly", 0) > best_savings:
            best_savings = data["savings_monthly"]
            best_model = model_val

    return {
        "provider":             provider,
        "azure_hybrid_benefit": ahb,
        "currency":             currency,
        "itemized":             itemized,
        "totals":               totals,
        "recommended_model":    best_model,
    }
