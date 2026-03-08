import json
from datetime import datetime
from typing import Any, Dict, Optional

import httpx

from app import db
from app.config import get_settings


class DevinAPIError(Exception):
    pass


class DevinService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.base_url = self.settings.devin_api_base.rstrip("/")

    def _headers(self) -> Dict[str, str]:
        if not self.settings.devin_api_key:
            raise DevinAPIError("DEVIN_API_KEY is missing. Add it to .env and restart the server.")
        return {
            "Authorization": "Bearer {0}".format(self.settings.devin_api_key),
            "Content-Type": "application/json",
        }

    def _build_url(self, suffix: str) -> str:
        org_part = "/{0}".format(self.settings.devin_org_id) if self.settings.devin_org_id else ""
        return "{0}{1}{2}".format(self.base_url, org_part, suffix)

    def _raise_for_status(self, response: httpx.Response) -> None:
        if response.is_success:
            return
        try:
            payload = response.json()
        except Exception:
            payload = response.text
        raise DevinAPIError("Devin API error {0}: {1}".format(response.status_code, payload))

    def create_playbook(self, title: str, body: str, macro: Optional[str] = None) -> Dict[str, Any]:
        payload = {"title": title, "body": body, "macro": macro}
        with httpx.Client(timeout=30.0) as client:
            response = client.post(self._build_url("/playbooks"), headers=self._headers(), json=payload)
            self._raise_for_status(response)
            return response.json()

    def create_session(self, prompt: str) -> Dict[str, Any]:
        payload = {"prompt": prompt}
        with httpx.Client(timeout=60.0) as client:
            response = client.post(self._build_url("/sessions"), headers=self._headers(), json=payload)
            self._raise_for_status(response)
            return response.json()

    def get_session_insights(self, session_id: str) -> Dict[str, Any]:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(self._build_url("/sessions/{0}/insights".format(session_id)), headers=self._headers())
            self._raise_for_status(response)
            return response.json()


def build_issue_prompt(issue: Dict[str, Any]) -> str:
    return """
You are resolving a GitHub issue in a production monorepo.

Goal:
Fix this issue with the smallest safe change possible.

Rules:
- Do not make architectural changes unless absolutely required.
- Prefer localized fixes.
- Run relevant tests or lint checks for the touched area.
- If the issue is underspecified, stop and report exactly what is missing.
- If the task touches auth, security, payments, infra, migrations, permissions, or compliance-sensitive logic, escalate instead of proceeding.

Required output:
1. Root cause summary
2. Proposed change summary
3. Files touched
4. Test evidence
5. PR link if created
6. Clear blocker report if not completed

Issue #{issue_number}: {title}

Issue body:
{body}

GitHub URL:
{url}
""".strip().format(
        issue_number=issue["github_issue_number"],
        title=issue["title"],
        body=issue.get("body") or "(none provided)",
        url=issue.get("url") or "(none)",
    )


def persist_run(issue_id: int, prompt: str, session: Dict[str, Any], playbook_id: Optional[str] = None, launch_mode: str = "live", last_error: Optional[str] = None) -> None:
    session_id = session.get("session_id") or session.get("id") or session.get("sessionId")
    session_url = session.get("url") or session.get("session_url") or session.get("sessionUrl")
    status = session.get("status", "new")
    pull_requests = session.get("pull_requests") or session.get("pullRequests") or []
    pr_url = pull_requests[0].get("pr_url") if pull_requests and isinstance(pull_requests[0], dict) else None

    db.execute(
        """
        INSERT INTO devin_runs (
            issue_id, devin_session_id, status, playbook_id, prompt_snapshot,
            pr_url, last_insight_summary, session_url, last_error, launch_mode, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            issue_id,
            session_id,
            status,
            playbook_id,
            prompt,
            pr_url,
            None,
            session_url,
            last_error,
            launch_mode,
            datetime.utcnow().isoformat(),
            datetime.utcnow().isoformat(),
        ),
    )


def persist_run_update(run_id: int, status: str, insight: Dict[str, Any]) -> None:
    analysis = insight.get("analysis") or {}
    action_items = analysis.get("action_items") or analysis.get("actionItems") or []
    summary = "; ".join([str(item) for item in action_items[:3]]) if action_items else "No action items returned yet."
    pull_requests = insight.get("pull_requests") or insight.get("pullRequests") or []
    pr_url = pull_requests[0].get("pr_url") if pull_requests and isinstance(pull_requests[0], dict) else None

    db.execute(
        """
        UPDATE devin_runs
        SET status = ?, pr_url = COALESCE(?, pr_url), last_insight_summary = ?, last_error = NULL, updated_at = ?
        WHERE id = ?
        """,
        (status, pr_url, summary, datetime.utcnow().isoformat(), run_id),
    )
    db.execute(
        """
        INSERT INTO run_updates (devin_run_id, status, insight_json, message, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (run_id, status, json.dumps(insight), summary, datetime.utcnow().isoformat()),
    )


def persist_run_error(run_id: int, status: str, message: str) -> None:
    payload = {"error": message}
    db.execute(
        """
        UPDATE devin_runs
        SET status = ?, last_error = ?, updated_at = ?
        WHERE id = ?
        """,
        (status, message, datetime.utcnow().isoformat(), run_id),
    )
    db.execute(
        """
        INSERT INTO run_updates (devin_run_id, status, insight_json, message, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (run_id, status, json.dumps(payload), message, datetime.utcnow().isoformat()),
    )
