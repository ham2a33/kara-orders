# Changelog

## v1.0.0

### Added

- Production hardening for security headers, environment validation, health checks, logging, and file upload validation.
- Production deployment assets including `docker-compose.prod.yml`, Nginx config, and CI workflows.
- Release documentation: installation, deployment, API, admin guide, user guide, release notes, production checklist, deployment checklist, known limitations, and future improvements.

## Unreleased

### Added

- SaaS platform layer for subscription plans, usage tracking, plan limits, audit logs, notifications, and system settings.
- Super admin administration endpoints and pages for plan changes, billing flags, company suspension, and global settings.
- Company subscription, usage, audit log, notification, and system settings database tables.
- Monthly AI usage accounting, limit enforcement, and welcome/limit notifications.
- Dashboard API for real-time company KPIs, revenue trends, order trends, inventory summary, and top lists.
- Analytics APIs for revenue, orders, products, customers, and export downloads in CSV, Excel, and PDF formats.
- Recharts-based dashboard, analytics, and reports pages for operational insight.
- AI order recognition API for photo, voice, text, and supplier PDF inputs.
- AI history persistence with company, user, model, confidence, token usage, and status tracking.
- AI review and order-confirmation workflow that reuses the existing `OrderService`.
- Product aliases for deterministic AI product matching.
- AI dashboard pages for recognition intake, history, and review.
- Orders and invoice API for order CRUD, restoration, list/search/filter/sort pagination, and PDF generation.
- Orders dashboard pages for list, create, edit, details, invoice preview, and invoice list.
- PDF invoice rendering with company branding, invoice metadata, item tables, and totals.
- Product catalog and inventory API for CRUD, search, filtering, pagination, restore, categories, tags, images, and inventory transactions.
- Product dashboard pages for the catalog, product editor, categories, inventory, and inventory history.
- Database support for product categories, tags, product images, inventory transactions, barcode search, and inventory-related fields.
- Company management API for profile, settings, branding, logo upload, invitations, and user administration.
- Company dashboard pages for profile, settings, branding, invoice settings, and users.
- Supabase Storage integration path for company and invoice logo uploads.
- Database support for extended company settings and invitation records.
- Initial project foundation for Next.js, FastAPI, PostgreSQL, Docker, and shared configuration.
- Stage 2 database models, relationships, soft deletes, timestamps, migrations, and development seed data.
- Stage 3 authentication and authorization with JWT access and refresh tokens, RBAC, and company isolation.
- Stage 8 dashboard and analytics with backend-calculated metrics and export downloads.
- Stage 9 SaaS platform and subscription system with internal billing architecture.
- Auth API endpoints for register, login, refresh, logout, and profile lookup.
- Support for the `owner`, `admin`, `manager`, and `employee` role model.

### Changed

- AI endpoints now start safely without `OPENAI_API_KEY` and return a clear configuration error when invoked.
- Replaced the earlier `owner`/`staff` role model with the approved four-role hierarchy.
- Added refresh-cookie based session handling to the backend authentication flow.
- Extended the product model to support barcode lookup, category relationships, inventory thresholds, and soft restore flows.
- Extended orders to capture customer address, notes, discount totals, and tax totals.
