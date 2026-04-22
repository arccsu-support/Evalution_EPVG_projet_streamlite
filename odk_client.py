"""
Client API pour ODK Central.
Gère l'authentification, la récupération des soumissions et des pièces jointes.
"""

import requests
import pandas as pd
import streamlit as st
import urllib.parse
from io import BytesIO


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

    def get_submissions(self) -> pd.DataFrame:
        """Récupère toutes les soumissions du formulaire sous forme de DataFrame."""
        if not self._authenticated:
            if not self.authenticate():
                return pd.DataFrame()

        url = (
            f"{self.server_url}/v1/projects/{self.project_id}"
            f"/forms/{self.form_id}.svc/Submissions"
        )
        try:
            resp = self.session.get(url, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            records = data.get("value", [])
            if not records:
                return pd.DataFrame()
            df = pd.json_normalize(records)
            return df
        except requests.RequestException as e:
            st.error(f"❌ Erreur de récupération des soumissions : {e}")
            return pd.DataFrame()

    def get_attachment(self, instance_id: str, filename: str) -> tuple[bytes | None, str | None]:
        """Télécharge une pièce jointe et retourne (content, error_msg)."""
        if not self._authenticated:
            if not self.authenticate():
                return None, "Authentification échouée"

        # URL ODK Central pour les pièces jointes :
        # /v1/projects/{projectId}/forms/{xmlFormId}/submissions/{instanceId}/attachments/{filename}
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

    def get_choices_mapping(self, field_names: list) -> dict:
        """
        Télécharge le fichier XLSForm depuis ODK Central et extrait 
        les labels des choix pour un (ou plusieurs) champ(s) donné(s).
        Retourne un dictionnaire de type { choice_name: choice_label }.
        """
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
            for fn in field_names:
                row = survey_df[survey_df['name'] == fn]
                if not row.empty:
                    type_val = str(row.iloc[0]['type'])
                    if 'select_one' in type_val:
                        list_names.add(type_val.replace('select_one', '').strip())
            
            if not list_names:
                print(f"[ODK DEBUG] Aucun type 'select_one' trouvé pour {field_names}")
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
                
            mapping = dict(zip(choices_df['name'].astype(str), choices_df[label_col].astype(str)))
            print(f"[ODK DEBUG] Mapping extrait: {len(mapping)} labels.")
            return mapping
            
        except Exception as e:
            print(f"[ODK DEBUG] Erreur extraction XLSForm : {e}")
            return {}


def generate_demo_data() -> pd.DataFrame:
    """Génère des données fictives pour le mode démo."""
    import random
    random.seed(42)

    etablissements = [
        "Pharmacie La Grâce", "Pharmacie du Peuple", "Pharmacie Santé Plus",
        "Pharmacie Lumière", "Dépôt Pharma Central", "Pharmacie Bénédiction",
        "Pharmacie Étoile", "Dépôt Médical Kinshasa", "Pharmacie La Foi",
        "Pharmacie Mont Amba", "Pharmacie Victoire", "Dépôt Pharma Ngaliema",
        "Pharmacie Espoir", "Pharmacie Alpha Santé", "Pharmacie La Paix",
    ]

    records = []
    # Coordonnées centrales approximatives de Kinshasa
    base_lat = -4.4419
    base_lon = 15.2662
    
    for i, nom in enumerate(etablissements):
        # Utilisation de valeurs float explicites pour éviter les avertissements de type
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
        
        # Génération de coordonnées GPS aléatoires autour de Kinshasa
        lat = base_lat + random.uniform(-0.05, 0.05)
        lon = base_lon + random.uniform(-0.05, 0.05)
        
        records.append({
            "__id": f"uuid:demo-{i+1:04d}",
            "nom_etablissement": nom,
            "total": total,
            "latitude": lat,
            "longitude": lon,
            **scores,
            "aa2": f"auth_ouverture_{i+1}.jpg" if random.random() > 0.2 else None,
            "aa4": f"contrat_pharma_{i+1}.jpg" if random.random() > 0.3 else None,
            "b_image": f"systeme_qualite_{i+1}.jpg" if random.random() > 0.3 else None,
            "c_image": f"installations_{i+1}.jpg" if random.random() > 0.2 else None,
            "d_image": f"equipements_{i+1}.jpg" if random.random() > 0.3 else None,
            "e_image": f"stocks_{i+1}.jpg" if random.random() > 0.3 else None,
            "f_image": f"approvisionnement_{i+1}.jpg" if random.random() > 0.4 else None,
            "g_image": f"distribution_{i+1}.jpg" if random.random() > 0.3 else None,
            "h_image": f"auto_inspection_{i+1}.jpg" if random.random() > 0.4 else None,
        })

    return pd.DataFrame(records)
