"""
Dashboard EPVG — Habilitation & Expertise
Application Streamlit pour le monitoring et l'aide à la décision
pour l'évaluation des établissements pharmaceutiques (EPVG) à Kinshasa.
"""

import os
import streamlit as st
import pandas as pd
import urllib.parse
import plotly.graph_objects as go
from io import BytesIO
from datetime import datetime
from dotenv import load_dotenv
from typing import Optional
import base64
import folium
from streamlit_folium import st_folium


# Load .env explicitly from the script's directory
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path)
from odk_client import ODKClient, generate_demo_data
from database import save_decision, get_decision, get_all_decisions
from scoring import (
    SCORE_COLUMNS, RUBRIQUE_LABELS, PHOTO_FIELDS,
    NIVEAUX_BPSD, DECISION_OPTIONS, classify_bpsd, categorize,
)

def get_secret(key, default_value=""):
    try:
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return os.getenv(key, default_value)

# Constantes d'authentification
APP_USER = get_secret("APP_USER", "admin")
APP_PASSWORD = get_secret("APP_PASSWORD", "admin")

# ── Configuration de la page ─────────────────────────────────────────────────
st.set_page_config(
    page_title="Dashboard EPVG — Habilitation",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS personnalisé ─────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    /* ── Global ────────────────────────────────────────── */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    .main .block-container {
        padding-top: 1.5rem;
        max-width: 1300px;
    }

    /* ── Header ────────────────────────────────────────── */
    .dashboard-header {
        background: linear-gradient(135deg, #0B2447 0%, #19376D 50%, #576CBC 100%);
        border-radius: 16px;
        padding: 2rem 2.5rem;
        margin-bottom: 1.8rem;
        color: white;
        box-shadow: 0 8px 32px rgba(11, 36, 71, 0.25);
    }
    .dashboard-header h1 {
        margin: 0;
        font-size: 1.9rem;
        font-weight: 800;
        letter-spacing: -0.5px;
    }
    .dashboard-header p {
        margin: 0.3rem 0 0 0;
        font-size: 0.95rem;
        opacity: 0.85;
    }

    /* ── KPI Cards ─────────────────────────────────────── */
    .kpi-card {
        background: white;
        border-radius: 14px;
        padding: 1.3rem 1.5rem;
        box-shadow: 0 2px 12px rgba(0,0,0,0.06);
        border-left: 5px solid;
        transition: transform 0.2s ease;
        height: 100%;
    }
    .kpi-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.1);
    }
    .kpi-value {
        font-size: 2rem;
        font-weight: 800;
        line-height: 1.1;
    }
    .kpi-label {
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: #64748b;
        font-weight: 600;
        margin-top: 0.3rem;
    }

    /* ── Score global card ─────────────────────────────── */
    .score-card {
        border-radius: 16px;
        padding: 1.8rem 2rem;
        text-align: center;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
    }
    .score-card .score-value {
        font-size: 3.5rem;
        font-weight: 800;
        line-height: 1;
    }
    .score-card .score-label {
        font-size: 1rem;
        font-weight: 600;
        margin-top: 0.5rem;
    }

    /* ── Photo gallery ─────────────────────────────────── */
    .photo-card {
        background: #f8fafc;
        border-radius: 12px;
        padding: 0.8rem;
        text-align: center;
        border: 1px solid #e2e8f0;
        transition: all 0.2s ease;
        height: 100%;
        display: flex;
        flex-direction: column;
    }
    .photo-card:hover {
        border-color: #576CBC;
        box-shadow: 0 4px 16px rgba(0,0,0,0.08);
        transform: translateY(-2px);
    }
    
    /* Wrapper standardisé pour uniformiser la taille de toutes les photos */
    .photo-wrapper {
        width: 100%;
        height: 180px; 
        border-radius: 8px;
        overflow: hidden;
        margin-bottom: 0.5rem;
        background: #e2e8f0;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    /* Cibler les images Streamlit générées dans le wrapper */
    .photo-card img {
        width: 100% !important;
        height: 180px !important;
        object-fit: cover !important;
        border-radius: 8px !important;
    }

    .photo-label {
        font-size: 0.8rem;
        font-weight: 600;
        color: #334155;
        margin-top: auto;
        padding-top: 0.5rem;
        line-height: 1.2;
    }
    
    .photo-missing {
        display: flex;
        align-items: center;
        justify-content: center;
        height: 180px;
        background: #f1f5f9;
        border-radius: 8px;
        color: #94a3b8;
        font-size: 0.85rem;
        width: 100%;
    }


    /* ── Decision form ─────────────────────────────────── */
    .decision-section {
        background: linear-gradient(135deg, #fefce8, #fef9c3);
        border-radius: 16px;
        padding: 1.5rem 2rem;
        border: 1px solid #fde047;
        margin-top: 1rem;
    }

    /* ── Sidebar styling ───────────────────────────────── */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0B2447 0%, #19376D 100%);
    }
    section[data-testid="stSidebar"] .stMarkdown,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] .stSelectbox label,
    section[data-testid="stSidebar"] .stRadio label {
        color: white !important;
    }

    /* ── Divider ───────────────────────────────────────── */
    .section-divider {
        border: none;
        height: 2px;
        background: linear-gradient(90deg, transparent, #cbd5e1, transparent);
        margin: 2rem 0;
    }
    
    /* ── Login Box ─────────────────────────────────────── */
    .login-container {
        max-width: 400px;
        margin: 5rem auto;
        padding: 2.5rem;
        background: white;
        border-radius: 16px;
        box-shadow: 0 10px 40px rgba(11, 36, 71, 0.1);
        text-align: center;
    }
    .login-container h2 {
        color: #0B2447;
        margin-bottom: 1.5rem;
        font-weight: 800;
    }
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
from PIL import Image
import os

logo_path = os.path.join(os.path.dirname(__file__), "assets", "logo.png")
logo_img = None
if os.path.exists(logo_path):
    logo_img = Image.open(logo_path)

col1, col2 = st.columns([1, 4])
with col1:
    if logo_img:
        st.image(logo_img, use_container_width=True)
with col2:
    st.markdown("""
    <div class="dashboard-header">
        <h1>🏥 Dashboard EPVG — Habilitation & Expertise</h1>
        <p>Monitoring et aide à la décision • Évaluation des Établissements Pharmaceutiques • Kinshasa</p>
    </div>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# AUTHENTIFICATION
# ══════════════════════════════════════════════════════════════════════════════
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

# Auto-correction si la session est dans un état incohérent (ex: ancienne session avec "admin")
if st.session_state["authenticated"] and "odk_server_url" not in st.session_state:
    st.session_state["authenticated"] = False
    st.rerun()

if not st.session_state["authenticated"]:
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    if logo_img:
        st.image(logo_img, width=150)
    st.markdown("<h2>🔒 Accès Sécurisé</h2>", unsafe_allow_html=True)
    
    with st.form("login_form"):
        app_password = st.text_input("Mot de passe Application", type="password")
        submit_button = st.form_submit_button("Se Connecter", use_container_width=True)

        if submit_button:
            if app_password == get_secret("APP_ACCESS_PASSWORD"):
                st.session_state["authenticated"] = True
                # Récupérer les identifiants ODK (hybride : st.secrets ou .env)
                server_url = get_secret("ODK_SERVER_URL", "")
                email = get_secret("ODK_EMAIL", "")
                odk_password = get_secret("ODK_PASSWORD", "")
                project_id = int(get_secret("ODK_PROJECT_ID", 1))
                form_id = get_secret("ODK_FORM_ID", "Formulaire_evaluation_epvg_phase2")
                # Stocker dans la session pour l'interface de filtrage/barre latérale
                st.session_state["odk_server_url"] = server_url
                st.session_state["odk_email"] = email
                st.session_state["odk_password"] = odk_password
                st.session_state["odk_project_id"] = project_id
                st.session_state["odk_form_id"] = form_id
                # Tester la connexion ODK directement
                if server_url and email and odk_password:
                    try:
                        client_test = ODKClient(server_url, email, odk_password, project_id, form_id)
                        if client_test.authenticate():
                            st.session_state["odk_client"] = client_test
                        else:
                            st.warning("⚠️ Connecté à l'app, mais la connexion à ODK a échoué. Identifiants rejetés.")
                    except Exception as e:
                        st.error("❌ Impossible de joindre le serveur. L'adresse est peut-être incorrecte ou le serveur est hors-ligne.")
                st.rerun()
            else:
                st.error("❌ Mot de passe invalide.")
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()  # Stoppe l'exécution ici si non authentifié

# Initialisation par défaut pour éviter les NameError
df = pd.DataFrame()

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR — CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════
load_dotenv()

with st.sidebar:
    if logo_img:
        st.image(logo_img, use_container_width=True)
    st.markdown("### ⚙️ Source de données")

    mode = st.radio(
        "Mode de connexion",
        ["🌐 ODK Central", "🧪 Données démo"],
        index=0,
        help="ODK Central : lecture des données réelles. Démo : données fictives.",
    )

    odk_client: Optional['ODKClient'] = None

    if mode == "🌐 ODK Central":
        st.markdown("---")
        # Récupération automatique du client ODK à partir de la session globale (de la page de connexion)
        if "authenticated" in st.session_state and st.session_state["authenticated"]:
             # Extract saved credentials from session state
             server_url = st.session_state.get("odk_server_url")
             email = st.session_state.get("odk_email")
             password = st.session_state.get("odk_password")
             project_id = st.session_state.get("odk_project_id")
             form_id = st.session_state.get("odk_form_id")

             if server_url and email and password:
                  if "odk_client" not in st.session_state:
                      try:
                          auto_client = ODKClient(server_url, email, password, project_id, form_id)
                          with st.spinner("🔄 Connexion à ODK Central…"):
                              if auto_client.authenticate():
                                  st.session_state["odk_client"] = auto_client
                                  st.success("✅ Connecté automatiquement")
                              else:
                                  st.error("❌ Échec de la connexion. Identifiants rejetés.")
                      except Exception as e:
                          st.error("❌ Impossible de joindre le serveur. Adresse incorrecte ou serveur hors-ligne.")
                              
             if "odk_client" in st.session_state:
                  odk_client = st.session_state["odk_client"]
                  st.caption("🟢 Connecté à ODK Central")
             
             if st.button("🔄 Rafraîchir la connexion", use_container_width=True):
                 st.cache_data.clear()
                 st.rerun()
            
    st.markdown("---")
    st.markdown("### 🧭 Navigation")
    
    page = st.radio(
        "Aller à la page :",
        ["📊 Statistiques Générales", "🏥 Évaluation Détaillée"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    if st.button("🚪 Se Déconnecter", use_container_width=True):
        st.session_state["authenticated"] = False
        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# CHARGEMENT DES DONNÉES
# ══════════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=300, show_spinner="📥 Chargement des données depuis ODK Central…")
def load_odk_data(_client: ODKClient) -> pd.DataFrame:
    return _client.get_submissions()


@st.cache_data(ttl=3600, show_spinner=False)
def load_labels_mapping(_client: ODKClient) -> dict:
    return _client.get_choices_mapping([
        "nom_etablissement", "nom_pharmacie", 
        "province_etablissement", "ville_etablissement", 
        "zone_sante", "zone", "province"
    ])

mapping_noms = {}

if mode == "🌐 ODK Central" and odk_client:
    df = load_odk_data(odk_client)
    mapping_noms = load_labels_mapping(odk_client)
elif mode == "🧪 Données démo":
    df = generate_demo_data()
else:
    st.info("⏳ En attente de connexion à ODK Central. Vérifiez vos paramètres dans la barre latérale.")
    st.stop()

if df.empty:
    st.warning("⚠️ Aucune donnée disponible. Vérifiez la connexion ODK ou passez en mode démo.")
    st.stop()

# ══════════════════════════════════════════════════════════════════════════════
# TRAITEMENT DES DONNÉES ET MAPPING DES COLONNES
# ══════════════════════════════════════════════════════════════════════════════
# Helper pour extraire une valeur de manière robuste (même si imbriquée dans des dicts ou avec préfixes)
def get_nested_val(data, target_key):
    target_key_lower = target_key.lower()
    
    # Cas 1: Si data est une Series (ligne Pandas aplatie ou non)
    if isinstance(data, pd.Series):
        # Recherche directe par suffixe dans les noms de colonnes
        for col in data.index:
            col_str = str(col).lower()
            if col_str == target_key_lower or any(col_str.endswith(f"{sep}{target_key_lower}") for sep in [".", "/", "-", "_"]):
                val = data[col]
                # Si la valeur est elle-même un dict (OData object), on extrait 'filename'
                if isinstance(val, dict) and "filename" in val:
                    return val["filename"]
                return val
        # Si non trouvé dans l'index direct, on cherche récursivement dans les valeurs qui sont des dicts
        for val in data.values:
            if isinstance(val, dict):
                res = get_nested_val(val, target_key)
                if res: return res
        return None

    # Cas 2: Si data est un dictionnaire
    if isinstance(data, dict):
        # Recherche directe
        if target_key in data: return data[target_key]
        for k, v in data.items():
            if k.lower() == target_key_lower: return v
            # Recherche récursive
            res = get_nested_val(v, target_key)
            if res: return res
    return None

# Mapping simple pour le filtrage
def find_col(df, target_name):
    target_name_lower = target_name.lower()
    for col in df.columns:
        col_str = str(col).lower()
        if col_str == target_name_lower or any(col_str.endswith(f"{sep}{target_name_lower}") for sep in [".", "/", "-", "_"]):
            return col
    return None

# Mapping automatique des colonnes vitales
col_total = find_col(df, "total")
col_nom = find_col(df, "nom_etablissement")
if not col_nom: col_nom = find_col(df, "nom_pharmacie") # Alternative possible

# Mapper les rubriques
rubrique_cols = {}
for r_code in SCORE_COLUMNS:
    found = find_col(df, r_code)
    if found:
        rubrique_cols[r_code] = found

if not col_total or not col_nom:
    st.error(f"❌ Erreurs de structure : Colonne 'total' ou 'nom_etablissement' non trouvée.")
    st.write("Colonnes détectées :", df.columns.tolist())
    st.info("💡 Si vous testez sans connexion réelle, passez en **Mode démo** dans la barre latérale.")
    st.stop()

# Nettoyage des scores
all_scores_to_clean = list(rubrique_cols.values()) + [col_total]
for col in all_scores_to_clean:
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

# Créer des colonnes standardisées pour l'app
df["total"] = df[col_total]
df["nom_etablissement"] = df[col_nom]

# MAPPING GLOBAL DES LABELS (Remplacement des codes par les labels humains)
if mapping_noms:
    col_prov = find_col(df, "province_etablissement") or find_col(df, "province")
    if col_prov:
        df[col_prov] = df[col_prov].apply(lambda x: mapping_noms.get(str(x), str(x).replace("_", " ").title()) if pd.notna(x) else x)

    col_z = find_col(df, "ville_etablissement") or find_col(df, "zone_sante") or find_col(df, "zone")
    if col_z:
        df[col_z] = df[col_z].apply(lambda x: mapping_noms.get(str(x), str(x).replace("_", " ").title()) if pd.notna(x) else x)
        
    df["nom_etablissement"] = df["nom_etablissement"].apply(lambda x: mapping_noms.get(str(x), str(x).replace("_", " ").title()) if pd.notna(x) else x)

# Instance ID détection robuste
# ODK Central REST API utilise l'ID de soumission (souvent stocké dans __id ou __system.submissionId en OData)
col_id = (
    find_col(df, "__id") or 
    find_col(df, "instanceID") or 
    find_col(df, "__system.submissionId") or
    find_col(df, "meta.instanceID")
)
if col_id:
    df["_instance_id"] = df[col_id]
else:
    df["_instance_id"] = df.index.astype(str)

# ── Classification BPSD & Décisions Expert ──
# D'abord on récupère toutes les décisions de la base locale
from database import get_all_decisions
all_decisions = get_all_decisions()
expert_override_map = {}
if all_decisions:
    expert_override_map = {str(d["instance_id"]): d.get("statut_expert", d.get("decision", "")) for d in all_decisions}

def get_final_bpsd(row):
    inst_id = str(row["_instance_id"])
    expert_statut = expert_override_map.get(inst_id)
    
    # 1. Si l'expert a statué, on force ce statut
    if expert_statut:
        for niv, data in NIVEAUX_BPSD.items():
            if data["label"] == expert_statut:
                return {"niveau": niv, **data}
    
    # 2. Sinon, on utilise l'algorithme brut
    return classify_bpsd(row["total"])

bpsd_results = df.apply(get_final_bpsd, axis=1)

df["_niveau"] = bpsd_results.apply(lambda x: x["niveau"])
df["_cat_label"] = bpsd_results.apply(lambda x: x["label"])
df["_cat_emoji"] = bpsd_results.apply(lambda x: x["emoji"])
df["_cat_color"] = bpsd_results.apply(lambda x: x["color"])


def format_etablissement_name(nom):
    nom_str = str(nom)
    if nom_str in mapping_noms:
        return mapping_noms[nom_str]
    return nom_str.replace("_", " ").title()

# ══════════════════════════════════════════════════════════════════════════════
# FILTRES AVANCÉS (SIDEBAR)
# ══════════════════════════════════════════════════════════════════════════════
st.sidebar.markdown("### 🎛️ Filtres Avancés")

filtered_df = df.copy()

if not df.empty:
    # 1. Filtre Province
    col_province = find_col(df, "province_etablissement") or find_col(df, "province")
    if col_province:
        provinces = ["Toutes"] + sorted([str(p) for p in df[col_province].dropna().unique()])
        sel_prov = st.sidebar.selectbox("📍 Province", provinces)
        if sel_prov != "Toutes":
            filtered_df = filtered_df[filtered_df[col_province] == sel_prov]
            
    # 2. Filtre Zone de Santé
    col_zone = find_col(df, "ville_etablissement") or find_col(df, "zone_sante") or find_col(df, "zone") 
    if col_zone:
        zones = ["Toutes"] + sorted([str(z) for z in filtered_df[col_zone].dropna().unique()])
        sel_zone = st.sidebar.selectbox("🏥 Zone de Santé", zones)
        if sel_zone != "Toutes":
            filtered_df = filtered_df[filtered_df[col_zone] == sel_zone]
            
    # 3. Filtre Niveau BPSD
    niveaux = ["Tous", "A", "B", "C", "D"]
    sel_niv = st.sidebar.selectbox("📊 Niveau BPSD", niveaux)
    if sel_niv != "Tous":
        filtered_df = filtered_df[filtered_df["_niveau"] == sel_niv]
        
    # 4. Filtre Période
    col_date = find_col(df, "start") or find_col(df, "today") or find_col(df, "date")
    if col_date:
        filtered_df["_parsed_date"] = pd.to_datetime(filtered_df[col_date], errors="coerce")
        min_date = filtered_df["_parsed_date"].min()
        max_date = filtered_df["_parsed_date"].max()
        if pd.notna(min_date) and pd.notna(max_date):
            date_range = st.sidebar.date_input(
                "📅 Période",
                value=(min_date.date(), max_date.date()),
                min_value=min_date.date(),
                max_value=max_date.date()
            )
            if len(date_range) == 2:
                filtered_df = filtered_df[
                    (filtered_df["_parsed_date"].dt.date >= date_range[0]) & 
                    (filtered_df["_parsed_date"].dt.date <= date_range[1])
                ]

# ══════════════════════════════════════════════════════════════════════════════
# GESTION DE LA VUE (ROUTING)
# ══════════════════════════════════════════════════════════════════════════════

if page == "📊 Statistiques Générales":
    # ══════════════════════════════════════════════════════════════════════════════
    # PAGE 1 : STATISTIQUES GLOBALES
    # ══════════════════════════════════════════════════════════════════════════════
    st.markdown("## 📊 Statistiques Macro-Évaluation EPVG")
    
    nb_total = len(filtered_df)
    moyenne = round(float(filtered_df["total"].mean()), 1) if nb_total else 0.0
    niv_a_pct = round(float(len(filtered_df[filtered_df["_niveau"] == "A"]) / nb_total * 100), 1) if nb_total else 0.0
    niv_b_pct = round(float(len(filtered_df[filtered_df["_niveau"] == "B"]) / nb_total * 100), 1) if nb_total else 0.0
    niv_c_pct = round(float(len(filtered_df[filtered_df["_niveau"] == "C"]) / nb_total * 100), 1) if nb_total else 0.0
    niv_d_pct = round(float(len(filtered_df[filtered_df["_niveau"] == "D"]) / nb_total * 100), 1) if nb_total else 0.0
    niv_a_n = len(filtered_df[filtered_df["_niveau"] == "A"])
    niv_b_n = len(filtered_df[filtered_df["_niveau"] == "B"])
    niv_c_n = len(filtered_df[filtered_df["_niveau"] == "C"])
    niv_d_n = len(filtered_df[filtered_df["_niveau"] == "D"])
    
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    
    with k1:
        st.markdown(f"""
        <div class="kpi-card" style="border-color: #576CBC;">
            <div class="kpi-value" style="color: #19376D;">{nb_total}</div>
            <div class="kpi-label">Établissements évalués</div>
        </div>
        """, unsafe_allow_html=True)
    
    with k2:
        avg_color = classify_bpsd(moyenne)["color"]
        st.markdown(f"""
        <div class="kpi-card" style="border-color: {avg_color};">
            <div class="kpi-value" style="color: {avg_color};">{moyenne}%</div>
            <div class="kpi-label">Moyenne générale</div>
        </div>
        """, unsafe_allow_html=True)
    
    with k3:
        st.markdown(f"""
        <div class="kpi-card" style="border-color: #27AE60;">
            <div class="kpi-value" style="color: #27AE60;">🟢 {niv_a_n}</div>
            <div class="kpi-label">Niveau A (≥80%)</div>
        </div>
        """, unsafe_allow_html=True)
    
    with k4:
        st.markdown(f"""
        <div class="kpi-card" style="border-color: #3498DB;">
            <div class="kpi-value" style="color: #3498DB;">🔵 {niv_b_n}</div>
            <div class="kpi-label">Niveau B (60-79%)</div>
        </div>
        """, unsafe_allow_html=True)
    
    with k5:
        st.markdown(f"""
        <div class="kpi-card" style="border-color: #F39C12;">
            <div class="kpi-value" style="color: #F39C12;">🟠 {niv_c_n}</div>
            <div class="kpi-label">Niveau C (51-59%)</div>
        </div>
        """, unsafe_allow_html=True)
    
    with k6:
        st.markdown(f"""
        <div class="kpi-card" style="border-color: #E74C3C;">
            <div class="kpi-value" style="color: #E74C3C;">🔴 {niv_d_n}</div>
            <div class="kpi-label">Niveau D (≤50%)</div>
        </div>
        """, unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════════
    # ANALYTIQUE : CARTOGRAPHIE DES LACUNES ET TENDANCES
    # ══════════════════════════════════════════════════════════════════════════════
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.markdown("### 📈 Analyses Avancées")
    
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.markdown("**Cartographie des Lacunes (Moyennes par Rubrique)**")
        # Ensure col_zone exists or attempt fallback
        local_col_zone = find_col(df, "ville_etablissement") or find_col(df, "zone_sante") or find_col(df, "zone")
        if not filtered_df.empty and local_col_zone and local_col_zone in filtered_df.columns:
            zones_uniques = sorted(filtered_df[local_col_zone].dropna().unique())
            heatmap_z = []
            heatmap_y = []
            heatmap_x = [label[:15]+"..." for label in RUBRIQUE_LABELS.values()]
            
            for z in zones_uniques:
                df_z = filtered_df[filtered_df[local_col_zone] == z]
                z_scores = []
                for r_code in RUBRIQUE_LABELS.keys():
                    if r_code in rubrique_cols and rubrique_cols[r_code] in df_z.columns:
                        z_scores.append(df_z[rubrique_cols[r_code]].mean())
                    else:
                        z_scores.append(0)
                heatmap_z.append(z_scores)
                heatmap_y.append(str(z))
                
            fig_hm = go.Figure(data=go.Heatmap(
                z=heatmap_z,
                x=heatmap_x,
                y=heatmap_y,
                colorscale='RdYlGn',
                zmin=0, zmax=100,
                hovertemplate="Zone: %{y}<br>Rubrique: %{x}<br>Score Moyen: %{z:.1f}%<extra></extra>"
            ))
            fig_hm.update_layout(height=400, margin=dict(l=0, r=0, t=30, b=0), font={"family":"Inter, sans-serif"})
            st.plotly_chart(fig_hm, use_container_width=True)
        else:
            st.info("Données insuffisantes pour la heatmap (colonne zone de santé absente).")
            
    with col_chart2:
        st.markdown("**Évolution Globale des Évaluations**")
        if not filtered_df.empty and "_parsed_date" in filtered_df.columns:
            df_trend = filtered_df.dropna(subset=["_parsed_date"]).copy()
            if not df_trend.empty:
                df_trend["mois_annee"] = df_trend["_parsed_date"].dt.to_period("M").astype(str)
                trend_data = df_trend.groupby("mois_annee")["total"].mean().reset_index()
                trend_data = trend_data.sort_values("mois_annee")
                
                fig_trend = go.Figure()
                fig_trend.add_trace(go.Scatter(
                    x=trend_data["mois_annee"], 
                    y=trend_data["total"],
                    mode='lines+markers',
                    line=dict(color='#27AE60', width=3),
                    marker=dict(size=8, color='#19376D')
                ))
                fig_trend.update_layout(
                    height=400, 
                    xaxis_title="Période (Mois)",
                    yaxis_title="Score Global Moyen (%)",
                    yaxis=dict(range=[0, 100]),
                    margin=dict(l=0, r=0, t=30, b=0),
                    font={"family":"Inter, sans-serif"}
                )
                st.plotly_chart(fig_trend, use_container_width=True)
            else:
                st.info("Aucune date valide trouvée.")
        else:
            st.info("Données temporelles insuffisantes pour l'analyse d'évolution.")

    # ══════════════════════════════════════════════════════════════════════════════
    # CARTOGRAPHIE DES ÉTABLISSEMENTS
    # ══════════════════════════════════════════════════════════════════════════════
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.markdown("### 🗺️ Cartographie des Établissements")
    
    # ── Extraction robuste des coordonnées GPS ────────────────────────────
    # ODK Central peut fournir les coordonnées de plusieurs manières :
    # 1. OData GeoJSON : colonnes "GEO_LOCALISATION.coordinates" (array [lon,lat,alt])
    # 2. Texte brut    : colonne "GEO_LOCALISATION" avec "lat lon alt acc"
    # 3. Colonnes séparées : "latitude" et "longitude" 
    lat_col = None
    lon_col = None
    
    # --- Méthode 1 : Colonnes lat/lon directes ---
    _lat = find_col(df, "latitude") or find_col(df, "lat")
    _lon = find_col(df, "longitude") or find_col(df, "lon") or find_col(df, "lng")
    if _lat and _lon:
        lat_col, lon_col = _lat, _lon
    
    # --- Méthode 2 : OData GeoJSON (GEO_LOCALISATION.coordinates) ---
    if not lat_col or not lon_col:
        # Chercher directement dans les colonnes du DataFrame
        coord_col = None
        for c in df.columns:
            if str(c).lower().endswith('.coordinates') and 'geo' in str(c).lower():
                coord_col = c
                break
        
        if coord_col:
            def parse_geojson_lat(val):
                try:
                    if isinstance(val, list) and len(val) >= 2:
                        return float(val[1])  # GeoJSON = [lon, lat, alt]
                    if isinstance(val, str):
                        import json
                        arr = json.loads(val)
                        if isinstance(arr, list) and len(arr) >= 2:
                            return float(arr[1])
                except: pass
                return None
            def parse_geojson_lon(val):
                try:
                    if isinstance(val, list) and len(val) >= 2:
                        return float(val[0])
                    if isinstance(val, str):
                        import json
                        arr = json.loads(val)
                        if isinstance(arr, list) and len(arr) >= 2:
                            return float(arr[0])
                except: pass
                return None
                
            filtered_df["_lat"] = filtered_df[coord_col].apply(parse_geojson_lat)
            filtered_df["_lon"] = filtered_df[coord_col].apply(parse_geojson_lon)
            lat_col, lon_col = "_lat", "_lon"

    # --- Méthode 3 : Texte brut geopoint ("lat lon alt acc") ---
    if not lat_col or not lon_col:
        geo_text_col = None
        for c in df.columns:
            cl = str(c).lower()
            if ('geo' in cl and 'coord' not in cl and 'type' not in cl) or cl == 'geopoint':
                geo_text_col = c
                break
        
        if geo_text_col:
            def extract_lat_text(val):
                if pd.isna(val): return None
                s = str(val).strip()
                parts = s.split()
                if len(parts) >= 2:
                    try: return float(parts[0])
                    except: pass
                return None
            def extract_lon_text(val):
                if pd.isna(val): return None
                s = str(val).strip()
                parts = s.split()
                if len(parts) >= 2:
                    try: return float(parts[1])
                    except: pass
                return None
            
            filtered_df["_lat"] = filtered_df[geo_text_col].apply(extract_lat_text)
            filtered_df["_lon"] = filtered_df[geo_text_col].apply(extract_lon_text)
            lat_col, lon_col = "_lat", "_lon"

    if lat_col and lon_col:
        # Check if the coordinates are properly formatted to float
        filtered_df[lat_col] = pd.to_numeric(filtered_df[lat_col], errors="coerce")
        filtered_df[lon_col] = pd.to_numeric(filtered_df[lon_col], errors="coerce")
        df_map = filtered_df.dropna(subset=[lat_col, lon_col])
        
        if not df_map.empty:
            center_lat = float(df_map[lat_col].mean())
            center_lon = float(df_map[lon_col].mean())
            
            m = folium.Map(location=[center_lat, center_lon], zoom_start=11, tiles="cartodb positron")
            
            for idx, row in df_map.iterrows():
                niv = row.get("_niveau", "D")
                color = {"A": "green", "B": "blue", "C": "orange", "D": "red"}.get(niv, "red")
                
                nom = str(row.get("nom_etablissement", "Inconnu"))
                nom_affiche = format_etablissement_name(nom)
                score = row.get("total", 0)
                label_cat = row.get("_cat_label", "")
                
                popup_html = f"""
                <div style="font-family: Arial, sans-serif; min-width: 200px;">
                    <h4 style="margin:0 0 5px 0; color:#19376D; font-size: 14px;">{nom_affiche}</h4>
                    <p style="margin:0; font-size: 13px;"><b>Score:</b> {score}%</p>
                    <p style="margin:0; font-size: 13px;"><b>Statut:</b> {label_cat}</p>
                </div>
                """
                
                folium.Marker(
                    location=[float(row[lat_col]), float(row[lon_col])],
                    popup=folium.Popup(popup_html, max_width=300),
                    tooltip=nom_affiche,
                    icon=folium.Icon(color=color, icon="plus", prefix="fa")
                ).add_to(m)
                
            st_folium(m, use_container_width=True, height=450, returned_objects=[])
        else:
            st.info("📌 Aucune coordonnée GPS valide trouvée pour ces établissements.")
    else:
        st.info("📌 Les données actuelles ne contiennent pas de coordonnées géographiques (latitude/longitude).")

    # Export
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.markdown("### 📥 Export & Hub de Données")

    export_col1, export_col2 = st.columns([2, 1])

    with export_col1:
        st.markdown("""
        Exportez un fichier Excel consolidé fusionnant les **scores ODK** et les **décisions expert**.
        Le rapport inclut toutes les rubriques, catégories et commentaires d'expert.
        """)
        
    with export_col2:
        if st.button("📥 Exporter le rapport final", use_container_width=True, type="primary"):
            # ── Colonnes d'identification ──
            id_cols = ["_instance_id", "nom_etablissement"]
            
            # ── Colonnes de scores par rubrique (sous-totaux) ──
            real_score_cols = [rubrique_cols[r] for r in SCORE_COLUMNS if r in rubrique_cols]
            
            # ── Total + Niveau BPSD ──
            result_cols = ["total", "_cat_label"]
            
            # Construire le DataFrame d'export avec uniquement ces colonnes
            selected_cols = id_cols + real_score_cols + result_cols
            export_df = filtered_df[[c for c in selected_cols if c in filtered_df.columns]].copy()

            # Formater le nom d'établissement
            export_df["nom_etablissement"] = export_df["nom_etablissement"].apply(format_etablissement_name)

            # Renommer toutes les colonnes pour lisibilité
            rename_map = {
                "_instance_id": "Instance ID",
                "nom_etablissement": "Établissement",
                "total": "Score Total (%)",
                "_cat_label": "Niveau BPSD",
            }
            # Renommer les rubriques avec leurs labels explicites
            for r_code, col_name in rubrique_cols.items():
                label = RUBRIQUE_LABELS.get(r_code)
                if label and col_name in export_df.columns:
                    rename_map[col_name] = label

            export_df.rename(columns=rename_map, inplace=True)

            # Fusionner les décisions du jury
            all_decisions = get_all_decisions()
            if all_decisions:
                dec_df = pd.DataFrame(all_decisions)
                
                if "statut_expert" not in dec_df.columns:
                    dec_df["statut_expert"] = dec_df.get("decision", "")
                if "notes_expert" not in dec_df.columns:
                    dec_df["notes_expert"] = dec_df.get("commentaire", "")

                dec_df.rename(columns={
                    "instance_id": "Instance ID",
                    "statut_expert": "Décision du Jury",
                    "notes_expert": "Observations Expert",
                    "date_decision": "Date Validation",
                }, inplace=True)
                
                cols_to_merge = ["Instance ID", "Décision du Jury", "Observations Expert", "Date Validation"]
                dec_df = dec_df[[c for c in cols_to_merge if c in dec_df.columns]]
                export_df = export_df.merge(dec_df, on="Instance ID", how="left")

            # Générer le fichier Excel
            try:
                import openpyxl
                output = BytesIO()
                with pd.ExcelWriter(output, engine="openpyxl") as writer:
                    export_df.to_excel(writer, index=False, sheet_name="Résultats EPVG")

                    # Auto-ajuster les colonnes
                    worksheet = writer.sheets["Résultats EPVG"]
                    for column in worksheet.columns:
                        max_length = 0
                        col_letter = column[0].column_letter
                        for cell in column:
                            try:
                                if cell.value and len(str(cell.value)) > max_length:
                                    max_length = len(str(cell.value))
                            except (TypeError, ValueError):
                                pass
                        adjusted_width = min(int(max_length) + 2, 40)
                        worksheet.column_dimensions[col_letter].width = adjusted_width

                output.seek(0)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M")
                st.download_button(
                    label="⬇️ Télécharger le fichier Excel",
                    data=output.getvalue(),
                    file_name=f"Rapport_EPVG_{timestamp}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"❌ Erreur lors de la génération de l'export Excel : {e}")

elif page == "🏥 Évaluation Détaillée":
    # ══════════════════════════════════════════════════════════════════════════════
    # PAGE 2 : VUE DÉTAILLÉE (ÉVALUATION)
    # ══════════════════════════════════════════════════════════════════════════════
    noms = sorted(df["nom_etablissement"].dropna().unique().tolist())

    # ── En-tête avec sélection sur la droite ──────────────────────────────────
    h_col1, h_col2 = st.columns([2, 1])
    
    with h_col2:
        selected_name = st.selectbox(
            "📍 Choisir un établissement", 
            noms, 
            index=0, 
            format_func=format_etablissement_name,
            label_visibility="collapsed"
        )
    
    # Calcul des données pour la ligne sélectionnée
    row = df[df["nom_etablissement"] == selected_name].iloc[0]
    instance_id = row["_instance_id"]
    score_total = row["total"]
    cat_info = classify_bpsd(score_total)

    with h_col1:
        st.markdown(f"## 🏥 {format_etablissement_name(selected_name)}")

    # --- Outils Diagnostic (déplacés dans Détails) ---
    if mode == "🌐 ODK Central":
        with st.expander("🛠️ Outils de Diagnostic & Expert Mode"):
            d_col1, d_col2 = st.columns(2)
            with d_col1:
                st.markdown("**Inspecteur JSON**")
                st.json(row.to_dict())
            with d_col2:
                st.markdown("**Vérification API ODK**")
                if not odk_client:
                    st.warning("⚠️ ODK Client non connecté. Connectez-vous dans le panneau latéral.")
                elif st.button("🔍 Tester l'accès aux photos", key="debug_odk_btn", use_container_width=True):
                    try:
                        import urllib.parse
                        api_id_encoded = urllib.parse.quote(str(instance_id))
                        url_base = f"{odk_client.server_url}/v1/projects/{odk_client.project_id}/forms/{odk_client.form_id}"
                        url_list = f"{url_base}/submissions/{api_id_encoded}/attachments"
                        r = odk_client.session.get(url_list, timeout=10)
                        if r.status_code == 200:
                            att_list = r.json()
                            st.success(f"✅ {len(att_list)} pièces jointes sur le serveur.")
                            names_in_server = [a['name'] for a in att_list]
                            comp_data = []
                            for f_key, f_label in PHOTO_FIELDS.items():
                                val = get_nested_val(row, f_key)
                                if val:
                                    status = "✅ Présent" if val in names_in_server else "❌ Absent"
                                    comp_data.append({"Photo": f_label, "Fichier": val, "État": status})
                            if comp_data: st.table(pd.DataFrame(comp_data))
                        else:
                            st.error(f"Erreur API {r.status_code}")
                    except Exception as e:
                        st.error(f"Erreur : {e}")

    # En-tête de la fiche (Score Card)
    st.markdown(f"""
    <div class="score-card" style="border-top: 5px solid {cat_info['color']}; background: {cat_info['bg']};">
        <div class="score-value" style="color: {cat_info['color']};">{score_total}%</div>
        <div class="score-label">{cat_info['emoji']} {cat_info['label']}</div>
        <div style="font-size: 0.8rem; color: #475569; margin-top: 0.8rem; max-width: 700px; margin-left: auto; margin-right: auto; line-height: 1.5;">{cat_info['description']}</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 📊 Performance & Comparatif (Radar)")
    rubriques = []
    scores = []
    colors = []
    avg_scores = []
    
    for r_code, label in RUBRIQUE_LABELS.items():
        if r_code in rubrique_cols:
            col_name = rubrique_cols[r_code]
            if col_name in row and pd.notna(row[col_name]):
                score = float(row[col_name])
                # Raccourcir le label pour l'affichage
                short_label = label[:25] + "..." if len(label) > 25 else label
                rubriques.append(short_label)
                scores.append(score)
                colors.append(classify_bpsd(score)["color"])
                
                # Moyenne globale depuis filtered_df
                if col_name in filtered_df.columns:
                    avg_scores.append(float(filtered_df[col_name].mean()))
                else:
                    avg_scores.append(0.0)
    
    col_bar, col_radar = st.columns(2)
    
    with col_bar:
        fig_bar = go.Figure(go.Bar(
            x=rubriques,
            y=scores,
            orientation='v',
            marker_color=colors,
            text=[f"{s}%" for s in scores],
            textposition='auto',
        ))
        
        fig_bar.update_layout(
            xaxis=dict(title_text="Rubriques"),
            yaxis=dict(range=[0, 100], title_text="Score (%)"),
            height=450,
            margin=dict(l=0, r=0, t=30, b=0),
            plot_bgcolor="white",
            font={"family": "Inter, sans-serif"}
        )
        fig_bar.add_hline(y=50, line_dash="dash", line_color="#E74C3C", annotation_text="Seuil D", annotation_position="top right", annotation={"font_color": "#E74C3C"})
        fig_bar.add_hline(y=60, line_dash="dash", line_color="#3498DB", annotation_text="Seuil B", annotation_position="top left", annotation={"font_color": "#3498DB"})
        fig_bar.add_hline(y=80, line_dash="dash", line_color="#27AE60", annotation_text="Seuil A", annotation_position="top left", annotation={"font_color": "#27AE60"})
        
        st.plotly_chart(fig_bar, use_container_width=True)
        
    with col_radar:
        fig_radar = go.Figure()
        
        # Fermeture du polygone
        r_scores = scores + [scores[0]] if len(scores)>0 else []
        r_avg = avg_scores + [avg_scores[0]] if len(avg_scores)>0 else []
        r_cats = rubriques + [rubriques[0]] if len(rubriques)>0 else []
        
        fig_radar.add_trace(go.Scatterpolar(
            r=r_avg,
            theta=r_cats,
            fill='toself',
            name='Moyenne Globale',
            line_color='rgba(100, 116, 139, 0.5)',
            fillcolor='rgba(100, 116, 139, 0.2)'
        ))
        
        nom_affiche = format_etablissement_name(selected_name)
        fig_radar.add_trace(go.Scatterpolar(
            r=r_scores,
            theta=r_cats,
            fill='toself',
            name=nom_affiche[:15] + "...",
            line_color=cat_info['color'],
            fillcolor=cat_info['bg']
        ))
        
        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 100])
            ),
            showlegend=True,
            legend=dict(orientation="h", y=-0.2),
            height=400,
            margin=dict(l=40, r=40, t=30, b=0),
            font={"family": "Inter, sans-serif"}
        )
        st.plotly_chart(fig_radar, use_container_width=True)


    # Décision existante
    existing = get_decision(instance_id)
    if existing:
        dec_color = {"Retenu": "#27AE60", "À délibérer": "#F39C12", "Non viable": "#E74C3C"}.get(existing["decision"], "#64748b")
        st.markdown(f"""
        <div style="margin-top:1rem; padding:0.8rem 1rem; border-radius:10px; background:white; border:1px solid #e2e8f0;">
            <div style="font-size:0.75rem; color:#64748b; text-transform:uppercase; letter-spacing:0.5px; font-weight:600;">Décision expert</div>
            <div style="font-size:1.1rem; font-weight:700; color:{dec_color}; margin-top:0.2rem;">{existing['decision']}</div>
            <div style="font-size:0.8rem; color:#475569; margin-top:0.3rem;">{existing.get('commentaire', '')}</div>
        </div>
        """, unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════════
    # GÉNÉRATEUR DE RAPPORTS (CAPA PDF)
    # ══════════════════════════════════════════════════════════════════════════════
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.markdown("### 📄 Rapport Officiel CAPA (Plan d'Actions Correctives)")
    
    failed_rubriques = []
    for r_code, label in RUBRIQUE_LABELS.items():
        if r_code in rubrique_cols:
            col_name = rubrique_cols[r_code]
            if col_name in row and pd.notna(row[col_name]):
                score = float(row[col_name])
                if score < 60:
                    failed_rubriques.append({"label": label, "score": score})
                    
    if failed_rubriques:
        st.warning(f"⚠️ {len(failed_rubriques)} rubriques nécessitent un plan d'actions correctives (score < 60%).")
    else:
        st.success("✅ Aucune rubrique critique n'est en échec.")
        
    try:
        from pdf_generator import generate_capa_pdf
        pdf_bytes = generate_capa_pdf(
            etablissement=nom_affiche,
            score_total=score_total,
            niveau=cat_info['niveau'],
            failed_rubriques=failed_rubriques
        )
        st.download_button(
            label="⬇️ Générer et Télécharger le Plan d'Actions (PDF)",
            data=bytes(pdf_bytes),
            file_name=f"CAPA_{nom_affiche.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf",
            mime="application/pdf",
            use_container_width=True,
            type="primary"
        )
    except Exception as e:
        st.error(f"❌ Erreur lors de la génération du PDF : {e}")

    # ══════════════════════════════════════════════════════════════════════════════
    # GALERIE DE PHOTOS
    # ══════════════════════════════════════════════════════════════════════════════
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.markdown("### 📸 Galerie de preuves photographiques")
    
    # --- Debug zone pour les photos ---
    with st.expander("🔍 Diagnostic de la Galerie (Mapping OData)"):
        st.info("💡 L'application cherche maintenant les 19 champs de photos identifiés dans votre XLSForm.")
        
        api_instance_id = instance_id
        st.markdown(f"**ID de soumission utilisé (REST API) :** `{api_instance_id}`")
        
        mapping_debug = []
        for field, label in PHOTO_FIELDS.items():
            val = get_nested_val(row, field)
            status = "✅ Trouvé" if val else "❌ Vide"
            
            # Simuler l'URL pour dépanage
            debug_url = "-"
            if val and odk_client:
                safe_fname = str(val).strip()
                debug_url = f"{odk_client.server_url}/v1/projects/{odk_client.project_id}/forms/{odk_client.form_id}/submissions/{api_instance_id}/attachments/{safe_fname}"
                
            mapping_debug.append({
                "Photo": label,
                "ID XLS": field,
                "État": status,
                "Fichier": str(val) if val else "-",
                "URL API": debug_url
            })
        st.table(pd.DataFrame(mapping_debug))
    
    photo_cols = st.columns(4) # Passage à 4 colonnes pour 19 photos
    for idx, (field, label) in enumerate(PHOTO_FIELDS.items()):
        col_idx = idx % 4
        with photo_cols[col_idx]:
            # Utiliser la recherche robuste récursive
            filename = get_nested_val(row, field)

            # --- Rendu de la carte photo ---
            image_html = ""
            if filename and str(filename).strip() and str(filename).lower() not in ["nan", "none", ""]:
                fname = str(filename).strip()
                image_loaded = False
                
                if mode == "🌐 ODK Central" and odk_client:
                    img_data, img_err = odk_client.get_attachment_image(instance_id, fname)
                    if img_data:
                        try:
                            from PIL import Image
                            import io
                            img = Image.open(io.BytesIO(img_data.getvalue()))
                            
                            # Crop 16:9
                            w, h = img.size
                            target = 16/9
                            if w/h > target:
                                nw = int(target * h)
                                off = (w - nw) // 2
                                img = img.crop((off, 0, off + nw, h))
                            else:
                                nh = int(w / target)
                                off = (h - nh) // 2
                                img = img.crop((0, off, w, off + nh))
                            
                            # Conversion en base64 pour affichage HTML unique
                            buffered = io.BytesIO()
                            img.save(buffered, format="JPEG")
                            img_str = base64.b64encode(buffered.getvalue()).decode()
                            image_html = f'<img src="data:image/jpeg;base64,{img_str}">'
                            image_loaded = True
                        except:
                            image_html = '<div class="photo-missing">⚠️ Erreur Image</div>'
                    else:
                        image_html = f'<div class="photo-missing">❌ {str(img_err)[:20]}</div>'
                
                if not image_loaded:
                    if mode != "🌐 ODK Central":
                        image_html = f'<div class="photo-missing">📄<br><span style="font-size:0.6rem;">{fname}</span></div>'
                    # Si mode ODK et erreur, image_html contient déjà le message d'erreur
            else:
                image_html = '<div class="photo-missing">📷 Non fournie</div>'

            # Affichage en un seul bloc markdown pour éviter les duplications DOM liées aux widgets Streamlit
            st.markdown(f"""
                <div class="photo-card">
                    {image_html}
                    <div class="photo-label">{label}</div>
                </div>
            """, unsafe_allow_html=True)



    # ══════════════════════════════════════════════════════════════════════════════
    # MODULE DE DÉCISION EXPERT
    # ══════════════════════════════════════════════════════════════════════════════
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.markdown("### ⚖️ Décision du Jury / Comité")
    
    # Charger la décision existante
    saved_decision = get_decision(str(instance_id))
    
    if saved_decision:
        st.success(f"✅ Évaluation validée le {saved_decision['date_decision']}")
        c1, c2 = st.columns([1, 2])
        c1.metric("Statut Final", saved_decision['statut_expert'])
        c2.markdown(f"**Observations :**<br>{saved_decision['notes_expert']}", unsafe_allow_html=True)
        
        if st.button("📝 Modifier l'évaluation", key=f"edit_btn_{instance_id}"):
            # Pour relancer le process, on va utiliser la session_state
            st.session_state[f"edit_{instance_id}"] = True
            st.rerun()
            
    # Formulaire de décision (s'il n'y en a pas OU si on est en mode édition)
    if not saved_decision or st.session_state.get(f"edit_{instance_id}", False):
        st.markdown('<div class="decision-section">', unsafe_allow_html=True)
        with st.form(key=f"form_decision_{instance_id}"):
            dec_options = ["Niveau A – Conformité élevée", "Niveau B – Conformité acceptable", "Niveau C – Conformité limitée", "Niveau D – Non conforme", "Mise en Demeure"]
            
            # Pré-sélection basées sur les anciennes données si existantes, sinon algo BPSD
            def_idx = 0
            if saved_decision and saved_decision['statut_expert'] in dec_options:
                def_idx = dec_options.index(saved_decision['statut_expert'])
            else:
                niveau = cat_info.get("niveau", "D")
                idx_map = {"A": 0, "B": 1, "C": 2, "D": 3}
                def_idx = idx_map.get(niveau, 3)
                
            statut_expert = st.selectbox(
                "Statut officiel retenu par le comité :",
                options=dec_options,
                index=def_idx
            )
            
            def_notes = saved_decision['notes_expert'] if saved_decision else f"Conforme à l'évaluation algorithmique ({score_total}%)."
            notes_expert = st.text_area("Observations & Justifications :", value=def_notes, height=100)
            
            submit_decision = st.form_submit_button("💾 Valider la décision officielle", use_container_width=True)
            
            if submit_decision:
                success = save_decision(
                    instance_id=str(instance_id),
                    nom_etablissement=str(selected_name),
                    score_algo=float(score_total),
                    statut_expert=str(statut_expert),
                    notes_expert=str(notes_expert)
                )
                if success:
                    st.session_state[f"edit_{instance_id}"] = False # Fermer le mode édition
                    st.success("✅ Décision enregistrée dans la base Excel/SQLite.")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("❌ Erreur lors de l'enregistrement.")
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# BOILERPLATE MÉTADONNÉES
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div style="text-align: center; margin-top: 50px; font-size: 0.8rem; color: #94a3b8;">
    Système d'Évaluation des Pharmacies (EPVG) • Version 2.1<br>
    Développé avec Streamlit & ODK Central
</div>
""", unsafe_allow_html=True)
# ══════════════════════════════════════════════════════════════════════════════
# TABLEAU RÉCAPITULATIF (en sidebar)
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("---")
    st.markdown("### 📋 Récapitulatif")

    # Mini tableau complet
    recap_df = df[["nom_etablissement", "total", "_niveau", "_cat_emoji"]].copy()
    recap_df["Niv."] = recap_df["_cat_emoji"] + " " + recap_df["_niveau"]
    recap_df = recap_df.drop(columns=["_niveau", "_cat_emoji"])
    recap_df.columns = ["Établissement", "Score", "Niv."]
    recap_df = recap_df.sort_values("Score", ascending=False)
    recap_df["Score"] = recap_df["Score"].apply(lambda x: f"{x:.0f}%")

    st.dataframe(recap_df, use_container_width=True, hide_index=True, height=350)

    # Stats décisions
    decisions = get_all_decisions()
    if decisions:
        st.markdown(f"**{len(decisions)}** décision(s) enregistrée(s)")
    else:
        st.caption("Aucune décision enregistrée")


# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
st.markdown("""
<div style="text-align:center; padding:1rem; color:#94a3b8; font-size:0.8rem;">
    Dashboard EPVG — Habilitation & Expertise • DIRCOP Kinshasa<br>
    Développé avec ❤️  en Python / Streamlit
</div>
""", unsafe_allow_html=True)
