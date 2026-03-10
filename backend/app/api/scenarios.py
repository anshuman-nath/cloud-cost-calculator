"""
Cost Scenarios API endpoints
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.utils.database import get_db
from app.models.bom import BillOfMaterials
from app.models.scenario import CostScenario
from app.models.service import ScenarioResponse
from app.services.scenario_manager import ScenarioManager
from app.utils.logger import logger

router = APIRouter()
scenario_manager = ScenarioManager()


@router.post("/{bom_id}/generate", response_model=List[ScenarioResponse])
def generate_scenarios(bom_id: int, db: Session = Depends(get_db)):
    """
    Generate cost scenarios for a BOM

    This is the KEY ENDPOINT that solves your problem:
    - Creates 3 scenarios (PAYG, 1-Yr RI, 3-Yr RI) from one BOM
    - Automatically applies discount models to all VMs
    - No need to update each VM individually!
    """
    logger.info(f"Generating scenarios for BOM {bom_id}")

    # Get BOM
    bom = db.query(BillOfMaterials).filter(BillOfMaterials.id == bom_id).first()
    if not bom:
        raise HTTPException(status_code=404, detail="BOM not found")

    # Delete existing scenarios for this BOM
    db.query(CostScenario).filter(CostScenario.bom_id == bom_id).delete()

    # Generate new scenarios
    scenarios_data = scenario_manager.create_scenarios_from_bom(
        bom_id=bom_id,
        bom_services=bom.services
    )

    # Save to database
    db_scenarios = []
    for scenario_data in scenarios_data:
        db_scenario = CostScenario(**scenario_data)
        db.add(db_scenario)
        db_scenarios.append(db_scenario)

    db.commit()

    for scenario in db_scenarios:
        db.refresh(scenario)

    logger.info(f"Generated {len(db_scenarios)} scenarios for BOM {bom_id}")

    return [
        ScenarioResponse(
            id=s.id,
            bom_id=s.bom_id,
            scenario_name=s.scenario_name,
            pricing_model=s.pricing_model,
            total_monthly_cost=s.total_monthly_cost,
            total_annual_cost=s.total_annual_cost,
            savings_vs_payg=s.savings_vs_payg,
            savings_percentage=s.savings_percentage,
            itemized_costs=s.itemized_costs
        )
        for s in db_scenarios
    ]


@router.get("/{bom_id}", response_model=List[ScenarioResponse])
def get_scenarios_for_bom(bom_id: int, db: Session = Depends(get_db)):
    """
    Get all scenarios for a specific BOM
    """
    scenarios = db.query(CostScenario).filter(CostScenario.bom_id == bom_id).all()

    return [
        ScenarioResponse(
            id=s.id,
            bom_id=s.bom_id,
            scenario_name=s.scenario_name,
            pricing_model=s.pricing_model,
            total_monthly_cost=s.total_monthly_cost,
            total_annual_cost=s.total_annual_cost,
            savings_vs_payg=s.savings_vs_payg,
            savings_percentage=s.savings_percentage,
            itemized_costs=s.itemized_costs
        )
        for s in scenarios
    ]


@router.get("/{bom_id}/compare")
def compare_scenarios(bom_id: int, db: Session = Depends(get_db)):
    """
    Compare all scenarios for a BOM
    Returns comparison data with savings highlights
    """
    scenarios = db.query(CostScenario).filter(CostScenario.bom_id == bom_id).all()

    if not scenarios:
        raise HTTPException(status_code=404, detail="No scenarios found for this BOM")

    scenarios_data = [
        {
            "scenario_name": s.scenario_name,
            "pricing_model": s.pricing_model,
            "total_monthly_cost": s.total_monthly_cost,
            "total_annual_cost": s.total_annual_cost,
            "savings_vs_payg": s.savings_vs_payg,
            "savings_percentage": s.savings_percentage
        }
        for s in scenarios
    ]

    comparison = scenario_manager.compare_scenarios(scenarios_data)

    return comparison
