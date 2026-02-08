from __future__ import annotations

import json
import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import dataclasses

logger = logging.getLogger(__name__)

def _now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds")

def _to_json(obj: Any) -> str:
    def default(o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        if isinstance(o, set):
            return sorted(list(o))
        return str(o)
    return json.dumps(obj, default=default, ensure_ascii=False)

def _from_json(raw: str) -> Any:
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return raw

class DataStore:
    def __init__(self, db_path: Union[str, Path, None] = "resume_analyzer.db",
                 auto_init: bool = True, autocommit: bool = True) -> None:
        self.db_path = Path(db_path) if db_path else Path(":memory:")
        self.autocommit = autocommit
        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row
        if auto_init:
            self._create_schema()

    def _create_schema(self) -> None:
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

    def add_resume(self, parsed_resume: Dict[str, Any], candidate_name: str,
                   original_file: Optional[str] = None) -> int:
        cur = self._conn.cursor()
        cur.execute(
            "INSERT INTO resumes (candidate_name, original_file, parsed_json, created_at) VALUES (?, ?, ?, ?)",
            (candidate_name, original_file or "", _to_json(parsed_resume), _now_iso())
        )
        if self.autocommit:
            self._conn.commit()
        return cur.lastrowid

    def add_job_description(self, description: str, job_title: str) -> int:
        cur = self._conn.cursor()
        cur.execute(
            "INSERT INTO job_descriptions (job_title, description, created_at) VALUES (?, ?, ?)",
            (job_title, description, _now_iso())
        )
        if self.autocommit:
            self._conn.commit()
        return cur.lastrowid

    def add_analysis(self, match_result: Any, resume_id: int, jd_id: int) -> int:
        if dataclasses.is_dataclass(match_result):
            overall_score = getattr(match_result, "overall_score", None)
            details = dataclasses.asdict(match_result)
        elif isinstance(match_result, dict):
            overall_score = match_result.get("overall_score")
            details = match_result
        else:
            overall_score = getattr(match_result, "overall_score", None)
            details = match_result.__dict__ if hasattr(match_result, "__dict__") else str(match_result)

        cur = self._conn.cursor()
        cur.execute(
            "INSERT INTO analyses (resume_id, jd_id, overall_score, details_json, created_at) VALUES (?, ?, ?, ?, ?)",
            (resume_id, jd_id, overall_score, _to_json(details), _now_iso())
        )
        if self.autocommit:
            self._conn.commit()
        return cur.lastrowid

    def get_resume(self, resume_id: int) -> Dict[str, Any]:
        cur = self._conn.execute("SELECT * FROM resumes WHERE id = ?", (resume_id,))
        row = cur.fetchone()
        if not row:
            raise KeyError(resume_id)
        payload = dict(row)
        payload["parsed_json"] = _from_json(payload["parsed_json"])
        return payload

    def get_job_description(self, jd_id: int) -> Dict[str, Any]:
        cur = self._conn.execute("SELECT * FROM job_descriptions WHERE id = ?", (jd_id,))
        row = cur.fetchone()
        if not row:
            raise KeyError(jd_id)
        return dict(row)

    def get_analysis(self, analysis_id: int) -> Dict[str, Any]:
        cur = self._conn.execute("SELECT * FROM analyses WHERE id = ?", (analysis_id,))
        row = cur.fetchone()
        if not row:
            raise KeyError(analysis_id)
        payload = dict(row)
        payload["details_json"] = _from_json(payload["details_json"])
        return payload

    def list_resumes(self) -> List[Dict[str, Any]]:
        cur = self._conn.execute("SELECT * FROM resumes ORDER BY created_at DESC")
        return [dict(r) for r in cur.fetchall()]

    def list_job_descriptions(self) -> List[Dict[str, Any]]:
        cur = self._conn.execute("SELECT * FROM job_descriptions ORDER BY created_at DESC")
        return [dict(r) for r in cur.fetchall()]

    def list_analyses(self) -> List[Dict[str, Any]]:
        cur = self._conn.execute("SELECT * FROM analyses ORDER BY created_at DESC")
        return [dict(r) for r in cur.fetchall()]

    def commit(self) -> None:
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "DataStore":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None and self.autocommit:
            self._conn.commit()
        self.close()
