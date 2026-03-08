import json
from datetime import datetime
from typing import Any, Dict, List

from app import db
from app.models import TriageResult

RISK_KEYWORDS = {
    "auth": "Touches authentication",
    "security": "Touches security-sensitive logic",
    "payment": "Touches payment systems",
    "billing": "Touches billing flow",
    "migration": "Looks like a migration",
    "architecture": "Implies architectural change",
    "refactor": "Implies broad refactor",
    "permission": "Touches permissions",
    "compliance": "May be compliance-sensitive",
}

SAFE_LABELS = {"bug", "test", "frontend", "backend", "reporting", "flaky", "chore"}


def triage_issue(issue: Dict[str, Any]) -> TriageResult:
    title = (issue.get("title") or "").lower()
    body = (issue.get("body") or "").lower()
    labels = {label.lower() for label in json.loads(issue.get("labels_json") or "[]")}

    score = 0
    reasons = []
    risk_flags = []

    if any(token in body for token in ["steps to repro", "repro", "expected", "actual"]):
        score += 25
        reasons.append("Issue includes reproduction detail or expected vs. actual behavior.")

    if len(body.split()) > 12:
        score += 10
        reasons.append("Issue body has enough context to scope the task.")

    if labels & SAFE_LABELS:
        score += 15
        reasons.append("Labels suggest bounded bug, test, or backend/frontend work.")

    if "flaky" in labels or "test" in labels:
        score += 10
        reasons.append("Flaky-test work is usually a good autonomous lane.")

    for keyword, reason in RISK_KEYWORDS.items():
        if keyword in title or keyword in body or keyword in labels:
            score -= 25
            risk_flags.append(reason)

    if len(body.split()) < 8:
        score -= 20
        reasons.append("Issue is too vague and likely needs clarification.")

    if score >= 35 and not risk_flags:
        decision = "safe_autonomous"
        scope = "small"
    elif risk_flags:
        decision = "senior_review"
        scope = "large"
    else:
        decision = "needs_clarification"
        scope = "medium"

    confidence = max(15, min(95, 50 + score))

    return TriageResult(
        issue_id=issue["id"],
        decision=decision,
        confidence=confidence,
        estimated_scope=scope,
        reasoning_summary=" ".join(reasons) if reasons else "Classified from title/body/labels using bounded-risk heuristics.",
        risk_flags=risk_flags,
    )



def persist_triage(result: TriageResult) -> None:
    db.execute(
        """
        INSERT INTO triage_results (issue_id, decision, confidence, reasoning_summary, risk_flags_json, estimated_scope, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            result.issue_id,
            result.decision,
            result.confidence,
            result.reasoning_summary,
            json.dumps(result.risk_flags),
            result.estimated_scope,
            datetime.utcnow().isoformat(),
        ),
    )
