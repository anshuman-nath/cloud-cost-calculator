"""
Cost Scenario data model
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.utils.database import Base


class CostScenario(Base):
    """
    Cost Scenario - represents a pricing model applied to a BOM
    """
    __tablename__ = "cost_scenarios"

    id = Column(Integer, primary_key=True, index=True)
    bom_id = Column(Integer, ForeignKey("bill_of_materials.id"), nullable=False)

    scenario_name = Column(String(100), nullable=False)  # "PAYG", "1-Year RI", "3-Year RI"
    pricing_model = Column(String(50), nullable=False)  # payg, 1yr_ri, 3yr_ri, 1yr_sp, 3yr_sp

    # Cost calculations
    total_monthly_cost = Column(Float, nullable=False, default=0.0)
    total_annual_cost = Column(Float, nullable=False, default=0.0)
    savings_vs_payg = Column(Float, default=0.0)
    savings_percentage = Column(Float, default=0.0)

    # Detailed breakdown
    itemized_costs = Column(JSON, nullable=False, default=[])

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    bom = relationship("BillOfMaterials", back_populates="scenarios")

    def __repr__(self):
        return f"<CostScenario(id={self.id}, name='{self.scenario_name}', cost=${self.total_monthly_cost:.2f}/mo)>"
