# -*- coding: utf-8 -*-
# app/models/referentiels.py
import enum 

# ── 1. LE RÉFÉRENTIEL DES MATIÈRES ───────────────────────────────────────
MATIERES = {
    "PASS": [
        "UE_1", "UE_2", "UE_3", "UE_4", "UE_5", "UE_6", "UE_7", "UE_8",
        "MMOK", "PHARMA",
        "Min SVE", "Min SVH", "Min SPS", "Min EEEA",
        "Min PHY_MECA", "Min MATH", "Min CHIMIE", "Min STAPS",
        "Min DROIT", "ORAUX",
    ],
    "LAS 1": [
        "Physiologie", "Anatomie", "Biologie Cell", "Biochimie",
        "Biostats", "Biophysique", "Chimie", "SSH",
        "Santé Publique", "ICM", "HBDV",
    ],
    "LAS 2": [
        "Microbiologie", "Biocell / Immuno", "Biologie Dev",
        "Enzymo / Métabo", "Génétique", "Physiologie",
        "Statistiques", "MES GSE",
    ],
}

# ── 2. LES MISSIONS INITIALES ET TARIFS ──────────────────────────────────
MISSIONS_INITIALES = {
    # --- 1. CRÉATION ET RÉDACTION ---
    "✍️ Rédiger et mettre en page les supports de cours": [
        {"titre": "LVL 1 - Pas ou peu de changements : MAP finale d'1 page de texte max (hors schéma)", "tarif": 10.0, "unite": "par map / support"},
        {"titre": "LVL 2 - Changements moyens : MAP finale de 2 ou 3 pages (hors schéma)", "tarif": 25.0, "unite": "par map / support"},
        {"titre": "LVL 3 - Beaucoup de changements : MAP finale de 4 pages ou plus (hors schéma / MAJ de cours)", "tarif": 50.0, "unite": "par map / support"},
        {"titre": "LVL 4 - Support non existant, qui a dû être créé de novo", "tarif": 100.0, "unite": "par map / support"},
        {"titre": "LVL 5 - Support non existant, créé de novo, particulièrement long/difficile (> 30 pages) – Uniquement pour UE1", "tarif": 200.0, "unite": "par map / support"}
    ],
    "📚 Création d'entraînements (TD, ED, Colle, CCB)": [
        {"titre": "LVL 1 - Questions de cours, relativement simple à faire", "tarif": 3.0, "unite": "par qcm"},
        {"titre": "LVL 2 - Questions intermédiaire (énoncé long ou schéma)", "tarif": 4.0, "unite": "par qcm"},
        {"titre": "LVL 3 - Questions d'exercice", "tarif": 6.0, "unite": "par qcm"},
        {"titre": "LVL 4 - Questions d'exercice compliquée à faire – Possible uniquement UE2, UE3, UE6", "tarif": 8.0, "unite": "par qcm"}
    ],
    "📌 Création de Post-it": [
        {"titre": "Post-it - Créer Post-it de novo", "tarif": 50.0, "unite": "par post-it"}
    ],
    "💻 Intégration dans Théia": [
        {"titre": "Standard - QCM classique, images et/ou texte", "tarif": 0.5, "unite": "par qcm"},
        {"titre": "Complexe - QCM complexe, formules mathématiques (ex: UE3, UE6)", "tarif": 1.0, "unite": "par qcm"}
    ],

    # --- 2. ANIMATION ET TRANSMISSION ---
    "👨‍🏫 Animation de séances": [
        {"titre": "Supports existants - ED, TD, Stage pré-rentrée, TDR – Préparation incluse", "tarif": 12.0, "unite": "par heure"},
        {"titre": "Supports à créer - ED, TD, Stage pré-rentrée, TDR – Préparation incluse", "tarif": 24.0, "unite": "par heure"}
    ],
    "🎙️ Enregistrement": [
        {"titre": "Enregistrement - Enregistrer et réécouter le cours", "tarif": 10.0, "unite": "par heure"}
    ],
    "💬 Permanences et support": [
        {"titre": "Permanences - Questions/réponses PASS et LASS, y compris réponse au forum (séance de 2h)", "tarif": 10.0, "unite": "par heure"}
    ],

    # --- 3. RELECTURE ET MAINTENANCE ---
    "📝 Relire/vérifier/corriger/mettre en page les supports": [
        {"titre": "LVL 1 - Pas ou peu de changements : MAP finale d'1 page de texte max (hors schéma)", "tarif": 3.0, "unite": "par support"},
        {"titre": "LVL 2 - Changements moyens : MAP finale de 2 ou 3 pages (hors schéma)", "tarif": 5.0, "unite": "par support"},
        {"titre": "LVL 3 - Beaucoup de changements : MAP finale de 4 pages ou plus (hors schéma / MAJ de cours)", "tarif": 10.0, "unite": "par support"},
        {"titre": "LVL 4 - Support non existant, qui a dû être créé de novo", "tarif": 20.0, "unite": "par support"},
        {"titre": "LVL 5 - Support non existant, créé de novo, particulièrement long/difficile (> 30 pages) – Uniquement pour UE2, UE3 et UE6", "tarif": 30.0, "unite": "par support"},
        {"titre": "LVL 6 - Support non existant, créé de novo, particulièrement long/difficile (> 30 pages) – Uniquement pour l'UE1", "tarif": 50.0, "unite": "par support"}
    ],
    "📖 Relecture des annales": [
        {"titre": "Relecture des annales - Relecture des annales (si nécessaire)", "tarif": 10.0, "unite": "par annale et par année"}
    ],
    "✅ Création de corrections d'annales": [
        {"titre": "LVL 1 - Questions de cours, relativement simple à corriger", "tarif": 1.5, "unite": "par qcm"},
        {"titre": "LVL 2 - Questions intermédiaire (énoncé long ou schéma à légender)", "tarif": 2.0, "unite": "par qcm"},
        {"titre": "LVL 3 - Questions d'exercice", "tarif": 3.0, "unite": "par qcm"}
    ],

    # --- 4. GESTION ET FORMATION ---
    "👔 Participation réunions pré-colles": [
        {"titre": "Participation - Réunions pré-colles", "tarif": 10.0, "unite": "par pré-colle"}
    ],
    "👔 Gestion d'équipe": [
        {"titre": "Gestion d'équipe - Réunions, pré-colles, etc. – À BIEN DÉTAILLER", "tarif": 50.0, "unite": "par mois", "is_resp": True}
    ],
    "🎓 Formation": [
        {"titre": "Formation - Réunion de formation (Word, Teams, …)", "tarif": 50.0, "unite": "par jour"}
    ],

    # --- 5. SAISONNIER ---
    "☀️ Mise à jour estivale": [
        {"titre": "Mise à jour estivale - Réintégrer les MAPS n-1, Relire les cours, Post-it et fiches, Relecture ED & entraînements", "tarif": 300.0, "unite": "par semaine"}
    ]
}

# ── 3. LES UNITÉS DISPONIBLES ───────────────────────────────────────────
UNITES_CHOICES = [
    # --- TEMPS ---
    "par heure",
    "par jour",
    "par mois",
    "par séance",
    
    # --- VOLUME / RÉDACTION ---
    "par qcm",
    "par annale et par année",
    "par post-it",
    "par support / map",
    
    # --- FORFAITAIRE ---
    "forfait mise à jour estivale",
    "par pré-colle"
]

class Role(str, enum.Enum):
    admin   = "admin"
    coordo  = "coordo"
    resp    = "resp"
    tcp     = "tcp"
    top     = "top"
    top_com = "top_com"
    com     = "com"

class Filiere(str, enum.Enum):
    medecine       = "Médecine"
    pharmacie      = "Pharmacie"
    maieutique     = "Maïeutique"
    odontologie    = "Odontologie"
    kinesitherapie = "Kinésithérapie"

class Annee(str, enum.Enum):
    p2 = "P2"
    d1 = "D1"
    d2 = "D2"
    d3 = "D3"

class Site(str, enum.Enum):
    lyon_est = "Lyon Est"
    lyon_sud = "Lyon Sud"

class TypeContrat(str, enum.Enum):
    ccda = "CCDA"
    cddu = "CDDU"