"""
Data Store Module
=================
Provides lightweight persistence for the resume‑matching system.

* Uses SQLite so it works out‑of‑the‑box (no server).
* Serialises rich Python objects (e.g. `MatchResult` dataclass instances or
  parsed‑resume dictionaries) to JSON.
* Exposes a single high‑level `DataStore` façade that the other modules can
  depend on without worrying about SQL.

Typical usage
-------------
>>> ds = DataStore("resume_analyzer.db")
>>> resume_id = ds.add_resume(parsed_resume, candidate_name="Alice Smith")
>>> jd_id      = ds.add_job_description(job_description, job_title="Data Scientist")
>>> analysis_id = ds.add_analysis(match_result, resume_id, jd_id)
>>> ds.commit()     # if you disabled autocommit
>>> analysis = ds.get_analysis(analysis_id)
>>> ds.close()
"""

from __future__ import annotations

import json
import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import dataclasses

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# ------------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------------

def _now_iso() -> str:
    """Return current timestamp in ISO‑8601 format."""
    return datetime.utcnow().isoformat(timespec="seconds")


def _to_json(obj: Any) -> str:
    """
    Convert arbitrary Python object to a JSON string.

    * Dataclass instances are converted via `dataclasses.asdict`
    * Sets are converted to sorted lists
    * Non‑serialisable objects are coerced via `str()`
    """
    def default(o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        if isinstance(o, set):
            return sorted(list(o))
        return str(o)

    try:
        return json.dumps(obj, default=default, ensure_ascii=False)
    except TypeError as exc:
        logger.error("Failed to serialise object of type %s – %s", type(obj), exc)
        raise

def _from_json(raw: str) -> Any:
    """JSON‑decode a string, falling back to the raw string on failure."""
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw


# ------------------------------------------------------------------------------
# DataStore
# ------------------------------------------------------------------------------

class DataStore:
    """
    Thin SQLite wrapper to persist resumes, job descriptions, and analysis runs.

    Schema (v1)
    -----------
    • resumes(id PK, candidate_name, original_file, parsed_json, created_at)
    • job_descriptions(id PK, job_title, description, created_at)
    • analyses(id PK, resume_id FK, jd_id FK, overall_score, details_json, created_at)
    """

    def __init__(self, db_path: Union[str, Path, None] = "resume_analyzer.db",
                 auto_init: bool = True, autocommit: bool = True) -> None:
        self.db_path = Path(db_path) if db_path else Path(":memory:")
        self.autocommit = autocommit
        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row  # nice dict‑like rows
        if auto_init:
            self._create_schema()

    # ------------------------------------------------------------------ DDL ---

    def _create_schema(self) -> None:
        """Create tables if they don't yet exist."""
        cur = self._conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS resumes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            candidate_name TEXT,
            original_file TEXT,
            parsed_json TEXT,
            created_at TEXT
        );
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS job_descriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_title TEXT,
            description TEXT,
            created_at TEXT
        );
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            resume_id INTEGER,
            jd_id INTEGER,
            overall_score REAL,
            details_json TEXT,
            created_at TEXT,
            FOREIGN KEY (resume_id) REFERENCES resumes(id),
            FOREIGN KEY (jd_id) REFERENCES job_descriptions(id)
        );
        """)
        if self.autocommit:
            self._conn.commit()

    # ------------------------------------------------------------------ Insert helpers ---

    def add_resume(self, parsed_resume: Dict[str, Any], candidate_name: str,
                   original_file: Optional[str] = None) -> int:
        """Insert a parsed resume and return its ID."""
        cur = self._conn.cursor()
        cur.execute(
            """
            INSERT INTO resumes (candidate_name, original_file, parsed_json, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                candidate_name,
                original_file or "",
                _to_json(parsed_resume),
                _now_iso(),
            ),
        )
        if self.autocommit:
            self._conn.commit()
        resume_id = cur.lastrowid
        logger.debug("Stored resume %s for %s", resume_id, candidate_name)
        return resume_id

    def add_job_description(self, description: str, job_title: str) -> int:
        """Insert a job description and return its ID."""
        cur = self._conn.cursor()
        cur.execute(
            """
            INSERT INTO job_descriptions (job_title, description, created_at)
            VALUES (?, ?, ?)
            """,
            (
                job_title,
                description,
                _now_iso(),
            ),
        )
        if self.autocommit:
            self._conn.commit()
        jd_id = cur.lastrowid
        logger.debug("Stored job description %s for role %s", jd_id, job_title)
        return jd_id

    def add_analysis(self, match_result: Any, resume_id: int, jd_id: int) -> int:
        """
        Insert an analysis run.

        Parameters
        ----------
        match_result
            Expected to be the `MatchResult` dataclass from *scoring.py* but may be
            any object that contains an `overall_score` attribute / key.

        Returns
        -------
        int
            Primary‑key ID of the new analyses row.
        """
        # Duck‑type access to overall_score
        if dataclasses.is_dataclass(match_result):
            overall_score = getattr(match_result, "overall_score", None)
            details = dataclasses.asdict(match_result)
        elif isinstance(match_result, dict):
            overall_score = match_result.get("overall_score")
            details = match_result
        else:
            # Attempt generic attribute access
            overall_score = getattr(match_result, "overall_score", None)
            details = match_result.__dict__ if hasattr(match_result, "__dict__") else str(match_result)

        cur = self._conn.cursor()
        cur.execute(
            """
            INSERT INTO analyses (resume_id, jd_id, overall_score, details_json, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                resume_id,
                jd_id,
                overall_score,
                _to_json(details),
                _now_iso(),
            ),
        )
        if self.autocommit:
            self._conn.commit()
        analysis_id = cur.lastrowid
        logger.debug("Stored analysis %s (resume %s vs JD %s)", analysis_id, resume_id, jd_id)
        return analysis_id

    # ------------------------------------------------------------------ Query helpers ---

    def get_resume(self, resume_id: int) -> Dict[str, Any]:
        cur = self._conn.execute("SELECT * FROM resumes WHERE id = ?", (resume_id,))
        row = cur.fetchone()
        if not row:
            raise KeyError(f"Resume id {resume_id} not found")
        payload = dict(row)
        payload["parsed_json"] = _from_json(payload["parsed_json"])
        return payload

    def get_job_description(self, jd_id: int) -> Dict[str, Any]:
        cur = self._conn.execute("SELECT * FROM job_descriptions WHERE id = ?", (jd_id,))
        row = cur.fetchone()
        if not row:
            raise KeyError(f"Job description id {jd_id} not found")
        return dict(row)

    def get_analysis(self, analysis_id: int) -> Dict[str, Any]:
        cur = self._conn.execute("SELECT * FROM analyses WHERE id = ?", (analysis_id,))
        row = cur.fetchone()
        if not row:
            raise KeyError(f"Analysis id {analysis_id} not found")
        payload = dict(row)
        payload["details_json"] = _from_json(payload["details_json"])
        return payload

    def list_resumes(self) -> List[Dict[str, Any]]:
        cur = self._conn.execute("SELECT * FROM resumes ORDER BY created_at DESC")
        rows = cur.fetchall()
        return [dict(r) for r in rows]

    def list_job_descriptions(self) -> List[Dict[str, Any]]:
        cur = self._conn.execute("SELECT * FROM job_descriptions ORDER BY created_at DESC")
        rows = cur.fetchall()
        return [dict(r) for r in rows]

    def list_analyses(self) -> List[Dict[str, Any]]:
        cur = self._conn.execute("SELECT * FROM analyses ORDER BY created_at DESC")
        rows = cur.fetchall()
        return [dict(r) for r in rows]

    # ------------------------------------------------------------------ Convenience ---

    def commit(self) -> None:
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    # ------------------------------------------------------------------ Context manager ---

    def __enter__(self) -> "DataStore":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None and self.autocommit:
            self._conn.commit()
        self.close()
