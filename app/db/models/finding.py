from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Finding(Base):
    __tablename__ = "findings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    analysis_job_id: Mapped[int] = mapped_column(ForeignKey("analysis_jobs.id"), nullable=False)
    rule_id: Mapped[int] = mapped_column(ForeignKey("rules.id"), nullable=False)
    zone_region_id: Mapped[int] = mapped_column(ForeignKey("zone_regions.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    analysis_job = relationship("AnalysisJob", back_populates="findings")
    rule = relationship("Rule", back_populates="findings")
    zone_region = relationship("ZoneRegion")
    observations = relationship("Observation", back_populates="finding")
