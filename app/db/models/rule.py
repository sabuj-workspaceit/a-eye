from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Rule(Base):
    __tablename__ = "rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    zone_region_id: Mapped[int] = mapped_column(ForeignKey("zone_regions.id"), nullable=False)
    scan_type: Mapped[str] = mapped_column(String(50), nullable=False)
    condition: Mapped[str] = mapped_column(Text, nullable=False)
    finding: Mapped[str] = mapped_column(String(255), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    severity: Mapped[str] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    zone_region = relationship("ZoneRegion", back_populates="rules")
    findings = relationship("Finding", back_populates="rule")
