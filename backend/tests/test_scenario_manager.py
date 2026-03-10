"""
Unit tests for Scenario Manager
"""
import pytest
from app.services.scenario_manager import ScenarioManager
from app.models.service import PricingModel


class TestScenarioManager:
    """Test scenario management"""

    def setup_method(self):
        """Setup test fixtures"""
        self.manager = ScenarioManager()

    def test_create_scenarios_from_bom(self):
        """Test creating 3 scenarios from BOM"""
        bom_services = [
            {
                "service_name": "Web Server",
                "service_type": "compute",
                "cloud_provider": "aws",
                "region": "us-east-1",
                "config": {
                    "instance_type": "m5.large",
                    "quantity": 2
                }
            },
            {
                "service_name": "Database",
                "service_type": "database",
                "cloud_provider": "aws",
                "region": "us-east-1",
                "config": {
                    "instance_type": "db.m5.large",
                    "storage_gb": 100
                }
            }
        ]

        scenarios = self.manager.create_scenarios_from_bom(
            bom_id=1,
            bom_services=bom_services
        )

        # Should create 3 scenarios
        assert len(scenarios) == 3

        # Check scenario names
        assert scenarios[0]['scenario_name'] == "Pay-As-You-Go"
        assert scenarios[1]['scenario_name'] == "1-Year Reserved"
        assert scenarios[2]['scenario_name'] == "3-Year Reserved"

    def test_savings_calculation(self):
        """Test savings calculation vs PAYG"""
        bom_services = [
            {
                "service_name": "Test VM",
                "service_type": "compute",
                "cloud_provider": "aws",
                "region": "us-east-1",
                "config": {
                    "instance_type": "m5.large",
                    "quantity": 1
                }
            }
        ]

        scenarios = self.manager.create_scenarios_from_bom(
            bom_id=1,
            bom_services=bom_services
        )

        payg_scenario = scenarios[0]
        ri_1yr_scenario = scenarios[1]
        ri_3yr_scenario = scenarios[2]

        # 1-year RI should save money
        assert ri_1yr_scenario['savings_vs_payg'] > 0
        assert ri_1yr_scenario['savings_percentage'] > 0

        # 3-year RI should save more than 1-year RI
        assert ri_3yr_scenario['savings_vs_payg'] > ri_1yr_scenario['savings_vs_payg']
        assert ri_3yr_scenario['savings_percentage'] > ri_1yr_scenario['savings_percentage']

    def test_itemized_costs(self):
        """Test itemized cost breakdown"""
        bom_services = [
            {
                "service_name": "VM 1",
                "service_type": "compute",
                "cloud_provider": "aws",
                "region": "us-east-1",
                "config": {"instance_type": "m5.large", "quantity": 1}
            },
            {
                "service_name": "VM 2",
                "service_type": "compute",
                "cloud_provider": "aws",
                "region": "us-east-1",
                "config": {"instance_type": "t3.medium", "quantity": 1}
            }
        ]

        scenarios = self.manager.create_scenarios_from_bom(
            bom_id=1,
            bom_services=bom_services
        )

        # Check itemized costs in first scenario
        itemized = scenarios[0]['itemized_costs']
        assert len(itemized) == 2
        assert itemized[0]['service_name'] == "VM 1"
        assert itemized[1]['service_name'] == "VM 2"

    def test_compare_scenarios(self):
        """Test scenario comparison"""
        scenarios = [
            {
                "scenario_name": "PAYG",
                "pricing_model": "payg",
                "total_monthly_cost": 100.0,
                "savings_vs_payg": 0.0,
                "savings_percentage": 0.0
            },
            {
                "scenario_name": "1-Year RI",
                "pricing_model": "1yr_ri",
                "total_monthly_cost": 60.0,
                "savings_vs_payg": 40.0,
                "savings_percentage": 40.0
            },
            {
                "scenario_name": "3-Year RI",
                "pricing_model": "3yr_ri",
                "total_monthly_cost": 38.0,
                "savings_vs_payg": 62.0,
                "savings_percentage": 62.0
            }
        ]

        comparison = self.manager.compare_scenarios(scenarios)

        # Check summary
        assert comparison['summary']['best_savings_scenario'] == "3-Year RI"
        assert comparison['summary']['max_savings_amount'] == 62.0
        assert comparison['summary']['max_savings_percentage'] == 62.0
