from fastapi import APIRouter, HTTPException

from app import db
from app.config import get_settings
from app.models import ImportRequest, LaunchRequest, TriageRequest
from app.services.devin_service import (
    DevinAPIError,
    DevinService,
    build_issue_prompt,
    persist_run,
    persist_run_error,
    persist_run_update,
)
from app.services.github_service import GitHubService
from app.services.repository import get_issue, list_issues, list_runs, summary_metrics
from app.services.triage_service import persist_triage, triage_issue

router = APIRouter()


@router.get("/health")
def health():
    settings = get_settings()
    return {
        "ok": True,
        "has_devin_key": bool(settings.devin_api_key),
        "has_github_token": bool(settings.github_token),
        "devin_org_id": bool(settings.devin_org_id),
    }


@router.post("/import")
def import_issues(payload: ImportRequest):
    settings = get_settings()
    github = GitHubService()

    owner = payload.owner or settings.github_owner
    repo = payload.repo or settings.github_repo
    stale_days = payload.stale_days or settings.stale_days_threshold

    if payload.use_demo_data:
        issues = github.demo_issues()
    else:
        if not owner or not repo:
            raise HTTPException(status_code=400, detail="GitHub owner/repo required unless using demo data.")
        issues = github.fetch_stale_issues(owner, repo, stale_days)

    for issue in issues:
        db.insert_issue(issue)

    return {"imported": len(issues), "issues": list_issues(), "metrics": summary_metrics()}


@router.post("/triage")
def triage(payload: TriageRequest):
    issues = list_issues()
    selected = [issue for issue in issues if not payload.issue_ids or issue["id"] in payload.issue_ids]
    if not selected:
        raise HTTPException(status_code=404, detail="No issues found for triage.")

    results = []
    for issue in selected:
        result = triage_issue(issue)
        persist_triage(result)
        results.append(result.model_dump())

    return {"triaged": len(results), "results": results, "issues": list_issues(), "metrics": summary_metrics()}


@router.post("/playbook")
def create_playbook():
    service = DevinService()
    body = (
        "You are resolving stale GitHub backlog items in a production monorepo. "
        "Choose the smallest safe change possible. If the task is unclear or high risk, stop and report blockers. "
        "Always provide a root cause summary, proposed changes, files touched, test evidence, and PR link or blocker report."
    )
    try:
        response = service.create_playbook(title="Backlog Burner / Small Safe Fix", body=body)
    except DevinAPIError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return response


@router.post("/launch")
def launch(payload: LaunchRequest):
    issues = [get_issue(issue_id) for issue_id in payload.issue_ids]
    issues = [issue for issue in issues if issue]
    if not issues:
        raise HTTPException(status_code=404, detail="No selected issues found.")

    launched = []
    service = DevinService()
    for issue in issues:
        prompt = build_issue_prompt(issue)
        if payload.dry_run:
            session = {
                "session_id": "demo-{0}".format(issue["github_issue_number"]),
                "status": "running",
                "url": "https://app.devin.ai/sessions/demo-{0}".format(issue["github_issue_number"]),
                "pull_requests": [],
            }
            persist_run(issue["id"], prompt, session, payload.playbook_id, launch_mode="dry_run")
            launched.append({"issue_id": issue["id"], "session": session, "mode": "dry_run"})
            continue

        try:
            session = service.create_session(prompt)
            persist_run(issue["id"], prompt, session, payload.playbook_id, launch_mode="live")
            launched.append({"issue_id": issue["id"], "session": session, "mode": "live"})
        except DevinAPIError as exc:
            session = {"session_id": None, "status": "launch_error", "url": None, "pull_requests": []}
            persist_run(issue["id"], prompt, session, payload.playbook_id, launch_mode="live", last_error=str(exc))
            launched.append({"issue_id": issue["id"], "session": session, "mode": "live", "error": str(exc)})

    return {"launched": launched, "runs": list_runs(), "metrics": summary_metrics()}


@router.post("/sync")
def sync_runs():
    settings = get_settings()
    runs = list_runs()
    if not runs:
        return {"updated": 0, "runs": [], "metrics": summary_metrics()}

    updated = 0
    service = DevinService()
    for run in runs:
        session_id = run.get("devin_session_id")
        if not session_id:
            continue

        if run.get("launch_mode") == "dry_run" or session_id.startswith("demo-") or not settings.devin_api_key:
            insight = {
                "status": "exit" if run["status"] == "running" else run["status"],
                "pull_requests": [{"pr_url": "https://github.com/finserv/monorepo/pull/{0}".format(run["id"] + 400), "pr_state": "open"}],
                "analysis": {"action_items": ["Open PR ready for engineer review", "Validate regression tests pass"]},
            }
            persist_run_update(run["id"], insight.get("status", run["status"]), insight)
            updated += 1
            continue

        try:
            insight = service.get_session_insights(session_id)
            persist_run_update(run["id"], insight.get("status", run["status"]), insight)
            updated += 1
        except DevinAPIError as exc:
            persist_run_error(run["id"], "sync_error", str(exc))
            updated += 1

    return {"updated": updated, "runs": list_runs(), "metrics": summary_metrics()}
