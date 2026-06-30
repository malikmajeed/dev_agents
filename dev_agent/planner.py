"""
Planner — generates FEATURES.md from PROJECT.md + TECHSTACK.md.
"""

import os, re
from pathlib import Path
from utils import call_hf, log

PLANNER_PROMPT = """You are a senior software architect. Generate a mid-level feature list for this project.

Rules:
- 8–14 features total (not enterprise, not trivial)
- Each feature has exactly 4 sub-tasks: Database, API, UI, Integration
- Be specific — name actual files, routes, components
- Output ONLY valid markdown in the exact format below — no preamble, no explanation

Tech stack in use:
{techstack}

---

Output format (repeat for each feature):

# FEATURES

## [Feature Name]
**Status:** pending  
**Priority:** high|medium|low  
**Sub-tasks:**
- [ ] Database: <Sequelize model — name the file in models/>
- [ ] API: <Next.js route handler — app/api/.../route.js>
- [ ] UI: <page or component — app/.../page.js or components/>
- [ ] Integration: <hooks, services, middleware wiring>

---

Project description:
{description}
"""


def generate_features(project_description: str, techstack: str, output_path: Path):
    log("Planner: generating feature list...")
    prompt = PLANNER_PROMPT.format(
        description=project_description.strip(),
        techstack=techstack[:1000] if techstack else "Next.js 14 + Sequelize + PostgreSQL",
    )
    response = call_hf(prompt, max_tokens=2500)

    if not response or len(response.strip()) < 100:
        log("Planner: model returned short/empty response — using NGO fallback")
        response = _ngo_fallback()

    if "# FEATURES" not in response:
        response = "# FEATURES\n\n" + response

    output_path.write_text(response.strip() + "\n")
    log(f"Planner: wrote {output_path}")


def _ngo_fallback() -> str:
    return """# FEATURES

## User authentication
**Status:** pending  
**Priority:** high  
**Sub-tasks:**
- [ ] Database: User model (models/User.js) — email, passwordHash, role. bcrypt on create.
- [ ] API: app/api/auth/register/route.js (POST), app/api/auth/login/route.js (POST), app/api/auth/me/route.js (GET)
- [ ] UI: app/(auth)/login/page.js, app/(auth)/register/page.js
- [ ] Integration: lib/auth.js JWT helpers, hooks/useAuth.js, middleware for protected routes

---

## Donor management
**Status:** pending  
**Priority:** high  
**Sub-tasks:**
- [ ] Database: Donor model (models/Donor.js) — name, email, phone, address, totalDonated
- [ ] API: app/api/donors/route.js (GET, POST), app/api/donors/[id]/route.js (GET, PUT, DELETE)
- [ ] UI: app/(dashboard)/donors/page.js — table list + add/edit modal
- [ ] Integration: services/donors.js + hooks/useDonors.js wired to API

---

## Cause and campaign management
**Status:** pending  
**Priority:** high  
**Sub-tasks:**
- [ ] Database: Cause model (models/Cause.js) — title, description, goalAmount, raisedAmount, isActive
- [ ] API: app/api/causes/route.js (GET, POST), app/api/causes/[id]/route.js (GET, PUT, DELETE, PATCH toggle)
- [ ] UI: app/(dashboard)/causes/page.js — card grid + create/edit form
- [ ] Integration: services/causes.js + hooks/useCauses.js; update raisedAmount from donation service

---

## Donation recording
**Status:** pending  
**Priority:** high  
**Sub-tasks:**
- [ ] Database: Donation model (models/Donation.js) — donorId, causeId, amount, type, date, note
- [ ] API: app/api/donations/route.js (GET with filters, POST)
- [ ] UI: app/(dashboard)/donations/page.js — DonationForm + filterable table
- [ ] Integration: services/donations.js — increment Cause.raisedAmount and Donor.totalDonated on create

---

## Student beneficiary profiles
**Status:** pending  
**Priority:** high  
**Sub-tasks:**
- [ ] Database: Student model (models/Student.js) — name, age, class, profile, sponsorDonorId, causeId, status
- [ ] API: app/api/students/route.js (GET, POST), app/api/students/[id]/route.js (GET, PUT, DELETE)
- [ ] UI: app/(dashboard)/students/page.js + public app/students/page.js for donor view
- [ ] Integration: services/students.js + hooks/useStudents.js

---

## Donation receipt emails
**Status:** pending  
**Priority:** medium  
**Sub-tasks:**
- [ ] Database: (uses Donation model) — no new model
- [ ] API: lib/email.js sendReceipt(donationId) called from donation service — not a public route
- [ ] UI: components/ReceiptPreview.js — preview in donor history
- [ ] Integration: services/donations.js calls sendReceipt after POST — async, non-blocking

---

## Admin dashboard
**Status:** pending  
**Priority:** medium  
**Sub-tasks:**
- [ ] Database: aggregate queries only — no new model
- [ ] API: app/api/dashboard/stats/route.js (GET) — totalRaised, donorCount, activeCauses, recentDonations
- [ ] UI: app/(dashboard)/page.js — KPI cards + chart + recent donations table
- [ ] Integration: hooks/useDashboard.js polling stats every 60s

---

## Report export
**Status:** pending  
**Priority:** low  
**Sub-tasks:**
- [ ] Database: query donations by date range — no new model
- [ ] API: app/api/reports/donations/route.js (GET) — CSV download with from, to, causeId params
- [ ] UI: app/(dashboard)/reports/page.js — date pickers, cause filter, download button
- [ ] Integration: hooks/useReports.js — fetch blob and trigger browser download

---

## Public donation page
**Status:** pending  
**Priority:** medium  
**Sub-tasks:**
- [ ] Database: (uses Donor, Donation, Cause) — no new model
- [ ] API: app/api/public/causes/route.js (GET), app/api/public/donate/route.js (POST, no auth)
- [ ] UI: app/(public)/donate/page.js — cause cards + inline donate form
- [ ] Integration: hooks/usePublicDonate.js — submit to public API, show success + trigger receipt

---

## Role-based access control
**Status:** pending  
**Priority:** medium  
**Sub-tasks:**
- [ ] Database: role field on User model (admin|staff)
- [ ] API: lib/authorize.js — check role on destructive routes in route handlers
- [ ] UI: components/RoleBadge.js — hide admin-only actions in dashboard
- [ ] Integration: middleware.js or layout checks role from JWT for /dashboard routes

---
"""
