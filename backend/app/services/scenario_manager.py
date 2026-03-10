"""
Scenario Manager - Create and compare cost scenarios
"""
from typing import List, Dict, Any
from app.models.service import PricingModel
from app.models.scenario import CostScenario
from app.services.pricing_engine import PricingEngine
from app.utils.logger import logger


class ScenarioManager:
    """
    Manage cost scenarios for BOMs
    Key feature: Bulk apply pricing models to all services
    """

    def __init__(self):
        self.pricing_engine = PricingEngine()

    def create_scenarios_from_bom(
        self,
        bom_id: int,
        bom_services: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Create 3 standard scenarios from a BOM:
        1. PAYG (baseline)
        2. 1-Year Reserved Instances
        3. 3-Year Reserved Instances

        This is the KEY FEATURE that solves your pain point:
        - No need to update each VM individually
        - Bulk applies pricing model to all eligible services

        Args:
            bom_id: BOM ID
            bom_services: List of service configurations

        Returns:
            List of scenario dictionaries
        """
        logger.info(f"Creating scenarios for BOM {bom_id}")

        scenarios = []

        # Scenario 1: PAYG (baseline)
        payg_scenario = self._calculate_scenario(
            bom_id,
            "Pay-As-You-Go",
            PricingModel.PAYG,
            bom_services
        )
        scenarios.append(payg_scenario)

        # Scenario 2: 1-Year RI
        ri_1yr_scenario = self._calculate_scenario(
            bom_id,
            "1-Year Reserved",
            PricingModel.RI_1YR,
            bom_services
        )
        # Calculate savings vs PAYG
        ri_1yr_scenario['savings_vs_payg'] = (
            payg_scenario['total_monthly_cost'] - ri_1yr_scenario['total_monthly_cost']
        )
        ri_1yr_scenario['savings_percentage'] = (
            (ri_1yr_scenario['savings_vs_payg'] / payg_scenario['total_monthly_cost']) * 100
            if payg_scenario['total_monthly_cost'] > 0 else 0
        )
        scenarios.append(ri_1yr_scenario)

        # Scenario 3: 3-Year RI
        ri_3yr_scenario = self._calculate_scenario(
            bom_id,
            "3-Year Reserved",
            PricingModel.RI_3YR,
            bom_services
        )
        # Calculate savings vs PAYG
        ri_3yr_scenario['savings_vs_payg'] = (
            payg_scenario['total_monthly_cost'] - ri_3yr_scenario['total_monthly_cost']
        )
        ri_3yr_scenario['savings_percentage'] = (
            (ri_3yr_scenario['savings_vs_payg'] / payg_scenario['total_monthly_cost']) * 100
            if payg_scenario['total_monthly_cost'] > 0 else 0
        )
        scenarios.append(ri_3yr_scenario)

        logger.info(f"Created {len(scenarios)} scenarios for BOM {bom_id}")

        return scenarios

    def _calculate_scenario(
        self,
        bom_id: int,
        scenario_name: str,
        pricing_model: PricingModel,
        services: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate costs for entire BOM with given pricing model

        This applies the pricing model to ALL services at once
        No need to update each service individually!
        """
        total_monthly_cost = 0.0
        itemized_costs = []

        for service in services:
            service_type = service.get("service_type", "")

            # Check if this service supports discount
            supports_discount = self.pricing_engine.supports_discount(service_type)

            # Apply pricing model if service supports it, otherwise use PAYG
            effective_pricing_model = (
                pricing_model if supports_discount else PricingModel.PAYG
            )

            # Calculate cost
            cost = self.pricing_engine.calculate_service_cost(
                service,
                effective_pricing_model
            )

            total_monthly_cost += cost

            # Add to itemized list
            itemized_costs.append({
                "service_name": service.get("service_name", "Unnamed"),
                "service_type": service_type,
                "cloud_provider": service.get("cloud_provider", ""),
                "region": service.get("region", ""),
                "pricing_model": effective_pricing_model.value,
                "monthly_cost": round(cost, 2),
                "config": service.get("config", {})
            })

        scenario_data = {
            "bom_id": bom_id,
            "scenario_name": scenario_name,
            "pricing_model": pricing_model.value,
            "total_monthly_cost": round(total_monthly_cost, 2),
            "total_annual_cost": round(total_monthly_cost * 12, 2),
            "savings_vs_payg": 0.0,  # Will be calculated by caller
            "savings_percentage": 0.0,  # Will be calculated by caller
            "itemized_costs": itemized_costs
        }

        logger.info(
            f"Scenario '{scenario_name}': ${scenario_data['total_monthly_cost']:.2f}/mo"
        )

        return scenario_data

    def compare_scenarios(
        self,
        scenarios: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Create a comparison report of multiple scenarios

        Returns:
            Comparison data with highlights
        """
        if not scenarios:
            return {}

        # Find baseline (PAYG)
        payg_scenario = next(
            (s for s in scenarios if s['pricing_model'] == PricingModel.PAYG.value),
            scenarios[0]
        )

        comparison = {
            "baseline": payg_scenario,
            "alternatives": [s for s in scenarios if s != payg_scenario],
            "summary": {
                "best_savings_scenario": None,
                "max_savings_amount": 0.0,
                "max_savings_percentage": 0.0
            }
        }

        # Find best savings
        for scenario in comparison["alternatives"]:
            savings = scenario.get("savings_vs_payg", 0)
            if savings > comparison["summary"]["max_savings_amount"]:
                comparison["summary"]["max_savings_amount"] = savings
                comparison["summary"]["max_savings_percentage"] = scenario.get("savings_percentage", 0)
                comparison["summary"]["best_savings_scenario"] = scenario["scenario_name"]

        return comparison
