# Project: NGO Donation Management System

## Description
A mid-level donation management system for an NGO that:
- Manages donors and tracks their full donation history
- Supports multiple causes/campaigns that donors can contribute to
- Manages student beneficiaries who are sponsored through donations
- Provides an admin dashboard for NGO staff to oversee all activity
- Sends automated receipt emails to donors after each donation
- Has a public-facing donation page so anyone can donate to a cause
- a feature to add students with their necessary details such as name age class profile and stuff. and they'll appear to donor in a seaprate page. 


## Scale
- Mid-level: not enterprise (no microservices, no event queues, no payment gateway)
- Expected users: 5–20 admin/staff, hundreds of donor records, dozens of students
- Single-tenant (one NGO instance)
- Manual donation recording (no Stripe/PayPal integration)

## Tech Stack
See TECHSTACK.md for the full stack details, folder structure, and conventions.

- **Backend:** Node.js + Express + PostgreSQL (Sequelize) — layered as routes → controllers → services → models
- **Frontend:** Next.js 14 (App Router, JavaScript) + TanStack Query + Zustand + Axios (with interceptors)
- **Validation:** Zod / Joi on both backend and frontend
- **Auth:** JWT + bcrypt
- **Email (donor receipts):** Nodemailer via Gmail SMTP
- **Styling:** Tailwind CSS

## Environment Variables

### Backend (.env)
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

### Frontend (.env)
```
NEXT_PUBLIC_API_URL=http://localhost:3001/api
NEXT_PUBLIC_API_BASE_URL=<your-value>
```
