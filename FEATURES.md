# FEATURES

## Donor Management
**Status:** pending  
**Priority:** high  
**Sub-tasks:**
- [ ] Database: `models/donor.js`
- [ ] API: `app/api/donors/route.js`
- [ ] UI: `app/admin/donors/page.js`
- [ ] Integration: `services/donorService.js` (hooks `hooks/useDonors.js` and controller wiring)

---

## Cause (Campaign) Management
**Status:** pending  
**Priority:** high  
**Sub-tasks:**
- [ ] Database: `models/cause.js`
- [ ] API: `app/api/causes/route.js`
- [ ] UI: `app/admin/causes/page.js`
- [ ] Integration: `services/causeService.js` (hook `hooks/useCauses.js`)

---

## Donation Recording
**Status:** pending  
**Priority:** high  
**Sub-tasks:**
- [ ] Database: `models/donation.js`
- [ ] API: `app/api/donations/route.js`
- [ ] UI: `app/admin/donations/page.js`
- [ ] Integration: `services/donationService.js` (includes email receipt trigger)

---

## Student Beneficiary Management
**Status:** pending  
**Priority:** high  
**Sub-tasks:**
- [ ] Database: `models/student.js`
- [ ] API: `app/api/students/route.js`
- [ ] UI: `app/admin/students/page.js`
- [ ] Integration: `services/studentService.js` (hook `hooks/useStudents.js`)

---

## Public Donation Page
**Status:** pending  
**Priority:** high  
**Sub-tasks:**
- [ ] Database: `models/donation.js` (reuse)
- [ ] API: `app/api/public/donate/route.js`
- [ ] UI: `app/public/donate/page.js`
- [ ] Integration: `components/DonateForm.jsx` + `hooks/useDonate.js`

---

## Authentication (Login & Registration)
**Status:** pending  
**Priority:** high  
**Sub-tasks:**
- [ ] Database: `models/user.js`
- [ ] API: `app/api/auth/login/route.js` & `app/api/auth/register/route.js`
- [ ] UI: `app/auth/login/page.js` & `app/auth/register/page.js`
- [ ] Integration: `lib/jwt.js` + `middleware/authMiddleware.js`

---

## Email Receipt Service
**Status:** pending  
**Priority:** medium  
**Sub-tasks:**
- [ ] Database: `models/emailLog.js`
- [ ] API: `app/api/email/receipt/route.js`
- [ ] UI: `app/admin/email-logs/page.js`
- [ ] Integration: `lib/email.js` (Nodemailer config) + `services/emailService.js`

---

## Admin Dashboard & Statistics
**Status:** pending  
**Priority:** medium  
**Sub-tasks:**
- [ ] Database: (no new model, uses aggregates)
- [ ] API: `app/api/dashboard/stats/route.js`
- [ ] UI: `app/admin/dashboard/page.js`
- [ ] Integration: `components/StatsChart.jsx` + `hooks/useStats.js`

---

## Reporting & CSV Export
**Status:** pending  
**Priority:** medium  
**Sub-tasks:**
- [ ] Database: (leverages existing models)
- [ ] API: `app/api/reports/donations/route.js`
- [ ] UI: `app/admin/reports/page.js`
- [ ] Integration: `services/reportService.js` (CSV generation utility)

---

## Role‑Based Access Control
**Status:** pending  
**Priority:** low  
**Sub-tasks:**
- [ ] Database: (adds `role` column to `models/user.js`)
- [ ] API: `middleware/requireRole.js`
- [ ] UI: `components/ProtectedRoute.jsx`
- [ ] Integration: `services/authService.js` (role checks in hooks)
