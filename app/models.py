from typing import List, Literal, Optional

from pydantic import BaseModel, Field


Decision = Literal["safe_autonomous", "needs_clarification", "senior_review"]


class ImportRequest(BaseModel):
    owner: Optional[str] = None
    repo: Optional[str] = None
    stale_days: Optional[int] = Field(default=None, ge=1)
    use_demo_data: bool = False


class TriageRequest(BaseModel):
    issue_ids: Optional[List[int]] = None


class LaunchRequest(BaseModel):
    issue_ids: List[int]
    playbook_id: Optional[str] = None
    dry_run: bool = False


class TriageResult(BaseModel):
    issue_id: int
    decision: Decision
    confidence: int
    estimated_scope: str
    reasoning_summary: str
    risk_flags: List[str]


class SummaryMetrics(BaseModel):
    issues_imported: int
    safe_autonomous: int
    needs_clarification: int
    senior_review: int
    active_runs: int
    completed_runs: int
    prs_opened: int
