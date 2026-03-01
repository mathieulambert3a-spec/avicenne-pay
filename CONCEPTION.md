# 📁 Conception : Avicenne Pay (Refonte 2026)

## 🎯 1. Vision et Contexte
**Avicenne Pay** est l'outil central de gestion des flux financiers et des déclarations d'activité pour la prépa Santé **Avicenne** (Lyon Est & Lyon Sud). 
**Objectif de la refonte :** Remplacer l'ancienne version instable par une architecture robuste (FastAPI/React) capable de gérer les nouveaux rôles (TOP, COM) et de sécuriser les données sensibles (NSS, IBAN).

**Chiffres clés :**
* **2 Sites :** Lyon Est (110 apprenants) / Lyon Sud (190 apprenants).
* **4 Produits :** PASS, LAS1, LAS2.
* **Effectifs :** 5 salariés + ~300 étudiants (P2 à D3).

---

## 💰 2. Modèles de Rémunération
Calcul automatique des coûts chargés (Coût entreprise) :

* **Cession de droits d'auteur (RESP & TCP) :** Missions au forfait.
  * **Coût chargé = Brut × 1,2**
* **CDDU (COM & autres missions horaires) :** Taux horaire (Max 100h/mois).
  * **Coût chargé = Brut × 1,7**
* **Forfait Parrainage :** Gratification fixe de **50 € / mois / filleul** (Max 4).

---

## 👥 3. Matrice détaillée des Rôles et Droits

### 👑 Administration
* **Périmètre :** Global.
* **Gestion :** Contrôle total des utilisateurs, référentiels et exports comptables.
* **Déclarations :** Vue globale. Statuts : `Brouillon`, `Soumise`, `Validée`. Renvoi en brouillon obligatoire avec commentaire motivé.

### 🎓 Coordinateurs
* **Périmètre :** Site principal (Est ou Sud).
* **Actions :** Gère les utilisateurs (RESP/TCP/TOP) de son site. Affecte les missions.
* **Validation :** Valide les déclarations des RESP, TCP et TOP de son périmètre.
* **Propre activité :** Saisit ses déclarations (soumises aux Admins).

### 📝 Responsables (RESP)
* **Périmètre :** 1 Site / 1 Programme / 1 Matière.
* **Actions :** Affecte les missions aux TCP de son périmètre.
* **Validation :** Valide les déclarations de ses TCP uniquement.
* **Propre activité :** Saisit ses déclarations (soumises au Coordinateur/Admin).

### 🛠️ TCP
* **Actions :** Saisie et soumission de ses propres déclarations via le référentiel pédagogique.

### 🤝 TOP (Responsables Parrains)
* **Périmètre :** Gestion d'une partie des parrains de son site. Sous l'autorité Coordinateurs/Admins.
* **Profil :** Doit renseigner son profil complet (NSS, IBAN, Adresse) pour paiement.
* **Gestion Utilisateurs :** Création/Modif/Suppression des parrains de son périmètre.
* **Affectation Étudiants :** Accès à la liste des étudiants inscrits (NOM, Prénom, Site, Programme, Mail, Tel) pour affectation manuelle aux parrains/marraines.
* **Propre activité :** Saisit ses déclarations.

### 🍼 Parrains / Marraines
* **Rémunération :** Automatique (50€/filleul). **Aucune déclaration à saisir.**
* **Actions :** Gère son profil complet et consulte les fiches de ses filleuls.
* **Comptabilité :** Les Admins extraient directement les montants basés sur le nombre de filleuls.

### 📣 TOP COM (Responsables Communication)
* **Périmètre :** Multi-sites (Est et Sud). Sous l'autorité directe des Admins.
* **Gestion Utilisateurs :** Gère l'intégralité des étudiants COM.
* **Missions :** Affecte les missions COM (Salons, JPO, fly, phoning). **Filtrage obligatoire par famille de mission.**
* **Validation :** Valide les déclarations des COM (renvoi possible en brouillon avec commentaire).
* **Propre activité :** Saisit ses déclarations (soumises aux Admins).

### 📱 COM (Étudiants Communication)
* **Périmètre :** Multi-sites. Sous l'autorité des TOPs COM.
* **Actions :** Saisit ses missions COM. Voit uniquement ses propres déclarations.
* **Validation :** Soumet ses déclarations aux TOP COM et Admins.

---

## 💾 4. Structure de Données (Entités SQL)

### Table `users` (Sécurisée)
* `id` (PK), `email` (Unique), `password_hash`, `role`
* `nom`, `prenom`, `adresse`, `code_postal`, `ville`, `telephone`
* `nss` (Masqué/Chiffré), `iban` (Masqué/Chiffré)
* `filiere`, `annee`, `site`, `programme`, `matiere`, `profil_complete` (Boolean)

### Table `etudiants_inscrits`
* `id` (PK), `nom`, `prenom`, `site`, `programme`, `mail`, `telephone`, `parrain_id` (FK)

### Table `missions` & `sous_missions`
* **Missions :** `id`, `titre`, `famille` (Péda, COM, Admin), `ordre`, `is_active`
* **Sous-Missions :** `id`, `mission_id` (FK), `titre`, `tarif`, `unite`, `ordre`, `is_active`

### Table `declarations` & `declaration_lignes`
* **Déclarations :** `id`, `user_id` (FK), `mois`, `annee`, `statut`, `commentaire_refus`
* **Lignes :** `id`, `declaration_id` (FK), `sous_mission_id` (FK), `quantite`

---

## 📝 5. Schémas de Validation (Pydantic)

* **DeclarationOut** : Inclut le calcul dynamique du `total_montant` et le détail des lignes.
* **DeclarationCreate** : Vérifie que `mois` est entre 1 et 12 et `annee` >= 2020.
* **LigneDeclarationCreate** : Validation stricte de `quantite > 0`.
* **ProfileUpdate** : Validation du format NSS (15 chiffres) et IBAN.

---

## 📋 6. Référentiel Exhaustif des Missions (TCP/RESP)

| Catégorie | Mission (Sous-type) | Tarif | Unité |
| :--- | :--- | :--- | :--- |
| **✍️ Rédiger supports** | LVL 1 - Pas/peu changements (1 p. max) | 10.0 | par support |
| | LVL 2 - Changements moyens (2-3 p.) | 25.0 | par support |
| | LVL 3 - Beaucoup changements (4 p.+) | 50.0 | par support |
| | LVL 4 - Créé de novo | 100.0 | par support |
| | LVL 5 - Créé de novo (> 30 p.) – UE1 uniquement | 200.0 | par support |
| **🎙️ Enregistrement** | Enregistrer et réécouter le cours | 10.0 | par heure |
| **📚 Entraînements** | LVL 1 - Questions de cours simples | 3.0 | par qcm |
| | LVL 2 - Questions intermédiaire (long/schéma) | 4.0 | par qcm |
| | LVL 3 - Questions d'exercice | 6.0 | par qcm |
| | LVL 4 - Exercice compliqué – UE2, UE3, UE6 | 8.0 | par qcm |
| **📖 Relecture annales** | Relecture des annales (si nécessaire) | 10.0 | par annale/année |
| **🎓 Formation** | Réunion de formation (Word, Teams, …) | 50.0 | par jour |
| **☀️ MAJ estivale** | Réintégrer MAPS n-1, relecture cours/fiches/ED | 300.0 | par semaine |
| **👨‍🏫 Animation** | Supports existants (Préparation incluse) | 12.0 | par heure |
| | Supports à créer (Préparation incluse) | 24.0 | par heure |
| **👔 Pré-colles** | Participation réunions pré-colles | 10.0 | par pré-colle |
| **📝 Relire/Corriger** | LVL 1 - Pas ou peu de changements | 3.0 | par support |
| | LVL 2 - Changements moyens | 5.0 | par support |
| | LVL 3 - Beaucoup de changements | 10.0 | par support |
| | LVL 4 - Créé de novo | 20.0 | par support |
| | LVL 5 - De novo long (>30 p.) – UE2, UE3, UE6 | 30.0 | par support |
| | LVL 6 - De novo long (>30 p.) – UE1 uniquement | 50.0 | par support |
| **📌 Post-it** | Créer Post-it de novo | 50.0 | par post-it |
| **✅ Corrections annales**| LVL 1 - Questions de cours simples | 1.5 | par qcm |
| | LVL 2 - Intermédiaire (énoncé/schéma) | 2.0 | par qcm |
| | LVL 3 - Questions d'exercice | 3.0 | par qcm |
| **💬 Permanences** | Questions/réponses PASS/LASS + forum | 10.0 | par heure |
| **👔 Gestion équipe** | Réunions, pré-colles, etc. | 50.0 | par mois |
| **💻 Intégration Théia**| Standard (QCM classique, images/texte) | 0.5 | par qcm |
| | Complexe (Formules maths - UE3, UE6) | 1.0 | par qcm |

---

## 📋 7. Référentiels Académiques

### Filières (Utilisateurs)
* Médecine, Pharmacie, Maïeutique, Odontologie, Kinésithérapie

### Matières par Programme

#### PASS
- UE_1, UE_2, UE_3, UE_4, UE_5, UE_6, UE_7, UE_8, MMOK, PHARMA
- Min SVE, Min SVH, Min SPS, Min EEEA, Min PHY_MECA, Min MATH, Min CHIMIE, Min STAPS, Min DROIT, ORAUX

#### LAS 1
- Physiologie, Anatomie, Biologie Cell, Biochimie, Biostats, Biophysique, Chimie, SSH, Santé Publique, ICM, HBDV

#### LAS 2
- Microbiologie, Biocell / Immuno, Biologie Dev, Enzmo / Métabo, Génétique, Physiologie, Statistiques, MES GSE

---

## ⚙️ 8. Unités Autorisées
- **Temps :** par heure, par jour, par mois, par séance.
- **Volume :** par qcm, par annale et par année, par post-it, par support / map.
- **Forfait :** forfait mise à jour estivale, par pré-colle.

---

## 🛠️ 9. Stack Technique
* **Frontend :** **React** (Utilisation de Tailwind pour le Dashboard).
* **Backend :** **FastAPI** (Python 3.10+).
* **Base de données :** **PostgreSQL** (Hébergée sur Render ou AWS RDS).
