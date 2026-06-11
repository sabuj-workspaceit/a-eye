from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ZoneRegion(Base):
    __tablename__ = "zone_regions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    zone_map_id: Mapped[int] = mapped_column(ForeignKey("zone_maps.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    coordinates: Mapped[str] = mapped_column(Text, nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    zone_map = relationship("ZoneMap", back_populates="regions")
    rules = relationship("Rule", back_populates="zone_region")
