# SonarTrivy — CI Pipeline Training Demo

A deliberately faulty Python application used to demonstrate:

- **SonarQube** — static code analysis (code smells, bugs, vulnerabilities, hotspots, secrets)
- **Trivy** — security scanning (CVEs in packages, secrets in files, OS image vulnerabilities)
- **GitHub Actions** — automated CI pipeline that fails when issues are found

The project has two versions:

| Branch | Purpose |
|---|---|
| `main` | Faulty version — CI pipeline intentionally fails |
| `fix/clean-version` | Fixed version — all issues resolved, CI passes |

---

## Project Structure

```
.
├── app/
│   ├── main.py            # FastAPI app — CORS *, debug=True, /debug/config endpoint
│   ├── database.py        # SQLite setup
│   ├── notes_service.py   # SQL injection, mutable default, ZeroDivision, bare except
│   └── security.py        # Hardcoded secrets, MD5, random token, eval()
├── tests/
│   └── test_app.py        # pytest tests
├── secrets/
│   └── fake-secrets.env   # Fake credentials — intentionally committed for Trivy demo
├── .github/
│   └── workflows/
│       └── ci.yml         # GitHub Actions pipeline
├── Dockerfile             # Old base image (python:3.9.0-slim-buster), copies secrets/
├── sonar-project.properties
├── trivy.yaml
├── pytest.ini
├── requirements.txt       # Old vulnerable package versions
└── requirements-dev.txt
```

---

## Local Setup

```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate     # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt -r requirements-dev.txt

# Run the app
uvicorn app.main:app --reload
# App is now at http://localhost:8000
# Interactive docs at http://localhost:8000/docs
```

---

## Running Tests Locally

```bash
# Run tests with coverage (configured via pytest.ini)
pytest

# Coverage report is written to coverage.xml and printed to terminal
```

---

## SonarQube — Local Scan

Prerequisites: SonarQube running on `http://localhost:9000` (Docker).

```bash
# 1. Generate coverage report first
pytest

# 2. Download and run the SonarQube scanner CLI
# Replace YOUR_TOKEN with a token from SonarQube → My Account → Security
sonar-scanner -Dsonar.token=YOUR_TOKEN
```

After the scan completes, open `http://localhost:9000/projects` to see the results.

### What SonarQube will detect in the faulty version

| Category | Issue | Location |
|---|---|---|
| Vulnerability | Hardcoded secrets (`JWT_SECRET`, `ADMIN_PASSWORD`, `DATABASE_PASSWORD`) | `security.py` |
| Vulnerability | `eval()` — remote code execution | `security.py`, `main.py` |
| Vulnerability | SQL string concatenation — injection | `notes_service.py:search_notes` |
| Hotspot | MD5 used for password hashing — weak algorithm | `security.py:hash_password` |
| Hotspot | `random` used for security token — not cryptographically secure | `security.py:generate_reset_token` |
| Hotspot | CORS `allow_origins=["*"]` — overly permissive | `main.py` |
| Hotspot | `/debug/config` endpoint exposes secrets over HTTP | `main.py` |
| Bug | Mutable default argument `tags=[]` | `notes_service.py:create_note` |
| Bug | Division without zero check → `ZeroDivisionError` | `notes_service.py:calculate_ratio` |
| Bug | Bare `except Exception` swallows all errors silently | `notes_service.py:get_note_by_id` |
| Code Smell | Unused variables (`unused_debug_value`, `temporary_status`) | `notes_service.py` |
| Code Smell | `score = score + 0` — no-op statement | `notes_service.py:calculate_note_score` |
| Code Smell | Cognitive complexity > 15 (deeply nested conditionals) | `notes_service.py:calculate_note_score` |
| Code Smell | `debug=True` in FastAPI constructor | `main.py` |

---

## Trivy — Local Scan

```bash
# Filesystem scan (packages + secrets + misconfig)
trivy fs .

# Save results to a JSON file
trivy fs . --format json --output trivy-fs-report.json

# Docker image scan
docker build -t sonar-trivy-demo:local .
trivy image sonar-trivy-demo:local

# Save image scan results
trivy image sonar-trivy-demo:local --format json --output trivy-image-report.json
```

### What Trivy will detect in the faulty version

| Scanner | Finding | Source |
|---|---|---|
| Vulnerability | `django 2.2.0` — 10+ CVEs (EOL package) | `requirements.txt` |
| Vulnerability | `urllib3 1.23` — CVE-2018-20060, CVE-2019-11324 | `requirements.txt` |
| Vulnerability | `jinja2 2.10.1` — CVE-2019-10906, CVE-2019-8341 | `requirements.txt` |
| Vulnerability | `requests 2.19.1` — CVE-2018-18074 | `requirements.txt` |
| Vulnerability | OS packages in `python:3.9.0-slim-buster` (Debian 10 EOL) | Docker image |
| Secret | AWS Access Key ID pattern | `secrets/fake-secrets.env` |
| Secret | AWS Secret Access Key pattern | `secrets/fake-secrets.env` |
| Secret | GitHub token pattern | `secrets/fake-secrets.env` |
| Secret | Slack webhook URL pattern | `secrets/fake-secrets.env` |
| Secret | Hardcoded password strings | `app/security.py` |

---

## GitHub Actions CI Pipeline

The pipeline has three independent jobs:

```
push / pull_request
        │
        ├── test ──────────────────► generates coverage.xml
        │       │
        │       └── sonarqube ──────► downloads coverage → scans → quality gate check
        │
        └── trivy ──────────────────► fs scan → image build → image scan → upload reports
```

### Pipeline behavior on the faulty version

- `test` job: **passes** (the app runs correctly despite its flaws)
- `sonarqube` job: **fails** at the quality gate (too many vulnerabilities/hotspots)
- `trivy` job: **fails** on HIGH/CRITICAL severity findings in both FS and image scans

### Required GitHub Secrets

Go to your repo → Settings → Secrets and variables → Actions → New repository secret.

| Secret name | Value |
|---|---|
| `SONAR_TOKEN` | Token from SonarQube/SonarCloud → My Account → Security |
| `SONAR_HOST_URL` | `https://sonarcloud.io` (SonarCloud) or your self-hosted URL |

If using SonarCloud, also add `sonar.organization=<your-org-key>` to `sonar-project.properties`.

---

## Fixing Common Issues

### SonarQube quality gate always passes
The default quality gate ("Sonar way") may not catch everything on a first scan. Go to SonarQube → Quality Gates → create a stricter gate that fails on any new vulnerability or security hotspot, then assign it to this project.

### Trivy scan is too slow
The vulnerability DB is downloaded on every run. Add caching to the workflow or run with `--skip-db-update` if the DB was recently updated.

### `docker build` fails with "Dockerfile not found"
Make sure the file is named `Dockerfile` (capital D). On Linux (GitHub Actions runner), the filesystem is case-sensitive.

### SonarQube can't be reached from GitHub Actions
GitHub-hosted runners cannot reach `localhost:9000`. Use SonarCloud, or a self-hosted runner, or run SonarQube as a service container in the workflow.

---

## Screenshots

<!-- Add screenshots after running the pipeline -->

- `docs/sonarqube-dashboard.png` — SonarQube project overview showing issues
- `docs/github-actions-failed.png` — GitHub Actions run showing failed jobs
- `docs/trivy-output.png` — Trivy terminal output with CVE list
