# Repository Configuration

DevAgent supports **separate GitHub repos** for backend and frontend.

## Dual-repo mode

Set these GitHub Actions **variables** (Settings → Secrets and variables → Actions → Variables):

```
BACKEND_REPOSITORY=malikmajeed/dms-backend
FRONTEND_REPOSITORY=malikmajeed/dms-frontend
```

Full URLs also work (auto-normalized to `owner/repo`):

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

The workflow uses **`DEVAGENT_GITHUB_TOKEN`** (a Personal Access Token) to access private repos.

### Create the PAT

1. GitHub → **Settings** → **Developer settings** → **Personal access tokens** → **Tokens (classic)**
2. Generate token with **`repo`** scope (required for private repositories)
3. Copy the token

### Add as secret (control repo)

`malikmajeed/dev_agents` → **Settings** → **Secrets and variables** → **Actions** → **New secret**

| Secret name | Value |
|-------------|--------|
| `DEVAGENT_GITHUB_TOKEN` | Your PAT (`ghp_...`) |

The workflow falls back to the automatic `GITHUB_TOKEN` if `DEVAGENT_GITHUB_TOKEN` is not set (mono-repo / public only).

Also enable **Workflow permissions → Read and write** on the control repo.

### Empty backend / frontend repos

If `dms-backend` or `dms-frontend` were created on GitHub with **no README / no first commit**, checkout fails at *"Checking out the ref"*. The workflow now auto-pushes an initial `main` commit when needed. Your PAT must have **`repo`** write access.

## `.gitignore` (control repo)

When using dual-repo mode, ignore the nested checkouts in the control repo:

```
backend/
frontend/
```
