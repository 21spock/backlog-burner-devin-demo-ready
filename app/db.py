import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from app.config import get_settings


RowDict = Dict[str, Any]


def _dict_factory(cursor: sqlite3.Cursor, row: Tuple[Any, ...]) -> RowDict:
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}


@contextmanager
def get_connection():
    settings = get_settings()
    db_path = Path(settings.database_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = _dict_factory
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS github_issues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                github_issue_number INTEGER NOT NULL,
                repo TEXT NOT NULL,
                title TEXT NOT NULL,
                body TEXT,
                state TEXT NOT NULL,
                labels_json TEXT NOT NULL DEFAULT '[]',
                author TEXT,
                url TEXT,
                created_at TEXT,
                updated_at TEXT,
                age_days INTEGER NOT NULL DEFAULT 0,
                comments_count INTEGER NOT NULL DEFAULT 0,
                UNIQUE(repo, github_issue_number)
            );

            CREATE TABLE IF NOT EXISTS triage_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                issue_id INTEGER NOT NULL,
                decision TEXT NOT NULL,
                confidence INTEGER NOT NULL,
                reasoning_summary TEXT NOT NULL,
                risk_flags_json TEXT NOT NULL DEFAULT '[]',
                estimated_scope TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(issue_id) REFERENCES github_issues(id)
            );

            CREATE TABLE IF NOT EXISTS devin_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                issue_id INTEGER NOT NULL,
                devin_session_id TEXT,
                status TEXT NOT NULL,
                playbook_id TEXT,
                prompt_snapshot TEXT NOT NULL,
                pr_url TEXT,
                last_insight_summary TEXT,
                session_url TEXT,
                last_error TEXT,
                launch_mode TEXT NOT NULL DEFAULT 'live',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(issue_id) REFERENCES github_issues(id)
            );

            CREATE TABLE IF NOT EXISTS run_updates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                devin_run_id INTEGER NOT NULL,
                status TEXT NOT NULL,
                insight_json TEXT NOT NULL,
                message TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(devin_run_id) REFERENCES devin_runs(id)
            );
            """
        )

        columns = [row["name"] for row in conn.execute("PRAGMA table_info(devin_runs)").fetchall()]
        if "last_error" not in columns:
            conn.execute("ALTER TABLE devin_runs ADD COLUMN last_error TEXT")
        if "launch_mode" not in columns:
            conn.execute("ALTER TABLE devin_runs ADD COLUMN launch_mode TEXT NOT NULL DEFAULT 'live'")


def execute(query: str, params: Iterable[Any] = ()) -> None:
    with get_connection() as conn:
        conn.execute(query, tuple(params))


def fetch_all(query: str, params: Iterable[Any] = ()) -> List[RowDict]:
    with get_connection() as conn:
        return list(conn.execute(query, tuple(params)).fetchall())


def fetch_one(query: str, params: Iterable[Any] = ()) -> Optional[RowDict]:
    with get_connection() as conn:
        return conn.execute(query, tuple(params)).fetchone()


def insert_issue(issue: RowDict) -> None:
    execute(
        """
        INSERT INTO github_issues (
            github_issue_number, repo, title, body, state, labels_json,
            author, url, created_at, updated_at, age_days, comments_count
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(repo, github_issue_number) DO UPDATE SET
            title=excluded.title,
            body=excluded.body,
            state=excluded.state,
            labels_json=excluded.labels_json,
            author=excluded.author,
            url=excluded.url,
            created_at=excluded.created_at,
            updated_at=excluded.updated_at,
            age_days=excluded.age_days,
            comments_count=excluded.comments_count
        """,
        (
            issue["github_issue_number"],
            issue["repo"],
            issue["title"],
            issue.get("body", ""),
            issue.get("state", "open"),
            json.dumps(issue.get("labels", [])),
            issue.get("author", ""),
            issue.get("url", ""),
            issue.get("created_at", ""),
            issue.get("updated_at", ""),
            issue.get("age_days", 0),
            issue.get("comments_count", 0),
        ),
    )
