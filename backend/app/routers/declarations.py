# backend/routers/declarations.py

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from app.database import get_db
from app.core.security import get_current_user
from app.models.user import User, Role
from app.models.declaration import Declaration, LigneDeclaration, StatutDeclaration
from app.models.mission import Mission
from app.schemas.declaration import DeclarationCreate, DeclarationOut, DeclarationUpdate, DeclarationReview
from app.core.security import check_peut_valider_declaration

router = APIRouter(prefix="/declarations", tags=["Déclarations"])

# ── 1. CREATE DÉCLARATION ──────────────────────────────────────────────────
@router.post("/", response_model=DeclarationOut, status_code=status.HTTP_201_CREATED)
def create_declaration(
    declaration_in: DeclarationCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) # 🔒 On injecte l'utilisateur connecté
):
    
    # 1. On crée l'enveloppe de la déclaration
    db_declaration = Declaration(
        user_id=current_user.id, # 👤 On utilise le VRAI ID extrait du Token JWT !
        mois=declaration_in.mois,
        annee=declaration_in.annee,
        statut=StatutDeclaration.brouillon
    )
    
    db.add(db_declaration)
    db.flush() # Récupère l'ID de la déclaration sans valider la transaction complète
    
    # 2. On traite chaque ligne envoyée
    for ligne in declaration_in.lignes:
        # On va chercher la mission en base pour connaître son tarif actuel
        db_mission = db.query(Mission).filter(Mission.id == ligne.mission_id).first()
        
        if not db_mission:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"La mission avec l'ID {ligne.mission_id} n'existe pas."
            )
            
        # On crée la ligne avec le tarif "photographié" au moment de la déclaration
        db_ligne = LigneDeclaration(
            declaration_id=db_declaration.id,
            mission_id=ligne.mission_id,
            quantite=ligne.quantite,
            tarif_applique=db_mission.tarif_unitaire # 💡 Toujours magique !
        )
        db.add(db_ligne)
        
    db.commit()
    db.refresh(db_declaration)
    
    return db_declaration

# ── 2. UPDATE DÉCLARATION ──────────────────────────────────────────────────
@router.put("/{declaration_id}", response_model=DeclarationOut)
def update_declaration(
    declaration_id: int, 
    declaration_in: DeclarationUpdate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) # 🔒 Authentification requise
):
    db_declaration = db.query(Declaration).filter(Declaration.id == declaration_id).first()
    
    if not db_declaration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Déclaration introuvable.")
        
    # 🔒 SÉCURITÉ : Est-ce que cette déclaration appartient bien à l'utilisateur connecté ?
    if db_declaration.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'êtes pas autorisé à modifier cette déclaration."
        )
        
    if db_declaration.statut != StatutDeclaration.brouillon:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Impossible de modifier une déclaration déjà soumise ou validée."
        )
        
    if declaration_in.mois:
        db_declaration.mois = declaration_in.mois
    if declaration_in.annee:
        db_declaration.annee = declaration_in.annee
        
    if declaration_in.lignes is not None:
        db.query(LigneDeclaration).filter(LigneDeclaration.declaration_id == declaration_id).delete()
        
        for ligne in declaration_in.lignes:
            db_mission = db.query(Mission).filter(Mission.id == ligne.mission_id).first()
            if not db_mission:
                db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"La mission avec l'ID {ligne.mission_id} n'existe pas."
                )
                
            db_ligne = LigneDeclaration(
                declaration_id=db_declaration.id,
                mission_id=ligne.mission_id,
                quantite=ligne.quantite,
                tarif_applique=db_mission.tarif_unitaire 
            )
            db.add(db_ligne)
            
    db.commit()
    db.refresh(db_declaration)
    return db_declaration

# ── 3. SOUMETTRE DÉCLARATION ───────────────────────────────────────────────
@router.post("/{declaration_id}/soumettre", response_model=DeclarationOut)
def soumettre_declaration(
    declaration_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) # 🔒 Authentification requise
):
    db_declaration = db.query(Declaration).filter(Declaration.id == declaration_id).first()
    
    if not db_declaration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Déclaration introuvable.")
        
    # 🔒 SÉCURITÉ : Est-ce que cette déclaration appartient bien à l'utilisateur connecté ?
    if db_declaration.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'êtes pas autorisé à soumettre cette déclaration."
        )
        
    if db_declaration.statut != StatutDeclaration.brouillon:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Impossible de soumettre une déclaration avec le statut '{db_declaration.statut}'."
        )
        
    if not db_declaration.lignes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossible de soumettre une déclaration vide sans aucune mission."
        )
        
    db_declaration.statut = StatutDeclaration.soumise
    
    db.commit()
    db.refresh(db_declaration)
    return db_declaration

# ── 4. REVIEW DÉCLARATION (ADMIN / COORDO) ──────────────────────────────────
@router.post("/{declaration_id}/review", response_model=DeclarationOut)
def review_declaration(
    declaration_id: int, 
    review_in: DeclarationReview, 
    db: Session = Depends(get_db),
    # 🛡️ Bloque l'accès si l'user n'est ni Admin ni Coordo
    current_user: User = Depends(check_peut_valider_declaration) 
):
    db_declaration = db.query(Declaration).filter(Declaration.id == declaration_id).first()
    
    if not db_declaration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Déclaration introuvable.")
        
    if db_declaration.statut != StatutDeclaration.soumise:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Seules les déclarations au statut 'soumise' peuvent être validées ou refusées."
        )

    auteur = db_declaration.user

    # 🔒 VERROU DE SITE : Le Coordo ne peut valider que sur son site
    if current_user.role == Role.coordo:
        if auteur.site != current_user.site:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Un Coordinateur ne peut valider que les déclarations des utilisateurs de son site."
            )

    # 📝 TRAITEMENT
    if review_in.statut == StatutDeclaration.brouillon:
        if not review_in.commentaire_refus or len(review_in.commentaire_refus.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Un commentaire est obligatoire pour justifier le refus."
            )
        db_declaration.statut = StatutDeclaration.brouillon
        db_declaration.commentaire_refus = review_in.commentaire_refus
        
    elif review_in.statut == StatutDeclaration.validee:
        db_declaration.statut = StatutDeclaration.validee
        db_declaration.date_validation = func.now() 
        db_declaration.commentaire_refus = None 
        db_declaration.validee_par_id = current_user.id 
        
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Action invalide. Choisissez 'validee' ou 'brouillon'."
        )
        
    db.commit()
    db.refresh(db_declaration)
    return db_declaration

# ── 5. GET DECLARATION ──────────────────────────────────
@router.get("/", response_model=List[DeclarationOut])
def get_declarations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Declaration)

    # 🛡️ 1. L'Admin voit TOUT
    if current_user.role == Role.admin:
        pass 

    # 🛡️ 2. Le COORDO (Voit les siennes + RESP et TCP de son site)
    elif current_user.role == Role.coordo:
        query = query.join(User, Declaration.user_id == User.id).filter(
            or_(
                Declaration.user_id == current_user.id,
                (User.site == current_user.site) & (User.role.in_([Role.resp, Role.tcp]))
            )
        )

    # 🛡️ 3. Le RESP (Voit les siennes + TCP de son triplet)
    elif current_user.role == Role.resp:
        query = query.join(User, Declaration.user_id == User.id).filter(
            or_(
                Declaration.user_id == current_user.id,
                (User.site == current_user.site) & 
                (User.programme == current_user.programme) & 
                (User.matiere == current_user.matiere) & 
                (User.role == Role.tcp)
            )
        )

    # 🛡️ 4. Le TOP COM (Voit les siennes + les COM de son site)
    elif current_user.role == Role.top_com:  # Adapte le nom de l'enum si c'est different !
        query = query.join(User, Declaration.user_id == User.id).filter(
            or_(
                Declaration.user_id == current_user.id,
                (User.site == current_user.site) & (User.role == Role.com)
            )
        )

    # 🛡️ 5. Tous les autres (TOP, COM, TCP) ne voient QUE les siennes
    else:
        query = query.filter(Declaration.user_id == current_user.id)

    declarations = query.order_by(Declaration.created_at.desc()).all()
    return declarations