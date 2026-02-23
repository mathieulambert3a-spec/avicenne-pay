from sqlalchemy import Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class LigneDeclaration(Base):
    __tablename__ = "lignes_declaration"

    id: Mapped[int] = mapped_column(primary_key=True)
    declaration_id: Mapped[int] = mapped_column(ForeignKey("declarations.id", ondelete="CASCADE"), nullable=False)
    sous_mission_id: Mapped[int] = mapped_column(ForeignKey("sous_missions.id"), nullable=False)
    quantite: Mapped[float] = mapped_column(Float, nullable=False)

    declaration: Mapped["Declaration"] = relationship("Declaration", back_populates="lignes")
    sous_mission: Mapped["SousMission"] = relationship("SousMission", back_populates="lignes")
