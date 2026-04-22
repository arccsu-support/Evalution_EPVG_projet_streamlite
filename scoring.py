"""
Logique de scoring et constantes de configuration pour le dashboard EPVG.
"""
import pandas as pd

# ── Rubriques de scores ──────────────────────────────────────────────────────
SCORE_COLUMNS = [
    "a_pourcentage", "b_pourcentage", "c_pourcentage",
    "d_pourcentage", "e_pourcentage", "f_pourcentage",
    "g_pourcentage", "h_pourcentage", "i_pourcentage",
]

RUBRIQUE_LABELS = {
    "a_pourcentage": "1. Organisation de l'Établissement",
    "b_pourcentage": "2. Système Qualité",
    "c_pourcentage": "3. Personnel",
    "d_pourcentage": "4. Documentation",
    "e_pourcentage": "5. Bâtiments, Locaux et Appareillage",
    "f_pourcentage": "6. Livraison aux Clients et Transport",
    "g_pourcentage": "7. Retour aux Expéditeurs",
    "h_pourcentage": "8. Auto-inspection",
    "i_pourcentage": "9. Autres Points Spécifiques",
}

# ── Mapping photos → libellés ────────────────────────────────────────────────
PHOTO_FIELDS = {
    "aa2": "Autorisation d'Ouverture",
    "ea2": "Image Bâtiments",
    "ea9": "Image Plafond",
    "ea13": "Zone de Quarantaine",
    "ea15": "Zone de Rebuts",
    "img_quai": "Quai de Déchargement",
    "img_cantine": "Cantine / Cafétéria",
    "img_salle_admin": "Salle d'Administration",
    "img_vestiaires": "Vestiaires",
    "img_installation": "Installations Sanitaires",
    "ec7": "Locaux d'Entreposage",
    "ec11": "Étagères",
    "ec15": "Stockage Produits",
    "ec22": "Protection Locaux (Nuisibles)",
    "ed4": "Thermomètre Fonctionnel",
    "ed6": "Thermomètre Étalonné",
    "eg4": "Hygromètre Fonctionnel",
    "eg6": "Thermomètre (Suivi)",
    "eh5": "Entretien Extincteurs",
}

# ── Niveaux BPSD (ARC-CSU) ──────────────────────────────────────────────────
NIVEAUX_BPSD = {
    "A": {
        "label": "Niveau A – Conformité élevée",
        "color": "#27AE60",
        "emoji": "🟢",
        "bg": "rgba(39,174,96,0.12)",
        "seuil": "≥ 80 %",
        "description": (
            "Établissement opérant à un niveau élevé de conformité aux BPSD, "
            "conformément aux référentiels de l'OMS et de la RDC, avec un taux global ≥ 80 %. "
            "Le cas échéant, l'établissement peut également être titulaire d'une certification "
            "délivrée par un organisme internationalement reconnu (audit < 3 ans)."
        ),
    },
    "B": {
        "label": "Niveau B – Conformité acceptable",
        "color": "#3498DB",
        "emoji": "🔵",
        "bg": "rgba(52,152,219,0.12)",
        "seuil": "60 % – 79 %",
        "description": (
            "Établissement opérant à un niveau acceptable de conformité aux BPSD, "
            "avec un taux global compris entre 60 % et 79 %. "
            "Des écarts mineurs ou majeurs peuvent être relevés, nécessitant un plan "
            "d'actions correctives (CAPA) dans un délai défini et raisonnable."
        ),
    },
    "C": {
        "label": "Niveau C – Conformité limitée",
        "color": "#F39C12",
        "emoji": "🟠",
        "bg": "rgba(243,156,18,0.12)",
        "seuil": "51 % – 59 %",
        "description": (
            "Établissement présentant un niveau de conformité limité aux BPSD, "
            "avec un taux global compris entre 51 % et 59 %. "
            "Des écarts significatifs majeurs et critiques peuvent impacter la qualité, "
            "la sécurité ou la traçabilité des produits. "
            "La poursuite de l'activité CSU est conditionnée à un plan de redressement."
        ),
    },
    "D": {
        "label": "Niveau D – Non conforme",
        "color": "#E74C3C",
        "emoji": "🔴",
        "bg": "rgba(231,76,60,0.12)",
        "seuil": "≤ 50 %",
        "description": (
            "Établissement opérant à un niveau inacceptable de conformité aux BPSD, "
            "avec un taux de conformité global ≤ 50 %. "
            "Les écarts observés sont critiques et susceptibles de compromettre la qualité, "
            "la sécurité ou l'intégrité des produits de santé. "
            "Des mesures administratives appropriées peuvent être envisagées."
        ),
    },
}

# Garde l'ancien nom CATEGORIES comme alias pour compatibilité
CATEGORIES = NIVEAUX_BPSD

DECISION_OPTIONS = ["Niveau A", "Niveau B", "Niveau C", "Niveau D"]


def classify_bpsd(score) -> dict:
    """
    Retourne un dict avec le niveau BPSD, le label, la couleur, l'emoji
    et la description en fonction du score total (0-100).
    Le score est arrondi à l'entier pour gérer strictement les seuils.
    """
    if pd.isna(score):
        score = 0
        
    score_int = round(float(score))
    
    if score_int >= 80:
        niveau = "A"
    elif score_int >= 60:
        niveau = "B"
    elif score_int >= 51:
        niveau = "C"
    else:
        niveau = "D"
    return {"niveau": niveau, **NIVEAUX_BPSD[niveau]}


# Alias pour compatibilité avec l'ancien code
def categorize(score: float) -> dict:
    """Alias de classify_bpsd pour compatibilité descendante."""
    result = classify_bpsd(score)
    # Mapper 'niveau' vers 'category' pour compatibilité
    result["category"] = result["niveau"]
    return result
