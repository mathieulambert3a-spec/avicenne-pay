# backend/models/mission.py

import enum
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Float, Enum as SAEnum, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

# On garde un Enum pour les types de contrats
class TypeContratMission(str, enum.Enum):
    cddu = "CDDU"   
    ccda = "CCDA"
    both = "BOTH"

class Mission(Base):
    __tablename__ = "missions"

    id: Mapped[int] = mapped_column(primary_key=True)
    categorie: Mapped[str] = mapped_column(String(255), nullable=False)
    titre: Mapped[str] = mapped_column(String(255), nullable=False)
    
    type_contrat: Mapped[TypeContratMission] = mapped_column(
        SAEnum(TypeContratMission, native_enum=False), 
        default=TypeContratMission.ccda,
        nullable=False
    )
    
    # Tarification
    tarif_unitaire: Mapped[float] = mapped_column(Float, nullable=False)
    
    # L'unité en texte (ex: "par qcm", "par map / support")
    # On utilise du texte libre pour coller à tes UNITES_CHOICES
    unite: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Est-ce réservé aux RESP ? (Pour le forfait gestion d'équipe)
    is_resp_only: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Est-ce que la mission est toujours d'actualité ?
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())