"""
Bill of Materials API endpoints
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session

from app.utils.database import get_db
from app.models.bom import BillOfMaterials

router = APIRouter(prefix="/api/v1/bom", tags=["Bill of Materials"])


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

SUPPORTED_PROVIDERS = {"aws", "azure", "gcp"}
SUPPORTED_CURRENCIES = {"USD"}   # GBP, EUR added when forex layer is ready


class ServiceConfig(BaseModel):
    """A single cloud service entry within a BOM."""
    service_name: str = Field(..., min_length=1, max_length=200)
    service_type: str = Field(..., description=(
        "aws:   compute | database | cache | serverless | storage | container | cdn | nosql\n"
        "azure: compute | database | nosql | container | storage | serverless | cache\n"
        "gcp:   compute | database | container | storage | serverless | nosql | cache | analytics"
    ))
    config: dict = Field(default_factory=dict, description="Provider-specific configuration")


class BOMCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    cloud_provider: str = Field(..., description="aws | azure | gcp")

    # Azure Hybrid Benefit toggle
    # Only meaningful for Azure BOMs; silently ignored for AWS/GCP
    azure_hybrid_benefit: bool = Field(
        default=False,
        description=(
            "Azure only. Set to true if you own existing Windows Server or "
            "SQL Server licences with active Software Assurance."
        )
    )

    # Currency: USD only now; GBP/EUR when forex layer ships
    currency: str = Field(default="USD", description="Display currency. Currently only USD.")

    services: list[ServiceConfig] = Field(default_factory=list)

    @validator("cloud_provider")
    def validate_provider(cls, v):
        v = v.lower()
        if v not in SUPPORTED_PROVIDERS:
            raise ValueError(f"cloud_provider must be one of {sorted(SUPPORTED_PROVIDERS)}")
        return v

    @validator("currency")
    def validate_currency(cls, v):
        v = v.upper()
        if v not in SUPPORTED_CURRENCIES:
            raise ValueError(
                f"Currency '{v}' is not yet supported. "
                f"Supported: {sorted(SUPPORTED_CURRENCIES)}. "
                f"GBP and EUR support is planned."
            )
        return v

    @validator("azure_hybrid_benefit")
    def ahb_only_for_azure(cls, v, values):
        # Warn (but don't block) if AHB is set for non-Azure provider
        provider = values.get("cloud_provider", "")
        if v and provider and provider != "azure":
            # Reset silently — AHB is meaningless for AWS/GCP
            return False
        return v


class BOMUpdateServicesRequest(BaseModel):
    services: list[ServiceConfig]
    azure_hybrid_benefit: Optional[bool] = None
    currency: Optional[str] = None


class BOMResponse(BaseModel):
    id: int
    name: str
    cloud_provider: str
    azure_hybrid_benefit: bool
    currency: str
    services: list[dict]
    service_count: int
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _bom_to_response(bom: BillOfMaterials) -> dict:
    return {
        "id":                    bom.id,
        "name":                  bom.name,
        "cloud_provider":        bom.cloud_provider,
        "azure_hybrid_benefit":  bom.azure_hybrid_benefit,
        "currency":              bom.currency,
        "services":              bom.services or [],
        "service_count":         len(bom.services or []),
        "created_at":            bom.created_at.isoformat() if bom.created_at else None,
        "updated_at":            bom.updated_at.isoformat() if bom.updated_at else None,
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_bom(request: BOMCreateRequest, db: Session = Depends(get_db)):
    """
    Create a new Bill of Materials.
    Services can be added now or via PATCH /api/v1/bom/{id}/services later.
    """
    bom = BillOfMaterials(
        name                 = request.name,
        cloud_provider       = request.cloud_provider,
        azure_hybrid_benefit = request.azure_hybrid_benefit,
        currency             = request.currency,
        services             = [s.dict() for s in request.services],
    )
    db.add(bom)
    db.commit()
    db.refresh(bom)
    return _bom_to_response(bom)


@router.get("", status_code=status.HTTP_200_OK)
async def list_boms(db: Session = Depends(get_db)):
    """List all BOMs (summary view — no service configs)."""
    boms = db.query(BillOfMaterials).order_by(BillOfMaterials.created_at.desc()).all()
    return [_bom_to_response(b) for b in boms]


@router.get("/{bom_id}", status_code=status.HTTP_200_OK)
async def get_bom(bom_id: int, db: Session = Depends(get_db)):
    """Get a single BOM with full service configs."""
    bom = db.query(BillOfMaterials).filter(BillOfMaterials.id == bom_id).first()
    if not bom:
        raise HTTPException(status_code=404, detail=f"BOM {bom_id} not found")
    return _bom_to_response(bom)


@router.patch("/{bom_id}/services", status_code=status.HTTP_200_OK)
async def update_bom_services(
    bom_id: int,
    request: BOMUpdateServicesRequest,
    db: Session = Depends(get_db),
):
    """
    Replace the services list on an existing BOM.
    Optionally update azure_hybrid_benefit and currency too.
    """
    bom = db.query(BillOfMaterials).filter(BillOfMaterials.id == bom_id).first()
    if not bom:
        raise HTTPException(status_code=404, detail=f"BOM {bom_id} not found")

    bom.services = [s.dict() for s in request.services]

    if request.azure_hybrid_benefit is not None:
        # Enforce: AHB only for Azure
        if bom.cloud_provider != "azure" and request.azure_hybrid_benefit:
            raise HTTPException(
                status_code=400,
                detail="azure_hybrid_benefit is only applicable for Azure BOMs."
            )
        bom.azure_hybrid_benefit = request.azure_hybrid_benefit

    if request.currency is not None:
        currency = request.currency.upper()
        if currency not in SUPPORTED_CURRENCIES:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Currency '{currency}' not yet supported. "
                    f"Supported: {sorted(SUPPORTED_CURRENCIES)}. GBP/EUR planned."
                )
            )
        bom.currency = currency

    db.commit()
    db.refresh(bom)
    return _bom_to_response(bom)


@router.delete("/{bom_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bom(bom_id: int, db: Session = Depends(get_db)):
    """Delete a BOM and all its associated scenarios (cascade)."""
    bom = db.query(BillOfMaterials).filter(BillOfMaterials.id == bom_id).first()
    if not bom:
        raise HTTPException(status_code=404, detail=f"BOM {bom_id} not found")
    db.delete(bom)
    db.commit()
    return None
