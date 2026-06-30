# Project: NGO Donation Management System

## Description
A mid-level donation management system for an NGO that:
- Manages donors and tracks their full donation history
- Supports multiple causes/campaigns that donors can contribute to
- Manages student beneficiaries who are sponsored through donations
- Provides an admin dashboard for NGO staff to oversee all activity
- Sends automated receipt emails to donors after each donation
- Has a public-facing donation page so anyone can donate to a cause
- A feature to add students with their necessary details (name, age, class, profile, etc.) — they appear to donors on a separate page

## Scale
- Mid-level: not enterprise (no microservices, no event queues, no payment gateway)
- Expected users: 5–20 admin/staff, hundreds of donor records, dozens of students
- Single-tenant (one NGO instance)
- Manual donation recording (no Stripe/PayPal integration)

## Architecture
Single **Next.js 14** full-stack app (App Router, JavaScript) in this repo.

- **API:** Next.js Route Handlers (`app/api/**/route.js`)
- **Database:** PostgreSQL via Sequelize (`models/`, `lib/db.js`)
- **UI:** React pages and components (`app/`, `components/`)
- **Auth:** JWT + bcrypt
- **Email:** Nodemailer via Gmail SMTP
- **Styling:** Tailwind CSS
- **Deploy:** Vercel (connect this repo, root `.`)

See [TECHSTACK.md](TECHSTACK.md) for folder structure and conventions.

## Environment Variables

See `.env.example` in the repo root:

```
DATABASE_URL=postgresql://user:pass@localhost:5432/ngo
JWT_SECRET=replace-with-long-random-string
JWT_EXPIRES_IN=7d
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=465
EMAIL_USER=ngo@gmail.com
EMAIL_PASS=gmail-app-password
```

## Features
DevAgent auto-generates [FEATURES.md](FEATURES.md) from `PROJECT.md` on the first run. You can edit that file anytime to add, remove, or reprioritize features. The agent implements one sub-task per hourly run and auto-merges each completed feature to `main`.
