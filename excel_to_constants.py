import pandas as pd
import json
import os
import re

def extract_missions():
    file_path = "TEMPLATE_Declaration_DA.xlsm"
    output_path = "app/schemas/constants.py"
    
    try:
        df = pd.read_excel(file_path, sheet_name="MISSIONS", header=None)
    except Exception as e:
        print(f"❌ Erreur : {e}")
        return

    missions_initiales = {}
    current_mission_title = None
    current_unit = "Heure" # Unité par défaut

    BLACKLIST = ["MISSION TCP", "MISSIONS TCP", "MISSION RESP", "MISSIONS RESP", "SOUS-TOTAL", "TOTAL À VERSER", "DONT MISSIONS"]

    print("🔍 Analyse avec extraction des unités...")

    for index, row in df.iterrows():
        col_a = str(row[0]).strip() if pd.notna(row[0]) else ""
        col_b = str(row[1]).strip() if pd.notna(row[1]) else ""
        col_c = row[2] if pd.notna(row[2]) else None

        col_a_upper = col_a.upper()
        if any(word in col_a_upper for word in BLACKLIST) or not col_a:
            continue

        # --- 1. DÉTECTION MISSION ET UNITÉ ---
        if col_c is None and len(col_a) > 3:
            raw_title = col_a
            
            # Gestion des subtilités (oublis de l'Excel)
            if "Participation réunions pré-colles" in raw_title:
                current_unit = "par pré-colle"
                current_mission_title = raw_title
            elif "Mise à jour estivale" in raw_title:
                current_unit = "par semaine"
                current_mission_title = raw_title
            
            # Cas général : Titre – Unité
            elif "–" in raw_title or "-" in raw_title:
                # On sépare au premier tiret trouvé
                parts = re.split(r'[–-]', raw_title, maxsplit=1)
                current_mission_title = parts[0].strip()
                unit_part = parts[1].strip().lower()
                
                # On normalise l'unité (ex: "semaine" -> "par semaine")
                if "par" not in unit_part:
                    current_unit = f"par {unit_part}"
                else:
                    current_unit = unit_part
            else:
                current_mission_title = raw_title
                current_unit = "Heure"

            if current_mission_title not in missions_initiales:
                missions_initiales[current_mission_title] = []
            continue

        # --- 2. DÉTECTION SOUS-MISSION ---
        if current_mission_title and col_c is not None:
            full_sub_title = f"{col_a} - {col_b}" if col_b and col_b.lower() != "nan" else col_a
            
            missions_initiales[current_mission_title].append({
                "titre": full_sub_title,
                "tarif": float(col_c),
                "unite": current_unit  # Utilise l'unité extraite de la mission parente
            })

    # Nettoyage et sauvegarde
    missions_initiales = {k: v for k, v in missions_initiales.items() if v}
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# -*- coding: utf-8 -*-\n")
        f.write("MISSIONS_INITIALES = ")
        f.write(json.dumps(missions_initiales, indent=4, ensure_ascii=False))
        f.write("\n\nUNITES_CHOICES = ['Heure', 'par heure', 'par journée', 'par semaine', 'par pré-colle', 'MAP / support']\n")

    print(f"✅ Extraction terminée avec unités automatiques !")

if __name__ == "__main__":
    extract_missions()