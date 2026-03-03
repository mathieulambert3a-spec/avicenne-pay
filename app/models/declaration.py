import enum
from datetime import datetime
from sqlalchemy import Integer, ForeignKey, DateTime, Enum as SAEnum, func, String, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.user import Site, Programme

class StatutDeclaration(str, enum.Enum):
    brouillon = "brouillon"
    soumise = "soumise"
    validee = "validee"

class Declaration(Base):
    __tablename__ = "declarations"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    site: Mapped[Site] = mapped_column(SAEnum(Site), nullable=False)
    programme: Mapped[Programme] = mapped_column(SAEnum(Programme), nullable=False)
    mois: Mapped[int] = mapped_column(Integer, nullable=False)
    annee: Mapped[int] = mapped_column(Integer, nullable=False)
    statut: Mapped[StatutDeclaration] = mapped_column(
        SAEnum(StatutDeclaration), default=StatutDeclaration.brouillon
    )
    
    # LE NOUVEAU CHAMP
    commentaire_admin: Mapped[str | None] = mapped_column(String(500))

    soumise_le: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # RELATIONS
    user: Mapped["User"] = relationship("User", back_populates="declarations")
    lignes: Mapped[list["LigneDeclaration"]] = relationship(
        "LigneDeclaration", back_populates="declaration", cascade="all, delete-orphan"
    )

class LigneDeclaration(Base):
    __tablename__ = "lignes_declaration"

    id: Mapped[int] = mapped_column(primary_key=True)
    declaration_id: Mapped[int] = mapped_column(ForeignKey("declarations.id", ondelete="CASCADE"), nullable=False)
    sous_mission_id: Mapped[int] = mapped_column(ForeignKey("sous_missions.id"), nullable=False)
    quantite: Mapped[float] = mapped_column(Float, nullable=False) # Nombre d'heures ou d'unités

    # RELATIONS
    declaration: Mapped["Declaration"] = relationship("Declaration", back_populates="lignes")
    sous_mission: Mapped["SousMission"] = relationship("SousMission")