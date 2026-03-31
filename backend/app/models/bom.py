"""
Bill of Materials data model
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON
from sqlalchemy.orm import relationship

from app.utils.database import Base
from sqlalchemy import Column, Integer, String, Boolean, JSON, DateTime
from datetime import datetime

class BillOfMaterials(Base):
    """
    Bill of Materials - represents a collection of cloud services
    for cost estimation across multiple pricing scenarios.
    """
    __tablename__ = "bill_of_materials"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    cloud_provider = Column(String(20), nullable=False)  # "aws", "azure", "gcp"

    # Azure Hybrid Benefit toggle
    # Only relevant when cloud_provider == "azure"
    # True = customer has existing Windows Server / SQL Server licenses
    azure_hybrid_benefit = Column(Boolean, default=False, nullable=False)
    description = Column(String, nullable=True, default="")
    # List of service configs — each item is a dict:
    # {
    #   "service_name": str,
    #   "service_type": str,   # "compute", "database", "storage", etc.
    #   "config": { ...provider-specific fields... }
    # }
    services = Column(JSON, nullable=False, default=[])

    # Currency for display — USD now, extensible to GBP/EUR later
    currency = Column(String(10), default="USD", nullable=False)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    scenarios = relationship("CostScenario", back_populates="bom", cascade="all, delete-orphan")

    def __repr__(self):
        ahb = " [AHB]" if self.azure_hybrid_benefit else ""
        return f"<BillOfMaterials(id={self.id}, name='{self.name}', provider='{self.cloud_provider}'{ahb})>"
