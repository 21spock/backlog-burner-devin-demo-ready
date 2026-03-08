# Backlog Burner (Python Starter App)

Backlog Burner is a lightweight FastAPI demo app for a Devin technical take-home. It imports stale GitHub issues, triages them into action buckets, launches Devin on low-risk issues, and gives leadership a clean view of what is moving.

## What changed in this rebuild

- Python 3.9-compatible typing
- clear split between **live Devin launch** and **demo launch**
- config banner on the homepage so you can see whether live mode is available
- better run tracking with `launch_mode` and `last_error`
- sync errors surface in the dashboard instead of disappearing

## Stack

- FastAPI
- SQLite
- Jinja2 templates
- Vanilla JS frontend
- GitHub REST API
- Devin API

## Quick start

### 1. Create a virtual environment

On macOS with Homebrew Python 3.11:

```bash
/opt/homebrew/bin/python3.11 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configure env vars

```bash
cp .env.example .env
```

Then open `.env` and add at least your Devin API key if you want live launches.

```env
DEVIN_API_KEY=replace_me
DEVIN_ORG_ID=
```

### 4. Run the app

```bash
python -m uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000`

## Demo workflow

### Fastest path

1. Import the 6 demo-ready issues
2. Run triage
3. Show the split: 2 safe for Devin, 2 need clarification, 2 senior review
4. Select the two green issues
5. Launch **demo Devin sessions** or **live Devin sessions**
6. Sync runs

### Live Devin workflow

1. Put a valid `DEVIN_API_KEY` in `.env`
2. Restart the server
3. Reload the page and confirm the green config badge says **live Devin launch available**
4. Select issues
5. Click **Launch live Devin sessions**
6. Use **Sync runs** to pull insights back into the dashboard

If live launch fails, the error is stored in the **Error** column in the runs table.

## API routes

- `GET /api/health` — tells you if the app sees your Devin/GitHub config
- `POST /api/import` — import demo or real GitHub issues
- `POST /api/triage` — run triage on all or selected issues
- `POST /api/launch` — create demo or live Devin runs
- `POST /api/sync` — refresh run state from demo/live sessions
- `POST /api/playbook` — create a reusable Devin playbook

## Take-home positioning

The point of this app is not “AI magically fixes all 300 issues.”

The point is:

- identify which issues are safe to automate
- route risky work away from the agent
- launch autonomous work on the right subset
- keep engineering leadership informed with a simple operating dashboard

## Recommended Loom structure

1. Show the stale issue backlog
2. Explain the triage buckets
3. Launch a live or demo Devin run
4. Show the runs table and sync flow
5. Close on next steps: GitHub integration hardening, playbooks, daily sweep, and Slack/Jira routing

## Safety note

Never commit your `.env` file or API keys to GitHub.


## Demo-ready issue pack

This rebuild now includes six intentional issues tuned for the take-home narrative. See `DEMO_ISSUES.md` for the exact bucket breakdown and talking points.
