from app import db
from app.services.github_service import GitHubService


def main() -> None:
    db.init_db()
    service = GitHubService()
    for issue in service.demo_issues():
        db.insert_issue(issue)
    print(f"Seeded {len(service.demo_issues())} demo issues.")


if __name__ == "__main__":
    main()
