"""
Client API pour ODK Central.
Gère l'authentification, la récupération des soumissions et des pièces jointes.
"""

import requests
import pandas as pd
import streamlit as st
import urllib.parse
from io import BytesIO, StringIO  # 👈 Ajout de StringIO ici pour le CSV


class ODKClient:
    """Client pour l'API ODK Central."""

    def __init__(self, server_url: str, email: str, password: str, project_id: int, form_id: str):
        self.server_url = server_url.rstrip("/")
        self.email = email
        self.password = password
        self.project_id = project_id
        self.form_id = form_id
        self.session = requests.Session()
        self._authenticated = False
        self.debug = True

    def authenticate(self) -> bool:
        """Authentification par session token."""
        try:
            resp = self.session.post(
                f"{self.server_url}/v1/sessions",
                json={"email": self.email, "password": self.password},
                timeout=30,
            )
            resp.raise_for_status()
            token = resp.json().get("token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            self._authenticated = True
            return True
        except requests.RequestException as e:
            st.error(f"❌ Erreur d'authentification ODK : {e}")
            return False

    # 🔄 LA FONCTION MODIFIÉE EST ICI :
    def get_submissions(self) -> pd.DataFrame:
        """Récupère toutes les soumissions du formulaire sous forme de DataFrame."""
        if not self._authenticated:
            if not self.authenticate():
                return pd.DataFrame()

        # URL modifiée pour cibler le CSV au lieu du OData .svc
        url = (
            f"{self.server_url}/v1/projects/{self.project_id}"
            f"/forms/{self.form_id}/submissions.csv"
        )
        try:
            resp = self.session.get(url, timeout=60)
            resp.raise_for_status()
            
            # Lecture directe du flux CSV dans Pandas
            df = pd.read_csv(StringIO(resp.text))
            
            if df.empty:
                return pd.DataFrame()
                
            return df
        except requests.RequestException as e:
            st.error(f"❌ Erreur de récupération des soumissions : {e}")
            return pd.DataFrame()

    def get_attachment(self, instance_id: str, filename: str) -> tuple[bytes | None, str | None]:
        """Télécharge une pièce jointe et retourne (content, error_msg)."""
        if not self._authenticated:
            if not self.authenticate():
                return None, "Authentification échouée"

        url = f"{self.server_url}/v1/projects/{self.project_id}/forms/{self.form_id}/submissions/{instance_id}/attachments/{filename}"
        
        if self.debug:
            print(f"[ODK DEBUG] Appel attachment : {url}")
        
        try:
            resp = self.session.get(url, timeout=30)
            if resp.status_code == 404:
                if self.debug:
                    print(f"[ODK DEBUG] ❌ 404 Not Found pour : {filename}")
                return None, f"404: Fichier non trouvé sur le serveur"
            resp.raise_for_status()
            print(f"[ODK DEBUG] ✅ Succès (200) pour : {filename} ({len(resp.content)} bytes)")
            return resp.content, None
        except requests.RequestException as e:
            msg = str(e)
            if "401" in msg or "403" in msg:
                return None, "Erreur de permissions (401/403)"
            return None, msg

    def get_attachment_image(self, instance_id: str, filename: str) -> tuple[BytesIO | None, str | None]:
        """Retourne (BytesIO, error_msg)."""
        content, error = self.get_attachment(instance_id, filename)
        if content:
            return BytesIO(content), None
        return None, error

    def get_choices_mapping(self, field_names: list = None) -> dict:
        """Télécharge le fichier XLSForm et extrait les labels."""
        if not self._authenticated:
            if not self.authenticate():
                return {}

        url = f"{self.server_url}/v1/projects/{self.project_id}/forms/{self.form_id}.xlsx"
        try:
            resp = self.session.get(url, timeout=30)
            if resp.status_code != 200:
                print(f"[ODK DEBUG] Impossible d'accéder au XLSForm (Code {resp.status_code})")
                return {}
            
            survey_df = pd.read_excel(BytesIO(resp.content), sheet_name="survey")
            list_names = set()
            
            # Si field_names n'est pas précisé, on récupère toutes les listes
            if not field_names:
                for idx, row in survey_df.iterrows():
                    type_val = str(row.get('type', ''))
                    if 'select_one' in type_val or 'select_multiple' in type_val:
                        list_names.add(type_val.replace('select_one', '').replace('select_multiple', '').strip())
            else:
                for fn in field_names:
                    row = survey_df[survey_df['name'] == fn]
                    if not row.empty:
                        type_val = str(row.iloc[0]['type'])
                        if 'select_one' in type_val or 'select_multiple' in type_val:
                            list_names.add(type_val.replace('select_one', '').replace('select_multiple', '').strip())
            
            if not list_names:
                print(f"[ODK DEBUG] Aucun type 'select_one/multiple' trouvé")
                return {}
                
            choices_df = pd.read_excel(BytesIO(resp.content), sheet_name="choices")
            choices_df = choices_df[choices_df['list_name'].isin(list_names)]
            
            if choices_df.empty:
                return {}
            
            label_col = 'label'
            for col in choices_df.columns:
                col_str = str(col).lower()
                if col_str.startswith('label'):
                    label_col = col
                    break
                    
            if 'name' not in choices_df.columns or label_col not in choices_df.columns:
                return {}
                
            # Dictionnaire global code -> label
            mapping = dict(zip(choices_df['name'].astype(str), choices_df[label_col].astype(str)))
            print(f"[ODK DEBUG] Mapping extrait: {len(mapping)} labels uniques.")
            return mapping
            
        except Exception as e:
            print(f"[ODK DEBUG] Erreur extraction XLSForm : {e}")
            return {}


def generate_demo_data() -> pd.DataFrame:
    """Génère des données fictives pour le mode démo avec gestion de la criticité."""
    import random
    from datetime import datetime, timedelta
    random.seed(42)

    etablissements = [
        "Pharmacie La Grâce", "Pharmacie du Peuple", "Pharmacie Santé Plus",
        "Pharmacie Lumière", "Dépôt Pharma Central", "Pharmacie Bénédiction",
        "Pharmacie Étoile", "Dépôt Médical Kinshasa", "Pharmacie La Foi",
        "Pharmacie Mont Amba", "Pharmacie Victoire", "Dépôt Pharma Ngaliema",
        "Pharmacie Espoir", "Pharmacie Alpha Santé", "Pharmacie La Paix",
    ]

    records = []
    base_lat = -4.4419
    base_lon = 15.2662
    start_date = datetime(2026, 4, 20)
    
    for i, nom in enumerate(etablissements):
        scores = {
            "a_pourcentage": float(round(random.uniform(20, 100), 1)),
            "b_pourcentage": float(round(random.uniform(20, 100), 1)),
            "c_pourcentage": float(round(random.uniform(20, 100), 1)),
            "d_pourcentage": float(round(random.uniform(20, 100), 1)),
            "e_pourcentage": float(round(random.uniform(20, 100), 1)),
            "f_pourcentage": float(round(random.uniform(20, 100), 1)),
            "g_pourcentage": float(round(random.uniform(20, 100), 1)),
            "h_pourcentage": float(round(random.uniform(20, 100), 1)),
            "i_pourcentage": float(round(random.uniform(20, 100), 1)),
        }
        total = float(round(sum(scores.values()) / 9.0, 1))
        
        lat = base_lat + random.uniform(-0.05, 0.05)
        lon = base_lon + random.uniform(-0.05, 0.05)
        eval_date = (start_date + timedelta(days=random.randint(0, 30))).strftime("%Y-%m-%d")
        
        if total >= 80:
            critique = random.randint(0, 0)
            majeur = random.randint(0, 10)
            mineur = random.randint(0, 5)
            remarque = random.randint(0, 1)
        elif total >= 60:
            critique = random.choice([0, 0, 0, 1])
            majeur = random.randint(8, 25)
            mineur = random.randint(3, 10)
            remarque = random.randint(0, 2)
        elif total >= 50:
            critique = random.randint(0, 2)
            majeur = random.randint(20, 45)
            mineur = random.randint(6, 15)
            remarque = random.randint(1, 3)
        else:
            critique = random.randint(2, 6)
            majeur = random.randint(40, 80)
            mineur = random.randint(10, 20)
            remarque = random.randint(1, 3)

        records.append({
            "__id": f"uuid:demo-{i+1:04d}",
            "nom_etablissement": nom,
            "total": total,
            "latitude": lat,
            "longitude": lon,
            "date_evaluation": eval_date,
            "total_critique": critique,
            "total_majeur": majeur,
            "total_mineur": mineur,
            "total_remarque": remarque,
            "total_taux_critique": float(round((critique / 15.0) * 100, 1)),
            "total_taux_majeur": float(round((majeur / 126.0) * 100, 1)),
            "total_taux_mineur": float(round((mineur / 24.0) * 100, 1)),
            "total_taux_remarque": float(round((remarque / 3.0) * 100, 1)),
            "a_critique": critique if random.random() > 0.5 else 0,
            "a_majeur": int(majeur * 0.1),
            "b_majeur": int(majeur * 0.1),
            "c_critique": critique - (critique if random.random() > 0.5 else 0),
            "c_majeur": int(majeur * 0.2),
            "c_mineur": int(mineur * 0.2),
            "d_critique": 0,
            "d_majeur": int(majeur * 0.1),
            "d_mineur": int(mineur * 0.2),
            "d_remarque": remarque,
            "e_critique": 0,
            "e_majeur": int(majeur * 0.2),
            "e_mineur": int(mineur * 0.3),
            "f_critique": 0,
            "f_majeur": int(majeur * 0.1),
            "f_mineur": int(mineur * 0.1),
            "g_majeur": int(majeur * 0.1),
            "g_mineur": int(mineur * 0.2),
            "h_majeur": int(majeur * 0.05),
            "i_majeur": int(majeur * 0.05),
            **scores,
            "aa2": f"auth_ouverture_{i+1}.jpg" if random.random() > 0.1 else None,
            "ea2": f"batiment_{i+1}.jpg" if random.random() > 0.2 else None,
            "ea9": f"plafond_{i+1}.jpg" if random.random() > 0.3 else None,
            "ea13": f"quarantaine_{i+1}.jpg" if random.random() > 0.2 else None,
            "ea15": f"rebuts_{i+1}.jpg" if random.random() > 0.3 else None,
            "img_quai": f"quai_{i+1}.jpg" if random.random() > 0.4 else None,
            "img_cantine": f"cantine_{i+1}.jpg" if random.random() > 0.5 else None,
            "img_salle_admin": f"salle_admin_{i+1}.jpg" if random.random() > 0.3 else None,
            "img_vestiaires": f"vestiaires_{i+1}.jpg" if random.random() > 0.4 else None,
            "img_installation": f"installations_{i+1}.jpg" if random.random() > 0.2 else None,
            "ec7": f"entrepot_{i+1}.jpg" if random.random() > 0.2 else None,
            "ec11": f"etagere_{i+1}.jpg" if random.random() > 0.2 else None,
            "ec15": f"stockage_{i+1}.jpg" if random.random() > 0.1 else None,
            "ec22": f"nuisibles_{i+1}.jpg" if random.random() > 0.3 else None,
            "ed4": f"thermo1_{i+1}.jpg" if random.random() > 0.2 else None,
            "ed6": f"thermo2_{i+1}.jpg" if random.random() > 0.4 else None,
            "eg4": f"hygro_{i+1}.jpg" if random.random() > 0.3 else None,
            "eg6": f"thermo_suivi_{i+1}.jpg" if random.random() > 0.3 else None,
            "eh6": f"cameras_{i+1}.jpg" if random.random() > 0.2 else None,
        })

    return pd.DataFrame(records)