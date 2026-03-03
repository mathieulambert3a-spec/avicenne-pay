import enum
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, Enum as SAEnum, func, Table, Column, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

# Table de liaison pour les permissions au niveau de la MISSION
user_mission_permissions = Table(
    "user_mission_permissions",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("mission_id", Integer, ForeignKey("missions.id", ondelete="CASCADE"), primary_key=True),
)

class Role(str, enum.Enum):
    admin = "admin"
    coordo = "coordo"
    resp = "resp"
    tcp = "tcp"

class Filiere(str, enum.Enum):
    medecine = "Médecine"
    pharmacie = "Pharmacie"
    maieutique = "Maïeutique"
    odontologie = "Odontologie"
    kinesitherapie = "Kinésithérapie"

class Annee(str, enum.Enum):
    p2 = "P2"
    d1 = "D1"
    d2 = "D2"

class Site(str, enum.Enum):
    lyon_est = "Lyon Est"
    lyon_sud = "Lyon Sud"

class Programme(str, enum.Enum):
    pass_ = "PASS"
    las1 = "LAS 1"
    las2 = "LAS 2"

MATIERES = {
    "PASS": ["UE_1", "UE_2", "UE_3", "UE_4", "UE_5", "UE_6", "UE_7", "UE_8", "MMOK", "PHARMA", "Min SVE", "Min SVH", "Min SPS", "Min EEEA", "Min PHY_MECA", "Min MATH", "Min CHIMIE", "Min STAPS", "Min DROIT", "ORAUX"],
    "LAS 1": ["Physiologie", "Anatomie", "Biologie Cell", "Biochimie", "Biostats", "Biophysique","Chimie", "SSH", "Santé Publique", "ICM", "HBDV"],
    "LAS 2": ["Microbiologie", "Biocell / Immuno", "Biologie Dev", "Enzmo / Métabo", "Génétique", "Physiologie", "Statistiques", "MES GSE"]
}

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[Role] = mapped_column(SAEnum(Role), nullable=False)

    nom: Mapped[str | None] = mapped_column(String(100))
    prenom: Mapped[str | None] = mapped_column(String(100))
    adresse: Mapped[str | None] = mapped_column(String(500))
    code_postal: Mapped[str | None] = mapped_column(String(10))
    ville: Mapped[str | None] = mapped_column(String(100))
    telephone: Mapped[str | None] = mapped_column(String(20))
    nss_encrypted: Mapped[str | None] = mapped_column(String(500))
    iban_encrypted: Mapped[str | None] = mapped_column(String(500))

    filiere: Mapped[Filiere | None] = mapped_column(SAEnum(Filiere))
    annee: Mapped[Annee | None] = mapped_column(SAEnum(Annee))
    site: Mapped[Site | None] = mapped_column(SAEnum(Site))
    programme: Mapped[Programme | None] = mapped_column(SAEnum(Programme))
    matiere: Mapped[str | None] = mapped_column(String(100))

    profil_complete: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # RELATIONS
    declarations: Mapped[list["Declaration"]] = relationship("Declaration", back_populates="user")
    
    missions_autorisees: Mapped[list["Mission"]] = relationship(
        "Mission",
        secondary=user_mission_permissions,
        backref="users_autorises"
    )