"""
Planner — generates FEATURES.md from PROJECT.md + TECHSTACK.md.
"""

import os, re
from pathlib import Path
from utils import call_hf, log

PLANNER_PROMPT = """You are a senior software architect. Generate a mid-level feature list for this project.

Rules:
- 8–14 features total (not enterprise, not trivial)
- Each feature has exactly 4 sub-tasks: Backend, API, Frontend, Wiring
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
- [ ] Backend: <mongoose model or business logic — name the file>
- [ ] API: <express routes — list the HTTP methods and paths>
- [ ] Frontend: <react page/component — name the file>
- [ ] Wiring: <how backend connects to frontend — axios call, context, etc.>

---

Project description:
{description}
"""


def generate_features(project_description: str, techstack: str, output_path: Path):
    log("Planner: generating feature list...")
    prompt = PLANNER_PROMPT.format(
        description=project_description.strip(),
        techstack=techstack[:1000] if techstack else "Node.js + Express + React",
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
- [ ] Backend: User model (models/User.js) with email, password, role fields. bcrypt hashing on save.
- [ ] API: POST /api/auth/register, POST /api/auth/login, GET /api/auth/me — JWT issued on login
- [ ] Frontend: LoginPage.jsx, RegisterPage.jsx, ProtectedRoute.jsx wrapper component
- [ ] Wiring: AuthContext.jsx stores token in memory, axios interceptor attaches Bearer token to all requests

---

## Donor management
**Status:** pending  
**Priority:** high  
**Sub-tasks:**
- [ ] Backend: Donor model (models/Donor.js) — name, email, phone, address, createdAt, totalDonated
- [ ] API: GET/POST /api/donors, GET/PUT/DELETE /api/donors/:id — auth required
- [ ] Frontend: DonorsPage.jsx (table list), DonorForm.jsx (add/edit modal), DonorCard.jsx
- [ ] Wiring: services/donors.js axios wrappers, useDonors custom hook for data fetching

---

## Cause and campaign management
**Status:** pending  
**Priority:** high  
**Sub-tasks:**
- [ ] Backend: Cause model (models/Cause.js) — title, description, goalAmount, raisedAmount, isActive, imageUrl
- [ ] API: GET/POST /api/causes, GET/PUT/DELETE /api/causes/:id, PATCH /api/causes/:id/toggle
- [ ] Frontend: CausesPage.jsx (card grid), CauseForm.jsx (create/edit), CauseCard.jsx (public-facing)
- [ ] Wiring: services/causes.js, update raisedAmount via donation controller hook

---

## Donation recording
**Status:** pending  
**Priority:** high  
**Sub-tasks:**
- [ ] Backend: Donation model (models/Donation.js) — donor ref, cause ref, amount, type (one-time/recurring), date, note
- [ ] API: GET /api/donations (filterable by donor, cause, date), POST /api/donations
- [ ] Frontend: DonationForm.jsx (amount, cause selector, donor lookup), DonationsPage.jsx (table with filters)
- [ ] Wiring: On POST /api/donations — increment Cause.raisedAmount, increment Donor.totalDonated, trigger receipt email

---

## Student beneficiary profiles
**Status:** pending  
**Priority:** high  
**Sub-tasks:**
- [ ] Backend: Student model (models/Student.js) — name, school, program, level, sponsorDonor ref, cause ref, status, enrolledAt
- [ ] API: GET/POST /api/students, GET/PUT/DELETE /api/students/:id
- [ ] Frontend: StudentsPage.jsx (searchable list), StudentForm.jsx, StudentProfile.jsx (shows sponsor + cause)
- [ ] Wiring: services/students.js, StudentProfile links to donor profile and cause detail

---

## Donation receipt emails
**Status:** pending  
**Priority:** medium  
**Sub-tasks:**
- [ ] Backend: config/email.js (nodemailer transporter), receiptTemplate.js (HTML email template with amount, cause, date)
- [ ] API: Internal sendReceipt(donationId) called from donation controller — not a public endpoint
- [ ] Frontend: ReceiptPreview.jsx shown in donor profile history (renders same HTML template)
- [ ] Wiring: POST /api/donations controller calls sendReceipt after saving — async, non-blocking

---

## Admin dashboard
**Status:** pending  
**Priority:** medium  
**Sub-tasks:**
- [ ] Backend: controllers/dashboard.js — aggregate queries: total raised, donor count, active causes, recent donations
- [ ] API: GET /api/dashboard/stats — returns { totalRaised, donorCount, activeCauses, recentDonations[] }
- [ ] Frontend: DashboardPage.jsx — StatsCards.jsx (4 KPI cards), DonationsChart.jsx (Chart.js bar), RecentTable.jsx
- [ ] Wiring: services/dashboard.js, dashboard polls every 60s via useInterval hook

---

## Report export
**Status:** pending  
**Priority:** low  
**Sub-tasks:**
- [ ] Backend: controllers/reports.js — query donations by date range + cause, format as CSV using json2csv
- [ ] API: GET /api/reports/donations?from=&to=&causeId= — streams CSV file download
- [ ] Frontend: ReportsPage.jsx — date range pickers, cause filter dropdown, Download CSV button
- [ ] Wiring: axios GET with responseType blob, trigger browser download via URL.createObjectURL

---

## Public donation page
**Status:** pending  
**Priority:** medium  
**Sub-tasks:**
- [ ] Backend: GET /api/public/causes (no auth), POST /api/public/donate (creates donor if not exists + donation)
- [ ] API: Public routes mounted at /api/public — no JWT middleware
- [ ] Frontend: PublicPage.jsx (landing), PublicCauseCard.jsx, PublicDonateForm.jsx (inline donor info collection)
- [ ] Wiring: PublicDonateForm submits to /api/public/donate, shows success message + triggers receipt email

---

## Role-based access control
**Status:** pending  
**Priority:** medium  
**Sub-tasks:**
- [ ] Backend: middleware/authorize.js — checks req.user.role against allowed roles array
- [ ] API: Apply authorize(['admin']) to destructive routes (DELETE, PUT on donors/causes/students)
- [ ] Frontend: RoleBadge.jsx, hide admin-only UI elements based on AuthContext role
- [ ] Wiring: Role stored in JWT payload, decoded in auth middleware, passed as req.user.role

---
"""
