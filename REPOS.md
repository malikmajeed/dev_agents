# Repository Layout

DevAgent runs in **mono-repo mode only** — one Next.js full-stack app in this repository.

## What lives here

| Path | Purpose |
|------|---------|
| `dev_agent/` | Python agent (orchestrator, coder, healer) |
| `app/` | Next.js App Router pages and API routes |
| `models/`, `lib/`, `services/` | Sequelize + business logic |
| `FEATURES.md` | Auto-generated from `PROJECT.md` on first run — editable anytime |
| `PROJECT.md` | Project description |
| `TECHSTACK.md` | Stack conventions the agent follows |

## Git flow

1. DevAgent reads `PROJECT.md` and generates `FEATURES.md` (if missing)
2. You can edit `FEATURES.md` to add or change features
3. DevAgent runs hourly, implements one sub-task per run on `feat/{feature-slug}`
3. When a feature's sub-tasks are done, it opens a PR and **auto-merges to `main`**
4. You deploy `main` to Vercel

## GitHub secrets

| Secret | Purpose |
|--------|---------|
| `HF_API_KEY` | HuggingFace Inference |
| `GMAIL_USER` / `GMAIL_APP_PASS` | Email notifications |
| `DEVAGENT_GITHUB_TOKEN` | Optional PAT with `repo` scope (falls back to `GITHUB_TOKEN`) |

Enable **Workflow permissions → Read and write** on this repo.

## Vercel

Connect this repo. Framework: Next.js. Root: `.`

Set `DATABASE_URL`, `JWT_SECRET`, and email env vars in the Vercel dashboard.
