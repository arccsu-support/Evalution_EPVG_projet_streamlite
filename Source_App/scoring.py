"""
Logique de scoring et constantes de configuration pour le dashboard EPVG.
Dashboard Habilitation EPVG — Formulaire_Habilitation EPVG
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

# ── Colonnes de sévérité par rubrique (calculate dans le XLSForm) ────────────
# Chaque rubrique produit des compteurs de non-conformités par niveau de sévérité
SEVERITY_COLUMNS_BY_RUBRIQUE = {
    "a": {"critique": "a_critique", "majeur": "a_majeur"},
    "b": {"majeur": "b_majeur"},
    "c": {"critique": "c_critique", "majeur": "c_majeur", "mineur": "c_mineur"},
    "d": {"critique": "d_critique", "majeur": "d_majeur", "mineur": "d_mineur", "remarque": "d_remarque"},
    "e": {"critique": "e_critique", "majeur": "e_majeur", "mineur": "e_mineur"},
    "f": {"critique": "f_critique", "majeur": "f_majeur", "mineur": "f_mineur"},
    "g": {"majeur": "g_majeur", "mineur": "g_mineur"},
    "h": {"majeur": "h_majeur"},
    "i": {"majeur": "i_majeur"},
}

# ── Dénominateurs pour les taux de non-conformité (max théorique par sévérité) ─
SEVERITY_DENOMINATORS = {
    "total_critique": 15,   # 15 questions critiques au total
    "total_majeur": 126,    # 126 questions majeures au total
    "total_mineur": 24,     # 24 questions mineures au total
    "total_remarque": 3,    # 3 questions remarques au total
}

# ── Metadata des questions : nom → sévérité ──────────────────────────────────
# Permet d'identifier le niveau de sévérité de chaque question individuelle
# Extrait du XLSForm (onglet survey, colonne type)
QUESTION_SEVERITY_MAP = {
    # Rubrique A — Organisation
    "aa1": "critique", "aa3": "majeur",
    # Rubrique B — Système Qualité
    "b1": "majeur", "b2": "majeur", "b3": "majeur", "b4": "majeur", "b5": "majeur",
    # Rubrique C — Personnel
    "ca1": "critique", "ca2": "majeur", "ca3": "majeur", "ca4": "majeur", "ca5": "majeur",
    "cb1": "critique", "cb2": "majeur", "cb3": "majeur", "cb4": "majeur", "cb5": "majeur",
    "cc1": "majeur", "cc2": "majeur", "cc3": "majeur", "cc4": "majeur",
    "cd1": "mineur",
    "ce1": "majeur", "ce2": "majeur", "ce3": "majeur",
    "cf1": "majeur", "cf2": "majeur", "cf3": "majeur",
    "cg1": "majeur", "cg2": "mineur", "cg3": "majeur", "cg4": "mineur",
    "cg5": "majeur", "cg6": "mineur", "cg7": "majeur", "cg8": "majeur",
    "ch1": "majeur", "ch2": "majeur", "ch3": "majeur", "ch4": "majeur", "ch5": "majeur",
    # Rubrique D — Documentation
    "da1": "remarque", "da2": "remarque", "da3": "critique", "da4": "critique",
    "da5": "critique", "da6": "critique", "da7": "majeur", "da8": "mineur",
    "db1": "majeur", "db2": "critique", "db3": "mineur", "db4": "critique",
    "dc1": "majeur", "dc2": "majeur", "dc3": "majeur", "dc4": "majeur",
    "dc5": "majeur", "dc6": "majeur", "dc7": "critique",
    "de1": "majeur", "de2": "mineur", "de3": "majeur", "de4": "majeur", "de5": "remarque",
    # Rubrique E — Bâtiments, Locaux et Appareillage
    "ea1": "majeur", "ea3": "majeur", "ea4": "majeur", "ea5": "mineur",
    "ea6": "majeur", "ea7": "majeur", "ea8": "majeur", "ea10": "majeur",
    "ea11": "majeur", "ea12": "majeur", "ea14": "majeur", "ea16": "majeur",
    "eb1": "majeur", "eb2": "mineur", "eb3": "majeur", "eb4": "mineur",
    "eb5": "majeur", "eb6": "majeur",
    "ec1": "majeur", "ec2": "majeur", "ec3": "majeur", "ec4": "majeur",
    "ec5": "majeur", "ec6": "majeur", "ec8": "mineur", "ec9": "majeur",
    "ec10": "mineur", "ec12": "majeur", "ec13": "majeur", "ec14": "majeur",
    "ec16": "majeur", "ec17": "majeur", "ec18": "critique", "ec19": "critique",
    "ec20": "majeur", "ec21": "majeur", "ec23": "mineur",
    "ed1": "majeur", "ed2": "majeur", "ed3": "majeur", "ed5": "majeur", "ed7": "majeur",
    "ef1": "majeur", "ef2": "mineur", "ef3": "mineur", "ef4": "majeur", "ef5": "majeur",
    "eg1": "majeur", "eg2": "mineur", "eg3": "majeur", "eg5": "majeur",
    "eg7": "mineur", "eg8": "mineur", "eg9": "mineur", "eg10": "majeur",
    "eh1": "majeur", "eh2": "majeur", "eh3": "majeur", "eh4": "majeur",
    "eh5": "mineur", "eh7": "majeur",
    "ei1": "majeur", "ei2": "majeur", "ei3": "majeur", "ei4": "majeur",
    "ei5": "majeur", "ei6": "majeur", "ei7": "majeur", "ei8": "majeur",
    "ej1": "majeur", "ej2": "critique", "ej3": "majeur", "ej4": "majeur",
    "ej5": "majeur", "ej6": "majeur", "ej7": "majeur",
    # Rubrique F — Livraison et Transport
    "fa1": "majeur", "fa2": "majeur", "fa3": "mineur", "fa4": "mineur",
    "fa5": "majeur", "fa6": "critique", "fa7": "critique",
    # Rubrique G — Retour aux Expéditeurs
    "ga1": "majeur", "ga2": "majeur", "ga3": "majeur", "ga4": "majeur",
    "ga5": "mineur", "ga6": "majeur", "ga7": "majeur",
    "gb1": "majeur", "gb2": "majeur", "gb3": "majeur", "gb4": "majeur", "gb5": "mineur",
    # Rubrique H — Auto-inspection
    "ha1": "majeur", "ha2": "majeur", "ha3": "majeur", "ha4": "majeur",
    # Rubrique I — Autres points
    "ia1": "majeur", "ia2": "majeur", "ia3": "majeur", "ia4": "majeur",
}

# ── Labels des questions pour affichage détaillé ──────────────────────────────
QUESTION_LABELS = {
    "aa1": "Établissement autorisé",
    "aa3": "Certifié par ACOREP/autre",
    "b1": "Manuel qualité signé", "b2": "Politique Qualité déclarée",
    "b3": "Liste des procédures", "b4": "Procédure des procédures",
    "b5": "Procédures signées",
    "ca1": "Pharmacien Responsable", "ca2": "Diplôme pharmacien",
    "ca3": "Certificat d'exercer", "ca4": "Inscrit à l'Ordre",
    "ca5": "Contrat de travail légalisé",
    "cb1": "Personnel Assurance Qualité", "cb2": "Diplôme AQ",
    "cb3": "Inscrit à l'Ordre (AQ)", "cb4": "Certificat d'exercer (AQ)",
    "cb5": "Contrat de travail (AQ)",
    "cc1": "Assistants en pharmacie", "cc2": "Diplômes requis",
    "cc3": "Carte(s) verte(s)", "cc4": "Contrats légalisés",
    "cd1": "Effectif suffisant",
    "ce1": "Organigramme", "ce2": "Organigramme signé/daté",
    "ce3": "Organigramme fonctionnel",
    "cf1": "Description de fonctions", "cf2": "Fiches de poste claires",
    "cf3": "Signé par responsable",
    "cg1": "Procédure de formation", "cg2": "Procédure respectée",
    "cg3": "Programme annuel formation", "cg4": "Programme respecté",
    "cg5": "Formations enregistrées", "cg6": "Formations évaluées",
    "cg7": "Formation produits dangereux", "cg8": "Formations BPDs",
    "ch1": "Procédures hygiène", "ch2": "Hygiène respectée",
    "ch3": "Tenues appropriées", "ch4": "Instructions affichées",
    "ch5": "Procédure accès produits",
    "da1": "Liste fournisseurs", "da2": "Importation médicaments",
    "da3": "Dérogation médicaments interdits", "da4": "AMM valides",
    "da5": "Certificats d'analyse", "da6": "Licences psychotropes",
    "da7": "Procédure commande", "da8": "Documents accessibles",
    "db1": "Procédure réception", "db2": "Vérification réception",
    "db3": "Plans d'échantillonnage", "db4": "Quarantaine après prélèvement",
    "dc1": "Sous-traitance transport", "dc2": "Sous-traitance livraison",
    "dc3": "Sous-traitance équipements", "dc4": "Sous-traitance nuisibles",
    "dc5": "Prise en charge sanitaire", "dc6": "Élimination déchets",
    "dc7": "Évaluation sous-traitants",
    "de1": "Procédure inventaire", "de2": "Périodicité inventaires",
    "de3": "Numéros de lots", "de4": "Rapport inventaire/CAPA",
    "de5": "Valeur du stock",
    "ea1": "Bâtiment conforme", "ea3": "Plan des locaux",
    "ea4": "Agencement logique", "ea5": "Bureau pharmacien (≥9m²)",
    "ea6": "Murs en bon état", "ea7": "Sol en bon état",
    "ea8": "Plafond satisfaisant", "ea10": "Stockage inflammables",
    "ea11": "Zones réception/expédition séparées", "ea12": "Zone de quarantaine",
    "ea14": "Zone de rebuts", "ea16": "Séparation flux personnel/produits",
    "eb1": "Quai de déchargement", "eb2": "SAS d'entrée",
    "eb3": "Cantine séparée", "eb4": "Salle d'administration",
    "eb5": "Vestiaires", "eb6": "Installations sanitaires",
    "ec1": "Procédure stockage", "ec2": "Contrôle contamination",
    "ec3": "FIFO/FEFO", "ec4": "Capacité stockage suffisante",
    "ec5": "Conservation conforme étiquetage", "ec6": "Locaux propres",
    "ec8": "Étagères disponibles", "ec9": "Étagères propres",
    "ec10": "Étagères ordonnées", "ec12": "Palettes suffisantes",
    "ec13": "Palettes conformes", "ec14": "Stockage hors sol",
    "ec16": "Distance des murs", "ec17": "Pas de stockage au plafond",
    "ec18": "Périmés retirés", "ec19": "Thermolabiles contrôlés",
    "ec20": "Pas de péremption <6 mois", "ec21": "Lutte contre nuisibles",
    "ec23": "Pas de poubelles en stockage",
    "ed1": "Procédure conservation froid", "ed2": "Réfrigérateur fonctionnel",
    "ed3": "Thermomètre réfrigérateur", "ed5": "Thermomètre étalonné",
    "ed7": "Relevés température à jour",
    "ef1": "Procédure nettoyage", "ef2": "Programme désinfection",
    "ef3": "Planning nettoyage", "ef4": "Matériels hors stockage",
    "ef5": "Élimination déchets",
    "eg1": "Climatisation/plafonniers", "eg2": "Éclairage suffisant",
    "eg3": "Hygromètre fonctionnel", "eg5": "Thermomètre fonctionnel",
    "eg7": "Emplacements appropriés", "eg8": "Instruments étalonnés",
    "eg9": "Cartographie température", "eg10": "Procédure cartographie",
    "eh1": "Procédure sécurité", "eh2": "Procédure incendie",
    "eh3": "Extincteurs entretenus", "eh4": "Système alarme",
    "eh5": "Caméras surveillance", "eh7": "Accès restreint médicaments",
    "ei1": "Kits informatiques", "ei2": "Système informatique validé",
    "ei3": "Traçabilité entrées/sorties", "ei4": "Procédure traçabilité",
    "ei5": "Paramètre date expiration", "ei6": "Paramètre fournisseur",
    "ei7": "Paramètre nom client", "ei8": "Paramètre numéro lot",
    "ej1": "Liste fournisseurs stupéfiants", "ej2": "Local stupéfiants sécurisé",
    "ej3": "Procédure psychotropes", "ej4": "Registre comptabilité",
    "ej5": "Registre à jour", "ej6": "Carnets bons commande",
    "ej7": "Stupéfiants hors rayons",
    "fa1": "Procédure livraison", "fa2": "Vente pharmacies autorisées",
    "fa3": "Véhicules adaptés", "fa4": "Véhicules conformes",
    "fa5": "Procédure transport", "fa6": "Transport thermolabiles",
    "fa7": "Transport stupéfiants",
    "ga1": "Procédure retour", "ga2": "Quarantaine retours",
    "ga3": "Rapport retours", "ga4": "Procédure rappel",
    "ga5": "Registres retours/rappels", "ga6": "Rapport rappel lot",
    "ga7": "Stockage séparé retours",
    "gb1": "Procédure plaintes", "gb2": "Enregistrement réclamations",
    "gb3": "CAPA appropriées", "gb4": "Partage informations",
    "gb5": "Rapport simulation",
    "ha1": "Procédure auto-inspection", "ha2": "Programme auto-inspection",
    "ha3": "Équipe compétente", "ha4": "Rapports transmis",
    "ia1": "Procédure PFQI", "ia2": "Information autorités PFQI",
    "ia3": "Stockage zone dédiée PFQI", "ia4": "Investigations documentées",
}

# ── Correspondance rubrique pour chaque question ─────────────────────────────
QUESTION_RUBRIQUE_MAP = {q: q[0] if len(q) >= 1 else "?" for q in QUESTION_SEVERITY_MAP}

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
    "eh6": "Caméras de surveillance",
}

# ── Styles de criticité des critères ─────────────────────────────────────────
CRITICALITY_STYLES = {
    "critique": {"label": "Critique", "color": "#E74C3C", "emoji": "🔴", "bg": "rgba(231,76,96,0.12)"},
    "majeur": {"label": "Majeur", "color": "#F39C12", "emoji": "🟠", "bg": "rgba(243,156,18,0.12)"},
    "mineur": {"label": "Mineur", "color": "#3498DB", "emoji": "🔵", "bg": "rgba(52,152,219,0.12)"},
    "remarque": {"label": "Remarque", "color": "#95A5A6", "emoji": "🛈", "bg": "rgba(149,165,166,0.12)"}
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
