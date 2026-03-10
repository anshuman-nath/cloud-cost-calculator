"""
Configuration management using Pydantic Settings
"""
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings"""

    # Application
    APP_NAME: str = "Cloud Cost Calculator"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"

    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "sqlite:///./cloud_cost_calculator.db"

    # Infracost API
    INFRACOST_API_KEY: str = ""
    INFRACOST_API_URL: str = "https://pricing.api.infracost.io/graphql"

    # AWS Pricing API
    AWS_PRICING_API_URL: str = "https://pricing.us-east-1.amazonaws.com"

    # Azure Pricing API
    AZURE_PRICING_API_URL: str = "https://prices.azure.com/api/retail/prices"

    # GCP Pricing API
    GCP_PRICING_API_URL: str = "https://cloudbilling.googleapis.com/v1/services"

    # Pricing refresh
    PRICING_REFRESH_DAYS: int = 7

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )


# Global settings instance
settings = Settings()
