import enum
from datetime import datetime
from sqlalchemy import Integer, ForeignKey, DateTime, Enum as SAEnum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class StatutDeclaration(str, enum.Enum):
    brouillon = "brouillon"
    soumise = "soumise"


class Declaration(Base):
    __tablename__ = "declarations"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    mois: Mapped[int] = mapped_column(Integer, nullable=False)
    annee: Mapped[int] = mapped_column(Integer, nullable=False)
    statut: Mapped[StatutDeclaration] = mapped_column(
        SAEnum(StatutDeclaration), default=StatutDeclaration.brouillon
    )
    soumise_le: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship("User", back_populates="declarations")
    lignes: Mapped[list["LigneDeclaration"]] = relationship(
        "LigneDeclaration", back_populates="declaration", cascade="all, delete-orphan"
    )
