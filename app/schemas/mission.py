from pydantic import BaseModel
from typing import Optional


class MissionCreate(BaseModel):
    titre: str
    ordre: int = 0
    is_active: bool = True


class MissionUpdate(BaseModel):
    titre: Optional[str] = None
    ordre: Optional[int] = None
    is_active: Optional[bool] = None


class SousMissionCreate(BaseModel):
    titre: str
    tarif: float
    unite: Optional[str] = None
    ordre: int = 0
    is_active: bool = True


class SousMissionUpdate(BaseModel):
    titre: Optional[str] = None
    tarif: Optional[float] = None
    unite: Optional[str] = None
    ordre: Optional[int] = None
    is_active: Optional[bool] = None
