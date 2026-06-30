# Tech Stack

> Maintained by DevAgent and editable manually. The agent reads this before generating code.

---

## Framework

| Layer | Choice | Notes |
|-------|--------|-------|
| Framework | Next.js 14 (App Router) | JavaScript only — no TypeScript |
| Database | PostgreSQL | via Sequelize ORM |
| Auth | JWT (jsonwebtoken) | + bcryptjs for hashing |
| Email | Nodemailer | SMTP via Gmail |
| Validation | Zod | request bodies, forms |
| Styling | Tailwind CSS | utility-first |
| Charts | Chart.js + react-chartjs-2 | dashboard stats (when needed) |

---

## Architecture

Single Next.js app — API routes and UI in one repo.

```
HTTP Request
    ↓
app/api/**/route.js     ← Route Handlers (thin: parse request, call service)
    ↓
services/               ← business logic (no req/res)
    ↓
models/                 ← Sequelize models
    ↓
lib/db.js               ← Sequelize singleton
    ↓
PostgreSQL
```

**UI flow:**

```
app/**/page.js          ← pages (server or client components)
    ↓
hooks/                  ← data fetching hooks (fetch to /api/*)
    ↓
components/             ← reusable UI
```

| Layer | Responsibility |
|-------|----------------|
| **Route Handlers** | `app/api/.../route.js` — parse request, call service, return JSON |
| **Services** | Business logic, orchestration, side effects (email, transactions) |
| **Models** | Sequelize definitions, associations, schema |
| **Pages/Components** | UI only — fetch via hooks or server components |
| **lib/** | DB connection, auth helpers, shared utilities |

---

## Packages

```json
{
  "dependencies": {
    "next": "^14.2.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "sequelize": "^6.37.0",
    "pg": "^8.11.3",
    "pg-hstore": "^2.3.4",
    "bcryptjs": "^2.4.3",
    "jsonwebtoken": "^9.0.2",
    "zod": "^3.22.4",
    "nodemailer": "^6.9.7"
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

---

## Folder Structure

```
app/
  api/                    ← Route Handlers (app/api/donors/route.js)
  (auth)/                 ← login, register route groups
  (dashboard)/            ← protected admin routes
  layout.js
  page.js
  globals.css
components/               ← reusable UI
hooks/                    ← useDonors(), useAuth(), etc.
lib/
  db.js                   ← Sequelize singleton
  auth.js                 ← JWT verify/sign helpers
models/                   ← Sequelize model definitions
services/                 ← business logic per domain
middleware.js             ← optional auth middleware
public/
next.config.js
tailwind.config.js
postcss.config.js
.env.example
package.json
dev_agent/                ← DevAgent Python code (do not edit from features)
FEATURES.md               ← auto-generated from PROJECT.md; editable
PROJECT.md
```

---

## Conventions

- **JavaScript only** — `.js` / `.jsx`, no TypeScript
- Route Handlers export `GET`, `POST`, `PUT`, `DELETE` as named async functions
- Services must not access `req` / `res` — receive plain data, return data or throw
- All DB access through Sequelize inside services
- Validate mutating endpoints with Zod before processing
- Use `fetch('/api/...')` from client hooks; no separate Express server
- Tailwind for all styling

---

## Deployment

| Environment | Platform | Trigger |
|-------------|----------|---------|
| Production | Vercel | push to `main` |

Connect this GitHub repo to Vercel. Framework: **Next.js**, root directory: **`.`**

Set environment variables in Vercel: `DATABASE_URL`, `JWT_SECRET`, email vars.

---

## DevAgent

| Layer | Choice |
|-------|--------|
| Agent language | Python 3.11 |
| AI model | HuggingFace Router API |
| Runner | GitHub Actions (hourly) |
| Git flow | `feat/*` branch → auto-merge PR to `main` |
| Features | Auto-planned from `PROJECT.md`, stored in `FEATURES.md` |

---

_Last updated by: DevAgent_
