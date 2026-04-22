"""
Module de base de données SQLite pour les décisions des experts.
Inclut le niveau BPSD et les observations du comité.
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict

DB_PATH = Path(__file__).parent / "decisions.sqlite"


def _get_connection() -> sqlite3.Connection:
    """Crée ou ouvre la base de données et initialise les tables."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    # Créer la table si elle n'existe pas (nouveau schéma)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS decisions_expert (
            instance_id TEXT PRIMARY KEY,
            nom_etablissement TEXT NOT NULL,
            score_algo REAL DEFAULT 0,
            statut_expert TEXT NOT NULL,
            notes_expert TEXT DEFAULT '',
            date_decision TEXT NOT NULL
        )
    """)

    # Migration : ajouter les colonnes manquantes si la table existe déjà avec l'ancien schéma
    try:
        conn.execute("SELECT score_algo FROM decisions_expert LIMIT 1")
    except sqlite3.OperationalError:
        conn.execute("ALTER TABLE decisions_expert ADD COLUMN score_algo REAL DEFAULT 0")

    try:
        conn.execute("SELECT statut_expert FROM decisions_expert LIMIT 1")
    except sqlite3.OperationalError:
        conn.execute("ALTER TABLE decisions_expert ADD COLUMN statut_expert TEXT DEFAULT ''")

    try:
        conn.execute("SELECT notes_expert FROM decisions_expert LIMIT 1")
    except sqlite3.OperationalError:
        conn.execute("ALTER TABLE decisions_expert ADD COLUMN notes_expert TEXT DEFAULT ''")

    conn.commit()
    return conn


def save_decision(
    instance_id: str,
    nom_etablissement: str,
    score_algo: float = 0.0,
    statut_expert: str = "",
    notes_expert: str = "",
    # Compatibilité avec l'ancien code
    decision: str = "",
    commentaire: str = "",
) -> bool:
    """Enregistre ou met à jour une décision d'expert."""
    # Compatibilité : si appelé avec l'ancien format
    if decision and not statut_expert:
        statut_expert = decision
    if commentaire and not notes_expert:
        notes_expert = commentaire

    conn = _get_connection()
    try:
        conn.execute("""
            INSERT INTO decisions_expert (instance_id, nom_etablissement, score_algo, statut_expert, notes_expert, date_decision)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(instance_id) DO UPDATE SET
                nom_etablissement = excluded.nom_etablissement,
                score_algo = excluded.score_algo,
                statut_expert = excluded.statut_expert,
                notes_expert = excluded.notes_expert,
                date_decision = excluded.date_decision
        """, (instance_id, nom_etablissement, score_algo, statut_expert, notes_expert, datetime.now().isoformat()))
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()


def get_decision(instance_id: str) -> Optional[Dict]:
    """Récupère la décision existante pour un établissement."""
    conn = _get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM decisions_expert WHERE instance_id = ?", (instance_id,)
        ).fetchone()
        if row:
            return dict(row)
        return None
    finally:
        conn.close()


def get_all_decisions() -> List[Dict]:
    """Récupère toutes les décisions enregistrées."""
    conn = _get_connection()
    try:
        rows = conn.execute("SELECT * FROM decisions_expert ORDER BY date_decision DESC").fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()
