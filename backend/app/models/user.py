# backend/models/user.py

import enum
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import String, Boolean, DateTime, Enum as SAEnum, func, ForeignKey, text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.declaration import Declaration
    from app.models.mission import Mission

# ── 1. ENUMS MÉTIER (Rôles, Sites, Programmes...) ──────────────────────────

class Role(str, enum.Enum):
    admin = "admin"
    coordo = "coordo"
    resp = "resp"
    tcp = "tcp"
    top = "top"
    top_com = "top_com"
    com = "com"
    
class Site(str, enum.Enum):
    lyon_est = "Lyon Est"   
    lyon_sud = "Lyon Sud"

class Programme(str, enum.Enum):
    pass_ = "PASS"
    las1 = "LAS 1"
    las2 = "LAS 2"

class TypeContrat(str, enum.Enum):
    cddu = "CDDU"
    ccda = "CCDA"

# ── 2. MODÈLE UTILISATEUR ──────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    # --- IDENTIFICATION & AUTH ---
    id: Mapped[int] = mapped_column(primary_key=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)
    hashed_password: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    role: Mapped[Role] = mapped_column(SAEnum(Role, name="role_enum"), nullable=False)
    site: Mapped[Optional[Site]] = mapped_column(SAEnum(Site, name="site_enum"), nullable=True)

    # --- COORDONNÉES ---
    nom: Mapped[Optional[str]] = mapped_column(String(100))
    prenom: Mapped[Optional[str]] = mapped_column(String(100))
    telephone: Mapped[Optional[str]] = mapped_column(String(20))
    adresse: Mapped[Optional[str]] = mapped_column(String(255))
    code_postal: Mapped[Optional[str]] = mapped_column(String(10))
    ville: Mapped[Optional[str]] = mapped_column(String(100))
    
    date_naissance: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    lieu_naissance: Mapped[Optional[str]] = mapped_column(String(100))

    # --- HIÉRARCHIE (Auto-référencement) ---
    manager_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    manager: Mapped[Optional["User"]] = relationship(
        "User", 
        remote_side=[id], 
        back_populates="subordinates"
    )
    subordinates: Mapped[List["User"]] = relationship(
        "User", 
        back_populates="manager"
    )

    # --- DONNÉES SENSIBLES (Chiffrées pour la paie) ---
    nss_encrypted: Mapped[Optional[str]] = mapped_column(String(500))
    iban_encrypted: Mapped[Optional[str]] = mapped_column(String(500))
    profil_complete: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # --- CONTEXTE PÉDAGOGIQUE (Pour les RESP et TCP) ---
    programme: Mapped[Optional[Programme]] = mapped_column(SAEnum(Programme, name="programme_enum"))
    matiere: Mapped[Optional[str]] = mapped_column(String(100))

    # --- MÉTADONNÉES ---
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # --- RELATIONS ---
    # Déclarations dont cet user est l'auteur
    declarations: Mapped[List["Declaration"]] = relationship(
        "Declaration",
        foreign_keys="Declaration.user_id",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    # ── PROPRIÉTÉS MÉTIER (Logique pure, pas de HTML) ───────────────────────

    @property
    def type_contrat(self) -> TypeContrat:
        """Détermine automatiquement le type de contrat selon le rôle."""
        if self.role in [Role.coordo, Role.top_com, Role.com, Role.top]:
            return TypeContrat.cddu
        elif self.role in [Role.resp, Role.tcp]:
            return TypeContrat.ccda
        return TypeContrat.aucun

    @property
    def is_payment_profile_complete(self) -> bool:
        """Vérifie si les infos critiques de paie sont renseignées."""
        champs_obligatoires = [self.nom, self.prenom, self.adresse, self.ville, self.nss_encrypted, self.iban_encrypted]
        return all(val and str(val).strip() for val in champs_obligatoires)


    # ── 3. CONTRAINTES D'UNICITÉ DE SÉCURITÉ ────────────────────────────────────
    # Ces index empêchent (au niveau SQL) de créer des doublons impossibles selon ton cahier des charges

    __table_args__ = (
        # 1 seul COORDO par site
        Index(
            "uq_one_coordo_per_site",
            "site",
            unique=True,
            postgresql_where=text("role = 'coordo' AND is_active = true")
        ),
        # 1 seul TOP COM par site
        Index(
            "uq_one_top_com_per_site",
            "site",
            unique=True,
            postgresql_where=text("role = 'top_com' AND is_active = true")
        ),
        # 1 seul RESP par site / programme / matière
        Index(
            "uq_one_resp_per_matiere_site",
            "site", "programme", "matiere",
            unique=True,
            postgresql_where=text("role = 'resp' AND is_active = true AND matiere IS NOT NULL")
        ),
    )