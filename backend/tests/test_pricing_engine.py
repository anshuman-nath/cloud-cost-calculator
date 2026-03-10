"""
Unit tests for Pricing Engine
"""
import pytest
from app.services.pricing_engine import PricingEngine
from app.models.service import PricingModel


class TestPricingEngine:
    """Test pricing engine calculations"""

    def setup_method(self):
        """Setup test fixtures"""
        self.engine = PricingEngine()

    def test_payg_calculation(self):
        """Test PAYG cost calculation"""
        service_config = {
            "service_type": "compute",
            "config": {
                "instance_type": "m5.large",
                "quantity": 1
            }
        }

        cost = self.engine.calculate_service_cost(
            service_config,
            PricingModel.PAYG
        )

        # m5.large = $0.096/hr * 730 hrs = $70.08
        assert cost > 0
        assert cost == pytest.approx(70.08, rel=0.01)

    def test_1yr_ri_discount(self):
        """Test 1-year RI discount application"""
        service_config = {
            "service_type": "compute",
            "config": {
                "instance_type": "m5.large",
                "quantity": 1
            }
        }

        payg_cost = self.engine.calculate_service_cost(
            service_config,
            PricingModel.PAYG
        )

        ri_1yr_cost = self.engine.calculate_service_cost(
            service_config,
            PricingModel.RI_1YR
        )

        # 1-year RI should be 40% cheaper
        expected_discount = payg_cost * 0.40
        assert ri_1yr_cost == pytest.approx(payg_cost - expected_discount, rel=0.01)

    def test_3yr_ri_discount(self):
        """Test 3-year RI discount application"""
        service_config = {
            "service_type": "compute",
            "config": {
                "instance_type": "m5.large",
                "quantity": 1
            }
        }

        payg_cost = self.engine.calculate_service_cost(
            service_config,
            PricingModel.PAYG
        )

        ri_3yr_cost = self.engine.calculate_service_cost(
            service_config,
            PricingModel.RI_3YR
        )

        # 3-year RI should be 62% cheaper
        expected_discount = payg_cost * 0.62
        assert ri_3yr_cost == pytest.approx(payg_cost - expected_discount, rel=0.01)

    def test_multiple_instances(self):
        """Test cost calculation with multiple instances"""
        service_config = {
            "service_type": "compute",
            "config": {
                "instance_type": "m5.large",
                "quantity": 5
            }
        }

        cost = self.engine.calculate_service_cost(
            service_config,
            PricingModel.PAYG
        )

        # Should be 5x the single instance cost
        single_cost = 70.08
        assert cost == pytest.approx(single_cost * 5, rel=0.01)

    def test_storage_no_discount(self):
        """Test that storage doesn't get RI discount"""
        service_config = {
            "service_type": "storage",
            "config": {
                "size_gb": 1000,
                "storage_type": "standard"
            }
        }

        payg_cost = self.engine.calculate_service_cost(
            service_config,
            PricingModel.PAYG
        )

        ri_cost = self.engine.calculate_service_cost(
            service_config,
            PricingModel.RI_1YR
        )

        # Storage costs should be the same regardless of pricing model
        assert payg_cost == ri_cost
