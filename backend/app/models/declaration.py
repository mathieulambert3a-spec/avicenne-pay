# backend/models/declaration.py

import enum
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Enum as SAEnum, DateTime, func, ForeignKey, Integer, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.user import User
from app.models.mission import Mission

# ── 1. ENUMS POUR LES STATUTS ──────────────────────────────────────────────

class StatutDeclaration(str, enum.Enum):
    brouillon = "brouillon"
    soumise = "soumise"
    validee = "validee"

# ── 2. TABLE DE LIAISON : LIGNES DE DÉCLARATION ────────────────────────────
# Cette table permet d'associer plusieurs missions à une même déclaration avec la quantité

class LigneDeclaration(Base):
    __tablename__ = "lignes_declaration"

    id: Mapped[int] = mapped_column(primary_key=True)
    declaration_id: Mapped[int] = mapped_column(ForeignKey("declarations.id", ondelete="CASCADE"))
    mission_id: Mapped[int] = mapped_column(ForeignKey("missions.id"))
    
    # Ex: 3.5 (pour 3h30), ou 5 (pour 5 QCM créés)
    quantite: Mapped[float] = mapped_column(Float, nullable=False)
    
    # On stocke le tarif unitaire au moment de la déclaration 
    # (très important pour l'historique si les tarifs évoluent plus tard !)
    tarif_applique: Mapped[float] = mapped_column(Float, nullable=False)

    # Relations
    mission: Mapped["Mission"] = relationship("Mission")


# ── 3. MODÈLE DÉCLARATION ──────────────────────────────────────────────────

class Declaration(Base):
    __tablename__ = "declarations"

    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Qui fait la déclaration ?
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Période concernée
    mois: Mapped[int] = mapped_column(Integer, nullable=False)  # De 1 à 12
    annee: Mapped[int] = mapped_column(Integer, nullable=False) # Ex: 2026
    
    statut: Mapped[StatutDeclaration] = mapped_column(
        SAEnum(StatutDeclaration, name="statut_declaration_enum"),
        default=StatutDeclaration.brouillon,
        nullable=False
    )

    # Validation
    validee_par_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    date_validation: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    
    # Le commentaire obligatoire en cas de refus / retour en brouillon
    commentaire_refus: Mapped[Optional[str]] = mapped_column(String(500))

    # Métadonnées
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relations
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], back_populates="declarations")
    validee_par: Mapped[Optional["User"]] = relationship("User", foreign_keys=[validee_par_id])
    
    # Permet de récupérer toutes les lignes (missions) de cette déclaration d'un coup
    lignes: Mapped[List["LigneDeclaration"]] = relationship("LigneDeclaration", cascade="all, delete-orphan")

    # ── PROPRIÉTÉS MÉTIER ───────────────────────────────────────────────────

    @property
    def total_remuneration(self) -> float:
        """Calcule automatiquement le montant total brut de la déclaration."""
        return sum(ligne.quantite * ligne.tarif_applique for ligne in self.lignes)