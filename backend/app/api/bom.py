"""
Bill of Materials API endpoints
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.utils.database import get_db
from app.models.bom import BillOfMaterials
from app.models.service import BOMCreate, BOMResponse
from app.utils.logger import logger

router = APIRouter()


@router.post("/", response_model=BOMResponse, status_code=201)
def create_bom(bom: BOMCreate, db: Session = Depends(get_db)):
    """
    Create a new Bill of Materials
    """
    logger.info(f"Creating BOM: {bom.name}")

    db_bom = BillOfMaterials(
        name=bom.name,
        description=bom.description,
        cloud_provider=bom.cloud_provider,
        services=bom.services
    )

    db.add(db_bom)
    db.commit()
    db.refresh(db_bom)

    logger.info(f"Created BOM with ID: {db_bom.id}")

    return BOMResponse(
        id=db_bom.id,
        name=db_bom.name,
        description=db_bom.description,
        cloud_provider=db_bom.cloud_provider,
        services=db_bom.services,
        created_at=db_bom.created_at.isoformat(),
        updated_at=db_bom.updated_at.isoformat()
    )


@router.get("/", response_model=List[BOMResponse])
def list_boms(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    List all BOMs
    """
    boms = db.query(BillOfMaterials).offset(skip).limit(limit).all()

    return [
        BOMResponse(
            id=bom.id,
            name=bom.name,
            description=bom.description,
            cloud_provider=bom.cloud_provider,
            services=bom.services,
            created_at=bom.created_at.isoformat(),
            updated_at=bom.updated_at.isoformat()
        )
        for bom in boms
    ]


@router.get("/{bom_id}", response_model=BOMResponse)
def get_bom(bom_id: int, db: Session = Depends(get_db)):
    """
    Get a specific BOM by ID
    """
    bom = db.query(BillOfMaterials).filter(BillOfMaterials.id == bom_id).first()

    if not bom:
        raise HTTPException(status_code=404, detail="BOM not found")

    return BOMResponse(
        id=bom.id,
        name=bom.name,
        description=bom.description,
        cloud_provider=bom.cloud_provider,
        services=bom.services,
        created_at=bom.created_at.isoformat(),
        updated_at=bom.updated_at.isoformat()
    )


@router.put("/{bom_id}", response_model=BOMResponse)
def update_bom(bom_id: int, bom_update: BOMCreate, db: Session = Depends(get_db)):
    """
    Update a BOM
    """
    bom = db.query(BillOfMaterials).filter(BillOfMaterials.id == bom_id).first()

    if not bom:
        raise HTTPException(status_code=404, detail="BOM not found")

    bom.name = bom_update.name
    bom.description = bom_update.description
    bom.cloud_provider = bom_update.cloud_provider
    bom.services = bom_update.services

    db.commit()
    db.refresh(bom)

    logger.info(f"Updated BOM {bom_id}")

    return BOMResponse(
        id=bom.id,
        name=bom.name,
        description=bom.description,
        cloud_provider=bom.cloud_provider,
        services=bom.services,
        created_at=bom.created_at.isoformat(),
        updated_at=bom.updated_at.isoformat()
    )


@router.delete("/{bom_id}", status_code=204)
def delete_bom(bom_id: int, db: Session = Depends(get_db)):
    """
    Delete a BOM
    """
    bom = db.query(BillOfMaterials).filter(BillOfMaterials.id == bom_id).first()

    if not bom:
        raise HTTPException(status_code=404, detail="BOM not found")

    db.delete(bom)
    db.commit()

    logger.info(f"Deleted BOM {bom_id}")

    return None
