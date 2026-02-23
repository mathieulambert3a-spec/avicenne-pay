from datetime import datetime
from sqlalchemy import String, Boolean, Integer, Float, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class SousMission(Base):
    __tablename__ = "sous_missions"

    id: Mapped[int] = mapped_column(primary_key=True)
    mission_id: Mapped[int] = mapped_column(ForeignKey("missions.id"), nullable=False)
    titre: Mapped[str] = mapped_column(String(500), nullable=False)
    tarif: Mapped[float] = mapped_column(Float, nullable=False)
    unite: Mapped[str | None] = mapped_column(String(100))
    ordre: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    mission: Mapped["Mission"] = relationship("Mission", back_populates="sous_missions")
    lignes: Mapped[list["LigneDeclaration"]] = relationship("LigneDeclaration", back_populates="sous_mission")
