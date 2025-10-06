# CannaHealth

This repository contains the CannaHealth analytics backend and the accompanying
frontend used to review analysis snapshots. The backend now operates entirely on
the Python standard library so that it can run in restricted environments
without needing to download external dependencies.

## Prerequisites

Install the following tools before working with the project:

- Python 3.11 or newer
- Node.js 18+ with `npm`
- Git

## Backend setup

1. Create and activate a virtual environment.
2. No external Python packages are required. The backend depends solely on the
   standard library.
3. Execute the test suite:
   ```bash
   python -m unittest discover web/backend/tests
   ```

## Frontend setup

1. Install the Node.js dependencies:
   ```bash
   cd web/frontend
   npm install
   ```
2. Run the lint checks and tests:
   ```bash
   npm run lint
   npm test
   ```
3. Configure `NEXT_PUBLIC_API_BASE_URL` to point at the backend's public URL.
   If no environment variable is provided the UI defaults to
   `http://localhost:8000`.
4. Run a full deployment audit locally (optional, mirrors the CI workflow):
   ```bash
   python tools/audit_deployment.py
   ```
5. Build and start the Next.js frontend:
   ```bash
   npm run dev
   # or
   npm run build
   npm run start
   ```

## Model validation

Validate the model manifest prior to committing model changes:

```bash
python tools/validate_model.py --model-dir model
```

## Deployment audit tooling

The `tools/audit_deployment.py` script inspects the GitHub Actions workflows
and recent log files to ensure the automated checks exercise the build, test,
and lint steps required for production readiness. The `deployment-audit`
workflow runs this script with the `--check` flag so that CI fails if any of
the expected commands disappear from the pipeline.
