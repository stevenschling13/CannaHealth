# CannaHealth

This repository contains the CannaHealth analytics backend and the accompanying
frontend used to review analysis snapshots. The project relies on standard
Python, Node.js, and container tooling; no offline shims are bundled in the
repository.

## Prerequisites

Install the following tools before working with the project:

- Docker and Docker Compose
- Python 3.11 or newer with `pip`
- Node.js 18+ with `npm`
- Git and the GitHub CLI (`gh`)
- Alembic

After installing the prerequisites, verify each binary with the corresponding
`--version` command to ensure they are available on your `PATH`.

## Backend setup

1. Create and activate a virtual environment.
2. Install the Python dependencies:
   ```bash
   pip install -r web/backend/requirements.txt
   ```
3. Export the database URL, for example:
   ```bash
   export DATABASE_URL=postgresql+asyncpg://canna:canna@localhost:5432/canna
   ```
4. Run the database migrations from the backend directory:
   ```bash
   cd web/backend
   alembic upgrade head
   ```
5. Execute the test suite:
   ```bash
   pytest -q
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
3. Configure `NEXT_PUBLIC_API_BASE_URL` (Next.js) or `REACT_APP_API_BASE_URL`
   (Create React App) to point at the backend's public URL. If no environment
   variable is provided the UI defaults to `http://localhost:8000`.
4. Start the development server using your preferred tooling (for example Vite
   or Next.js) once the API base URL is configured.

## Model validation

Validate the model manifest prior to committing model changes:

```bash
python tools/validate_model.py --model-dir model
```
