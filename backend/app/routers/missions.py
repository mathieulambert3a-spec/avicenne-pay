# backend/routers/missions.py

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import Role, User
from app.models.mission import Mission, TypeContratMission
from app.schemas.mission import MissionCreate, MissionUpdate, MissionOut
from app.core.security import get_current_user, check_is_at_least_coordo

router = APIRouter(prefix="/missions", tags=["Missions"])

# 🔓 LECTURE : Filtrée selon le rôle (on garde la logique précédente)
@router.get("/", response_model=List[MissionOut])
def get_missions(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = db.query(Mission).filter(Mission.is_active == True)
    
    # Si l'utilisateur n'est NI admin NI resp, on lui cache les missions réservées aux responsables
    if current_user.role not in [Role.admin, Role.resp]:
        query = query.filter(Mission.is_resp_only == False)
        
    return query.all()


# 🔒 CRÉATION : Réservée aux Admins (Tout) et Coordos (Uniquement CCDA)
@router.post("/", response_model=MissionOut, status_code=status.HTTP_201_CREATED)
def create_mission(
    mission_in: MissionCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(check_is_at_least_coordo) # 🛡️ Plus besoin de if sur le rôle ici
):
    if current_user.role == Role.coordo and mission_in.type_contrat != TypeContratMission.ccda:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="En tant que Coordinateur, vous ne pouvez créer que des missions de type CCDA."
        )
        
    new_mission = Mission(**mission_in.model_dump())
    db.add(new_mission)
    db.commit()
    db.refresh(new_mission)
    return new_mission

# 🔒 MODIFICATION / TOGGLE : Réservée aux Admins (Tout) et Coordos (Uniquement CCDA)
@router.put("/{mission_id}", response_model=MissionOut)
def update_mission(
    mission_id: int,
    mission_in: MissionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_is_at_least_coordo) # 🛡️ Idem !
):
    db_mission = db.query(Mission).filter(Mission.id == mission_id).first()
    if not db_mission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mission introuvable.")
        
    if current_user.role == Role.coordo:
        # On l'empêche de toucher à une mission qui n'est pas CCDA
        if db_mission.type_contrat != TypeContratMission.ccda:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="En tant que Coordinateur, vous ne pouvez pas modifier une mission qui n'est pas CCDA."
            )
        # On l'empêche de transformer une CCDA en autre chose
        if mission_in.type_contrat and mission_in.type_contrat != TypeContratMission.ccda:
             raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous ne pouvez pas basculer une mission CCDA vers un autre type de contrat."
            )
        
    update_data = mission_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_mission, key, value)
        
    db.commit()
    db.refresh(db_mission)
    return db_mission


@router.delete("/{mission_id}", response_model=MissionOut) # 💡 On renvoie la mission modifiée !
def delete_mission(
    mission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_is_at_least_coordo) # 🛡️ Idem !
):
    db_mission = db.query(Mission).filter(Mission.id == mission_id).first()
    if not db_mission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mission introuvable.")
        
    if current_user.role == Role.coordo and db_mission.type_contrat != TypeContratMission.ccda:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="En tant que Coordinateur, vous ne pouvez désactiver que des missions de type CCDA."
        )
        
    # 💥 On ne supprime pas, on désactive !
    db_mission.is_active = False
    
    db.commit()
    db.refresh(db_mission)
    return db_mission