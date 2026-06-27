# Repository Configuration

DevAgent supports **separate GitHub repos** for backend and frontend.

## Dual-repo mode

Set these GitHub Actions **variables** (Settings → Secrets and variables → Actions → Variables):

```
BACKEND_REPOSITORY=https://github.com/malikmajeed/dms-backend.git
FRONTEND_REPOSITORY=https://github.com/malikmajeed/dms-frontend.git
```

Or uncomment and fill in below (env vars take precedence):

```
# BACKEND_REPOSITORY=your-org/ngo-backend
# FRONTEND_REPOSITORY=your-org/ngo-frontend
```

## Layout

| Role | What lives here | GitHub slug |
|------|-----------------|-------------|
| **Control** (this repo) | `dev_agent/`, `PROJECT.md`, `FEATURES.md`, `PROGRESS.md` | same repo that runs the workflow |
| **Backend** | Express API, models, routes — checked out to `backend/` | `your-org/ngo-backend` |
| **Frontend** | Next.js app — checked out to `frontend/` | `your-org/ngo-frontend` |

## Mono-repo mode

Leave `BACKEND_REPOSITORY` and `FRONTEND_REPOSITORY` **empty**. DevAgent commits everything to this repo under `backend/` and `frontend/` folders.

## Permissions

The `GITHUB_TOKEN` must be able to push and open PRs on all three repos. For org repos, enable **Workflow permissions → Read and write** and allow access to organization repositories.

## `.gitignore` (control repo)

When using dual-repo mode, ignore the nested checkouts in the control repo:

```
backend/
frontend/
```
