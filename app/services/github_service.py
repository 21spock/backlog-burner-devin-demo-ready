from datetime import datetime, timezone
from typing import Any, Dict, List

import httpx

from app.config import get_settings


class GitHubService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def _headers(self) -> Dict[str, str]:
        headers = {"Accept": "application/vnd.github+json"}
        if self.settings.github_token:
            headers["Authorization"] = "Bearer {0}".format(self.settings.github_token)
        return headers

    def fetch_stale_issues(self, owner: str, repo: str, stale_days: int) -> List[Dict[str, Any]]:
        url = "https://api.github.com/repos/{0}/{1}/issues".format(owner, repo)
        with httpx.Client(timeout=30.0) as client:
            response = client.get(
                url,
                headers=self._headers(),
                params={"state": "open", "per_page": 100, "sort": "updated", "direction": "asc"},
            )
            response.raise_for_status()
            raw_issues = response.json()

        now = datetime.now(timezone.utc)
        normalized = []
        for item in raw_issues:
            if "pull_request" in item:
                continue
            created_at = datetime.fromisoformat(item["created_at"].replace("Z", "+00:00"))
            age_days = (now - created_at).days
            if age_days < stale_days:
                continue
            normalized.append(
                {
                    "github_issue_number": item["number"],
                    "repo": "{0}/{1}".format(owner, repo),
                    "title": item["title"],
                    "body": item.get("body") or "",
                    "state": item.get("state", "open"),
                    "labels": [label["name"] for label in item.get("labels", [])],
                    "author": item.get("user", {}).get("login", ""),
                    "url": item.get("html_url", ""),
                    "created_at": item.get("created_at", ""),
                    "updated_at": item.get("updated_at", ""),
                    "age_days": age_days,
                    "comments_count": item.get("comments", 0),
                }
            )
        return normalized

    def demo_issues(self) -> List[Dict[str, Any]]:
        repo_name = self._repo_name()
        base_url = self._repo_base_url(repo_name)
        return [
            {
                "github_issue_number": 201,
                "repo": repo_name,
                "title": "Disable live Devin launch when DEVIN_API_KEY is missing",
                "body": (
                    "Problem: the dashboard still invites users to click live launch even when no Devin key is configured.\n\n"
                    "Steps to repro:\n"
                    "1. Remove DEVIN_API_KEY from .env\n"
                    "2. Open the dashboard\n"
                    "3. Click Launch live Devin sessions\n\n"
                    "Expected: the live-launch action is visibly disabled and helper text explains what is missing.\n"
                    "Actual: users can still click into a broken path.\n\n"
                    "Acceptance criteria:\n"
                    "- live launch button is disabled when DEVIN_API_KEY is missing\n"
                    "- helper text explains how to enable live launch\n"
                    "- demo launch still works"
                ),
                "state": "open",
                "labels": ["bug", "frontend", "demo-safe", "safe-lane"],
                "author": "vp-eng-demo",
                "url": "{0}/issues/201".format(base_url),
                "created_at": "2025-11-14T09:00:00Z",
                "updated_at": "2026-02-10T10:00:00Z",
                "age_days": 115,
                "comments_count": 2,
            },
            {
                "github_issue_number": 202,
                "repo": repo_name,
                "title": "Add triage filter chips so engineers can isolate safe-autonomous issues",
                "body": (
                    "Problem: once triage runs, engineers still have to manually scan the whole table to find issues Devin should work on.\n\n"
                    "Expected: filter chips for Safe autonomous, Needs clarification, and Senior review.\n"
                    "Actual: backlog table stays flat after triage.\n\n"
                    "Acceptance criteria:\n"
                    "- chips filter the visible issues without a page reload\n"
                    "- active filter state is obvious\n"
                    "- Clear filters returns the full list"
                ),
                "state": "open",
                "labels": ["enhancement", "frontend", "ux", "safe-lane"],
                "author": "staff-eng-demo",
                "url": "{0}/issues/202".format(base_url),
                "created_at": "2025-11-18T09:00:00Z",
                "updated_at": "2026-02-12T10:00:00Z",
                "age_days": 111,
                "comments_count": 4,
            },
            {
                "github_issue_number": 203,
                "repo": repo_name,
                "title": "Improve issue import reliability",
                "body": (
                    "Some imports feel incomplete and stale issues occasionally look duplicated.\n\n"
                    "We should make the import flow better for enterprise customers before the next demo."
                ),
                "state": "open",
                "labels": ["bug", "needs-spec"],
                "author": "product-demo",
                "url": "{0}/issues/203".format(base_url),
                "created_at": "2025-12-03T09:00:00Z",
                "updated_at": "2026-02-15T10:00:00Z",
                "age_days": 96,
                "comments_count": 1,
            },
            {
                "github_issue_number": 204,
                "repo": repo_name,
                "title": "Make progress notifications more useful for the engineering team",
                "body": (
                    "Stakeholders want better updates while work is running.\n\n"
                    "We should show the right status detail in the dashboard and maybe send something to Slack, but the exact message format is still undecided.\n\n"
                    "Known asks:\n"
                    "- surface blockers clearly\n"
                    "- avoid noisy updates\n"
                    "- keep leadership informed"
                ),
                "state": "open",
                "labels": ["enhancement", "product-question"],
                "author": "vp-product-demo",
                "url": "{0}/issues/204".format(base_url),
                "created_at": "2025-12-09T09:00:00Z",
                "updated_at": "2026-02-14T10:00:00Z",
                "age_days": 90,
                "comments_count": 5,
            },
            {
                "github_issue_number": 205,
                "repo": repo_name,
                "title": "Add role-based approval controls before allowing live issue launches",
                "body": (
                    "We need an approval model before this can be used in a regulated engineering organization.\n\n"
                    "Requirements under discussion:\n"
                    "- only approved roles can launch live Devin sessions\n"
                    "- launch approvals should be auditable\n"
                    "- permissions must work across multiple teams and future orgs\n\n"
                    "This likely touches auth, permissions, and audit requirements."
                ),
                "state": "open",
                "labels": ["security", "permissions", "architecture", "compliance"],
                "author": "security-demo",
                "url": "{0}/issues/205".format(base_url),
                "created_at": "2025-10-28T09:00:00Z",
                "updated_at": "2026-01-28T10:00:00Z",
                "age_days": 132,
                "comments_count": 7,
            },
            {
                "github_issue_number": 206,
                "repo": repo_name,
                "title": "Support multi-repo and multi-tenant backlog routing for enterprise roll-out",
                "body": (
                    "Leadership wants this to scale beyond a single repo.\n\n"
                    "Potential scope includes multi-repo imports, routing policies, org-level analytics, repo-specific playbooks, and tenant isolation for enterprise customers.\n\n"
                    "This is a larger systems design problem rather than a single isolated code fix."
                ),
                "state": "open",
                "labels": ["architecture", "multi-tenant", "roadmap", "enterprise"],
                "author": "cto-demo",
                "url": "{0}/issues/206".format(base_url),
                "created_at": "2025-10-19T09:00:00Z",
                "updated_at": "2026-01-22T10:00:00Z",
                "age_days": 141,
                "comments_count": 8,
            },
        ]

    def _repo_name(self) -> str:
        if self.settings.github_owner and self.settings.github_repo:
            return "{0}/{1}".format(self.settings.github_owner, self.settings.github_repo)
        return "aaronspock/backlog-burner-devin-demo"

    def _repo_base_url(self, repo_name: str) -> str:
        return "https://github.com/{0}".format(repo_name)
