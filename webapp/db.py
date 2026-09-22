"""أرشفة/ذاكرة تخزين مؤقت (History / Cache) — القسم 13 من المواصفة."""
import json
import os
import sqlite3
from datetime import datetime, timezone

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "job_descriptions.db")


def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS job_descriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_title_raw TEXT NOT NULL,
            job_title_normalized TEXT NOT NULL,
            sub_units_raw TEXT NOT NULL DEFAULT '',
            level_tier INTEGER NOT NULL,
            content_json TEXT NOT NULL,
            docx_file_path TEXT NOT NULL,
            version INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    # ترقية قواعد بيانات محلية أُنشئت قبل إضافة عمود sub_units_raw.
    try:
        conn.execute("ALTER TABLE job_descriptions ADD COLUMN sub_units_raw TEXT NOT NULL DEFAULT ''")
    except sqlite3.OperationalError:
        pass
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_job_title_normalized ON job_descriptions(job_title_normalized)"
    )
    conn.commit()
    conn.close()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_latest_by_normalized(job_title_normalized: str):
    conn = get_connection()
    row = conn.execute(
        """
        SELECT * FROM job_descriptions
        WHERE job_title_normalized = ?
        ORDER BY version DESC LIMIT 1
        """,
        (job_title_normalized,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_by_id(record_id: int):
    conn = get_connection()
    row = conn.execute("SELECT * FROM job_descriptions WHERE id = ?", (record_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def insert_record(job_title_raw: str, job_title_normalized: str, level_tier: int,
                   content: dict, docx_file_path: str, sub_units_raw: str = "") -> dict:
    conn = get_connection()
    existing = conn.execute(
        "SELECT MAX(version) AS max_version FROM job_descriptions WHERE job_title_normalized = ?",
        (job_title_normalized,),
    ).fetchone()
    next_version = (existing["max_version"] or 0) + 1
    now = _now()
    cursor = conn.execute(
        """
        INSERT INTO job_descriptions
            (job_title_raw, job_title_normalized, sub_units_raw, level_tier, content_json,
             docx_file_path, version, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (job_title_raw, job_title_normalized, sub_units_raw, level_tier,
         json.dumps(content, ensure_ascii=False), docx_file_path, next_version, now, now),
    )
    conn.commit()
    record_id = cursor.lastrowid
    conn.close()
    return get_by_id(record_id)


def list_history(limit: int = 50):
    """أحدث نسخة فقط لكل مسمى وظيفي، مرتّبة بحسب آخر تحديث."""
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT jd.* FROM job_descriptions jd
        INNER JOIN (
            SELECT job_title_normalized, MAX(version) AS max_version
            FROM job_descriptions GROUP BY job_title_normalized
        ) latest
        ON jd.job_title_normalized = latest.job_title_normalized
        AND jd.version = latest.max_version
        ORDER BY jd.updated_at DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def list_versions(job_title_normalized: str):
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT * FROM job_descriptions
        WHERE job_title_normalized = ?
        ORDER BY version DESC
        """,
        (job_title_normalized,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
