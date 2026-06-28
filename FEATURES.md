# FEATURES

## User authentication
**Status:** done ✅  
**Priority:** high  
**Note:** Sub-task blocked: Wiring: AuthContext.jsx stores token in memory, axios interceptor attaches Bearer token to all requests  
**Sub-tasks:**
- [~] Backend: User model (models/User.js) with email, password, role fields. bcrypt hashing on save.
- [~] API: POST /api/auth/register, POST /api/auth/login, GET /api/auth/me — JWT issued on login
- [~] Frontend: LoginPage.jsx, RegisterPage.jsx, ProtectedRoute.jsx wrapper component
- [~] Wiring: AuthContext.jsx stores token in memory, axios interceptor attaches Bearer token to all requests

---

## Donor management
**Status:** in_progress 🔄  
**Priority:** high  
**Sub-tasks:**
- [x] Backend: Donor model (models/Donor.js) — name, email, phone, address, createdAt, totalDonated
- [x] API: GET/POST /api/donors, GET/PUT/DELETE /api/donors/:id — auth required
- [x] Frontend: DonorsPage.jsx (table list), DonorForm.jsx (add/edit modal), DonorCard.jsx
- [p] Wiring: services/donors.js axios wrappers, useDonors custom hook for data fetching

---

## Cause and campaign management
**Status:** pending ⏳  
**Priority:** high  
**Sub-tasks:**
- [ ] Backend: Cause model (models/Cause.js) — title, description, goalAmount, raisedAmount, isActive, imageUrl
- [ ] API: GET/POST /api/causes, GET/PUT/DELETE /api/causes/:id, PATCH /api/causes/:id/toggle
- [ ] Frontend: CausesPage.jsx (card grid), CauseForm.jsx (create/edit), CauseCard.jsx (public-facing)
- [ ] Wiring: services/causes.js, update raisedAmount via donation controller hook

---

## Donation recording
**Status:** pending ⏳  
**Priority:** high  
**Sub-tasks:**
- [ ] Backend: Donation model (models/Donation.js) — donor ref, cause ref, amount, type (one-time/recurring), date, note
- [ ] API: GET /api/donations (filterable by donor, cause, date), POST /api/donations
- [ ] Frontend: DonationForm.jsx (amount, cause selector, donor lookup), DonationsPage.jsx (table with filters)
- [ ] Wiring: On POST /api/donations — increment Cause.raisedAmount, increment Donor.totalDonated, trigger receipt email

---

## Student beneficiary profiles
**Status:** pending ⏳  
**Priority:** high  
**Sub-tasks:**
- [ ] Backend: Student model (models/Student.js) — name, school, program, level, sponsorDonor ref, cause ref, status, enrolledAt
- [ ] API: GET/POST /api/students, GET/PUT/DELETE /api/students/:id
- [ ] Frontend: StudentsPage.jsx (searchable list), StudentForm.jsx, StudentProfile.jsx (shows sponsor + cause)
- [ ] Wiring: services/students.js, StudentProfile links to donor profile and cause detail

---

## Donation receipt emails
**Status:** pending ⏳  
**Priority:** medium  
**Sub-tasks:**
- [ ] Backend: config/email.js (nodemailer transporter), receiptTemplate.js (HTML email template with amount, cause, date)
- [ ] API: Internal sendReceipt(donationId) called from donation controller — not a public endpoint
- [ ] Frontend: ReceiptPreview.jsx shown in donor profile history (renders same HTML template)
- [ ] Wiring: POST /api/donations controller calls sendReceipt after saving — async, non-blocking

---

## Admin dashboard
**Status:** pending ⏳  
**Priority:** medium  
**Sub-tasks:**
- [ ] Backend: controllers/dashboard.js — aggregate queries: total raised, donor count, active causes, recent donations
- [ ] API: GET /api/dashboard/stats — returns { totalRaised, donorCount, activeCauses, recentDonations[] }
- [ ] Frontend: DashboardPage.jsx — StatsCards.jsx (4 KPI cards), DonationsChart.jsx (Chart.js bar), RecentTable.jsx
- [ ] Wiring: services/dashboard.js, dashboard polls every 60s via useInterval hook

---

## Report export
**Status:** pending ⏳  
**Priority:** low  
**Sub-tasks:**
- [ ] Backend: controllers/reports.js — query donations by date range + cause, format as CSV using json2csv
- [ ] API: GET /api/reports/donations?from=&to=&causeId= — streams CSV file download
- [ ] Frontend: ReportsPage.jsx — date range pickers, cause filter dropdown, Download CSV button
- [ ] Wiring: axios GET with responseType blob, trigger browser download via URL.createObjectURL

---

## Public donation page
**Status:** pending ⏳  
**Priority:** medium  
**Sub-tasks:**
- [ ] Backend: GET /api/public/causes (no auth), POST /api/public/donate (creates donor if not exists + donation)
- [ ] API: Public routes mounted at /api/public — no JWT middleware
- [ ] Frontend: PublicPage.jsx (landing), PublicCauseCard.jsx, PublicDonateForm.jsx (inline donor info collection)
- [ ] Wiring: PublicDonateForm submits to /api/public/donate, shows success message + triggers receipt email

---

## Role-based access control
**Status:** pending ⏳  
**Priority:** medium  
**Sub-tasks:**
- [ ] Backend: middleware/authorize.js — checks req.user.role against allowed roles array
- [ ] API: Apply authorize(['admin']) to destructive routes (DELETE, PUT on donors/causes/students)
- [ ] Frontend: RoleBadge.jsx, hide admin-only UI elements based on AuthContext role
- [ ] Wiring: Role stored in JWT payload, decoded in auth middleware, passed as req.user.role

---
