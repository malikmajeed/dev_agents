# Tech Stack

> This file is maintained by DevAgent and updated as the project evolves.
> You can also edit it manually — the agent will respect your changes.

---

## Backend

| Layer | Choice | Notes |
|-------|--------|-------|
| Runtime | Node.js 20 | LTS |
| Framework | Express 4 | REST API |
| Database | PostgreSQL | via Sequelize ORM |
| Auth | JWT (jsonwebtoken) / Cookies | + bcrypt for hashing |
| Email | Nodemailer | SMTP via Gmail |
| Validation | Zod (preferred) / Joi | request body, params, query validation |
| Environment | dotenv | .env file loading |
| Dev server | nodemon | auto-restart on change |

### Backend Architecture

Follow a strict layered flow — **routes → controllers → services → models**. Do not put business logic in routes or controllers.

| Layer | Responsibility |
|-------|----------------|
| **Routes** | Mount endpoints, apply middleware (auth, validation), delegate to controllers |
| **Controllers** | Parse request, call the appropriate service, shape HTTP response (status + JSON) |
| **Services** | All business logic, orchestration, and side effects (email, transactions) |
| **Models** | Sequelize model definitions, associations, DB schema only |
| **Middleware** | Auth, validation, error handling — reusable cross-cutting concerns |

```
HTTP Request
    ↓
routes/          ← define path + middleware chain
    ↓
controllers/     ← thin: extract input, call service, return response
    ↓
services/        ← business logic lives here
    ↓
models/          ← Sequelize models + DB access
    ↓
PostgreSQL
```

### Backend Packages
```json
{
  "dependencies": {
    "express": "^4.18.2",
    "sequelize": "^6.37.0",
    "pg": "^8.11.3",
    "pg-hstore": "^2.3.4",
    "jsonwebtoken": "^9.0.2",
    "bcryptjs": "^2.4.3",
    "nodemailer": "^6.9.7",
    "zod": "^3.22.4",
    "dotenv": "^16.3.1",
    "cors": "^2.8.5",
    "cookie-parser": "^1.4.6"
  },
  "devDependencies": {
    "nodemon": "^3.0.2",
    "sequelize-cli": "^6.6.2"
  }
}
```

> Use **Joi** instead of Zod on the backend if the team prefers — same role, pick one and stay consistent.

### Backend Folder Structure
```
backend/
  src/
    models/           ← Sequelize model definitions + associations
    migrations/       ← Sequelize migrations (schema changes)
    seeders/          ← optional seed data
    routes/           ← Express routers (mounted at /api/*)
    controllers/      ← thin HTTP handlers (call services, return responses)
    services/         ← business logic (donations, donors, auth, email, etc.)
    middleware/       ← auth.js, validate.js, errorHandler.js
    validators/       ← Zod/Joi schemas per resource (donor, donation, auth, etc.)
    config/           ← db.js (Sequelize + Postgres), email.js
    utils/            ← shared helpers (ApiError, asyncHandler, etc.)
  server.js           ← entry point
  .env.example        ← env var template
  package.json
```

### Backend Conventions

- Controllers must **not** contain business logic — only call services and map results to HTTP.
- Services must **not** access `req` / `res` — receive plain data, return plain data or throw errors.
- All DB access goes through **Sequelize models** inside services (or dedicated repository helpers if needed).
- Validate every mutating endpoint with **Zod/Joi** in middleware before the controller runs.
- Use a centralized **error handler** middleware; services throw typed errors, controllers don't catch unless transforming.

---

## Frontend

| Layer | Choice | Notes |
|-------|--------|-------|
| Framework | Next.js 14 (App Router) | **JavaScript** — no TypeScript |
| HTTP | Axios | centralized instance with interceptors |
| Data fetching | TanStack Query (React Query) | server state, caching, mutations |
| Client state | Zustand | auth session, UI state, global stores |
| Validation | Zod (preferred) / Joi | forms, API payloads before send |
| Styling | Tailwind CSS | utility-first; maintain consistent UI tokens |
| Charts | Chart.js + react-chartjs-2 | dashboard stats |

### Frontend Architecture

All API traffic flows through a single pipeline — **never call Axios directly from pages or components**.

```
Page / Component
    ↓
hooks/              ← useDonors(), useCreateDonation() — TanStack Query wrappers
    ↓
services/api/       ← apiClient (Axios) + resource functions (donors.js, donations.js)
    ↓
interceptors        ← attach token, handle 401, normalize errors
    ↓
Backend /api/*
```

| Layer | Responsibility |
|-------|----------------|
| **Pages / Components** | UI only — render data, dispatch actions via hooks |
| **Hooks** | TanStack Query `useQuery` / `useMutation` wrappers per domain |
| **Services** | Axios instance + per-resource API functions |
| **Interceptors** | Request: attach JWT/cookies; Response: refresh auth, redirect on 401, unwrap errors |
| **Stores (Zustand)** | Auth user, tokens, UI flags — not server-fetched lists (those belong in TanStack Query) |
| **Validators** | Zod/Joi schemas shared pattern for form validation before mutation |

### Frontend Packages
```json
{
  "dependencies": {
    "next": "^14.2.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "axios": "^1.6.2",
    "@tanstack/react-query": "^5.28.0",
    "zustand": "^4.5.0",
    "zod": "^3.22.4",
    "chart.js": "^4.4.0",
    "react-chartjs-2": "^5.2.0"
  },
  "devDependencies": {
    "tailwindcss": "^3.4.0",
    "postcss": "^8.4.35",
    "autoprefixer": "^10.4.17",
    "eslint": "^8.57.0",
    "eslint-config-next": "^14.2.0"
  }
}
```

### Frontend Folder Structure
```
frontend/
  app/                    ← Next.js App Router pages and layouts
    (auth)/               ← login, register route groups
    (dashboard)/          ← protected admin routes
    layout.js
    page.js
  components/             ← reusable UI (Button, Card, Table, Modal, etc.)
  hooks/                  ← TanStack Query hooks (useDonors, useDonations, useAuth)
  services/
    api/
      client.js           ← Axios instance + request/response interceptors
      donors.js           ← donor API functions
      donations.js        ← donation API functions
      auth.js             ← login, logout, me
  stores/                 ← Zustand stores (authStore.js, uiStore.js)
  validators/             ← Zod/Joi schemas for forms
  lib/                    ← queryClient setup, constants, helpers
  styles/
    globals.css           ← Tailwind directives + base styles
  public/
  next.config.js
  tailwind.config.js
  postcss.config.js
  .env.example
  package.json
```

### Frontend Conventions

- **JavaScript only** — `.js` / `.jsx` files, no TypeScript.
- **Tailwind CSS** for all styling — avoid CSS Modules unless a third-party component requires it.
- Configure Axios **request interceptor** to attach JWT (header or cookie) on every call.
- Configure Axios **response interceptor** to handle 401 (clear auth store, redirect to login) and normalize error payloads.
- Wrap the app in **QueryClientProvider**; each domain gets a custom hook in `hooks/`.
- Use **Zustand** for auth and ephemeral UI state; use **TanStack Query** for all server data (donors, donations, students, stats).
- Validate forms with **Zod/Joi** before calling mutations.

---

## Deployment

| Environment | Platform | Trigger |
|-------------|----------|---------|
| Preview (per PR) | Vercel | auto on PR open |
| Staging | Vercel | auto on merge to `staging` |
| Production | Vercel | manual PR: staging → main |

### Vercel Config
```json
{
  "projects": [
    {
      "name": "ngo-frontend",
      "root": "frontend",
      "framework": "nextjs"
    },
    {
      "name": "ngo-backend",
      "root": "backend",
      "framework": null,
      "buildCommand": "npm install",
      "outputDirectory": "."
    }
  ]
}
```

### Environment Variables

**Backend (.env)**
```
DATABASE_URL=postgresql://user:pass@localhost:5432/ngo
JWT_SECRET=replace-with-long-random-string
JWT_EXPIRES_IN=7d
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=465
EMAIL_USER=ngo@gmail.com
EMAIL_PASS=gmail-app-password
CLIENT_URL=http://localhost:3000
PORT=3001
```

**Frontend (.env)**
```
NEXT_PUBLIC_API_URL=http://localhost:3001/api
```

---

## DevAgent

| Layer | Choice |
|-------|--------|
| Agent language | Python 3.11 |
| AI model | HuggingFace Inference API (free) |
| Default model | mistralai/Mistral-7B-Instruct-v0.3 |
| Runner | GitHub Actions (free tier) |
| Schedule | Every hour (GitHub cron) |
| PR management | GitHub REST API |
| Notifications | Gmail SMTP + IMAP |

---

_Last updated by: DevAgent_  
_To update manually: edit this file and commit. The agent reads it before generating any code._
