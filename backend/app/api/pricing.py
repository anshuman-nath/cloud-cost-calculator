"""
Pricing API endpoints
"""
from fastapi import APIRouter
from app.services.pricing_fetcher import PricingFetcher
from app.utils.logger import logger

router = APIRouter()
pricing_fetcher = PricingFetcher()


@router.get("/refresh")
async def refresh_pricing():
    """
    Manually trigger pricing data refresh
    """
    logger.info("Manual pricing refresh triggered")

    # TODO: Implement full pricing data refresh
    # This would fetch latest pricing from all cloud providers
    # and update the local cache

    return {
        "status": "success",
        "message": "Pricing data refresh initiated",
        "note": "Full implementation pending"
    }


@router.get("/test/infracost")
async def test_infracost():
    """
    Test Infracost API connection
    """
    result = await pricing_fetcher.fetch_infracost_pricing(
        service="AmazonEC2",
        region="us-east-1"
    )

    return {
        "status": "success" if result else "failed",
        "data": result
    }


@router.get("/test/azure")
async def test_azure():
    """
    Test Azure Pricing API connection
    """
    result = await pricing_fetcher.fetch_azure_pricing(
        service_name="Virtual Machines",
        region="eastus"
    )

    return {
        "status": "success" if result else "failed",
        "data": result
    }
