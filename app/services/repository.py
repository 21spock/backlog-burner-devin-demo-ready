import json
from typing import Any, Dict, List, Optional

from app import db
from app.models import SummaryMetrics


RowDict = Dict[str, Any]


def list_issues() -> List[RowDict]:
    rows = db.fetch_all(
        """
        SELECT gi.*, tr.decision, tr.confidence, tr.reasoning_summary, tr.risk_flags_json, tr.estimated_scope
        FROM github_issues gi
        LEFT JOIN (
            SELECT t1.*
            FROM triage_results t1
            INNER JOIN (
                SELECT issue_id, MAX(id) AS max_id FROM triage_results GROUP BY issue_id
            ) latest ON latest.max_id = t1.id
        ) tr ON tr.issue_id = gi.id
        ORDER BY gi.age_days DESC, gi.github_issue_number ASC
        """
    )
    for row in rows:
        row["labels"] = json.loads(row.get("labels_json") or "[]")
        row["risk_flags"] = json.loads(row.get("risk_flags_json") or "[]") if row.get("risk_flags_json") else []
    return rows



def get_issue(issue_id: int) -> Optional[RowDict]:
    row = db.fetch_one("SELECT * FROM github_issues WHERE id = ?", (issue_id,))
    if row:
        row["labels"] = json.loads(row.get("labels_json") or "[]")
    return row



def list_runs() -> List[RowDict]:
    return db.fetch_all(
        """
        SELECT dr.*, gi.github_issue_number, gi.title AS issue_title
        FROM devin_runs dr
        JOIN github_issues gi ON gi.id = dr.issue_id
        ORDER BY dr.updated_at DESC, dr.id DESC
        """
    )



def summary_metrics() -> SummaryMetrics:
    issues = db.fetch_all("SELECT COUNT(*) AS count FROM github_issues")
    triage_counts = db.fetch_all(
        """
        SELECT decision, COUNT(*) AS count
        FROM (
            SELECT t1.*
            FROM triage_results t1
            INNER JOIN (
                SELECT issue_id, MAX(id) AS max_id FROM triage_results GROUP BY issue_id
            ) latest ON latest.max_id = t1.id
        )
        GROUP BY decision
        """
    )
    runs = db.fetch_all("SELECT status, COUNT(*) AS count FROM devin_runs GROUP BY status")
    prs = db.fetch_one("SELECT COUNT(*) AS count FROM devin_runs WHERE pr_url IS NOT NULL AND pr_url != ''")

    triage_map = {row["decision"]: row["count"] for row in triage_counts}
    active_statuses = {"new", "claimed", "running", "resuming", "blocked", "queued"}
    active_runs = sum(row["count"] for row in runs if row["status"] in active_statuses)
    completed_runs = sum(row["count"] for row in runs if row["status"] in {"exit", "completed", "succeeded"})

    return SummaryMetrics(
        issues_imported=issues[0]["count"] if issues else 0,
        safe_autonomous=triage_map.get("safe_autonomous", 0),
        needs_clarification=triage_map.get("needs_clarification", 0),
        senior_review=triage_map.get("senior_review", 0),
        active_runs=active_runs,
        completed_runs=completed_runs,
        prs_opened=prs["count"] if prs else 0,
    )
