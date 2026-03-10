"""
Service configuration schemas using Pydantic
"""
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class CloudProvider(str, Enum):
    """Cloud provider enum"""
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"


class PricingModel(str, Enum):
    """Pricing model enum"""
    PAYG = "payg"
    RI_1YR = "1yr_ri"
    RI_3YR = "3yr_ri"
    SP_1YR = "1yr_sp"
    SP_3YR = "3yr_sp"


class ServiceType(str, Enum):
    """Service type enum"""
    COMPUTE = "compute"
    DATABASE = "database"
    STORAGE = "storage"
    NETWORK = "network"
    SECURITY = "security"
    MONITORING = "monitoring"
    OTHER = "other"


class VMInstanceConfig(BaseModel):
    """Virtual Machine instance configuration"""
    instance_type: str = Field(..., description="Instance type (e.g., m5.large, Standard_D4s_v3)")
    quantity: int = Field(1, ge=1, description="Number of instances")
    region: str = Field(..., description="Cloud region")
    os: str = Field("linux", description="Operating system (linux, windows)")
    cloud_provider: CloudProvider

    # Optional configurations
    disk_size_gb: Optional[int] = Field(None, description="Root disk size in GB")
    additional_disks: Optional[int] = Field(0, description="Number of additional disks")
    network_egress_gb: Optional[float] = Field(0, description="Network egress per month in GB")


class DatabaseConfig(BaseModel):
    """Database service configuration"""
    db_type: str = Field(..., description="Database type (e.g., mysql, postgresql, mssql)")
    instance_type: str = Field(..., description="Instance type")
    storage_gb: int = Field(..., ge=1, description="Storage size in GB")
    region: str
    cloud_provider: CloudProvider

    # Optional
    backup_retention_days: Optional[int] = Field(7, ge=0)
    replicas: Optional[int] = Field(0, ge=0)


class ServiceConfig(BaseModel):
    """Generic service configuration"""
    service_name: str
    service_type: ServiceType
    cloud_provider: CloudProvider
    region: str
    config: Dict[str, Any]  # Flexible config for any service


class BOMCreate(BaseModel):
    """Schema for creating a BOM"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    cloud_provider: str
    services: list = Field(default_factory=list)


class BOMResponse(BaseModel):
    """Schema for BOM response"""
    id: int
    name: str
    description: Optional[str]
    cloud_provider: str
    services: list
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class ScenarioResponse(BaseModel):
    """Schema for scenario response"""
    id: int
    bom_id: int
    scenario_name: str
    pricing_model: str
    total_monthly_cost: float
    total_annual_cost: float
    savings_vs_payg: float
    savings_percentage: float
    itemized_costs: list

    class Config:
        from_attributes = True
