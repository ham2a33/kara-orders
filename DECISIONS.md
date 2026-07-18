# Architecture Decisions

## Authentication

- Use JWT access tokens for API authorization.
- Use HTTP-only refresh cookies for session rotation.
- Keep password hashing server-side with bcrypt.
- Validate passwords against a strict minimum policy.

## Authorization

- Use RBAC with the roles `owner`, `admin`, `manager`, and `employee`.
- Treat `owner` as the highest privilege and `employee` as the lowest privilege.
- Enforce company isolation in token validation and protected dependencies.

## Company Management

- Keep company profile, branding, and invoice defaults on the `companies` table for simple tenant reads.
- Store invitation state separately so invite lifecycle can be audited before acceptance.
- Use Supabase Storage as the external file store for company and invoice logos.
- Expose company management endpoints under `/api/v1/companies` and keep them scoped to the current tenant.

## Products & Inventory

- Keep the catalog centered on `products` with explicit category, barcode, tag, and inventory fields.
- Model categories, tags, product images, and inventory transactions as first-class tables to preserve auditability.
- Use soft deletes for catalog records so restoration is possible without losing historical references.
- Expose product and inventory endpoints under `/api/v1/products` and enforce tenant isolation in every query.

## Orders & Invoices

- Keep manual order creation centered on the backend so pricing, tax, and invoice totals are never trusted from the client.
- Store order-level customer details and computed totals on the `orders` table for direct invoice rendering.
- Store line-item discount and tax values on `order_items` to preserve a full audit trail of invoice math.
- Generate invoice PDFs server-side with a dedicated rendering service and expose them through `/api/v1/orders`.

## AI Order Recognition

- Keep AI as an extraction layer only: the model returns structured items, while the backend matches products and calculates totals.
- Use a reusable OpenAI provider abstraction so future Kara Group projects can reuse the same AI wiring.
- Store uploaded AI inputs in Supabase Storage and persist recognition history for auditability and review.
- Allow the application to start without `OPENAI_API_KEY`; AI endpoints return a clear configuration error instead of crashing.

## Dashboard & Analytics

- Calculate dashboard and analytics metrics exclusively on the backend to keep business logic authoritative.
- Use a dedicated analytics service with cached aggregate queries for revenue, orders, products, customers, and exports.
- Expose a single dashboard endpoint for high-level KPIs and dedicated analytics endpoints for deeper reporting slices.
- Generate CSV, Excel, and PDF exports server-side so operational reports remain consistent and auditable.
- Render analytics dashboards on the frontend with TanStack Query and Recharts to keep charts responsive and easy to refresh.

## SaaS Platform

- Keep subscription plans, company usage, audit logs, notifications, and global settings inside the core backend instead of introducing a separate billing service.
- Treat plan limits as server-enforced rules so the frontend never becomes the source of truth for usage caps.
- Seed a default Business plan and system settings row so new companies can start with a consistent SaaS baseline.
- Keep payment providers out of this stage and design the internal billing data model so future integrations can be added without schema churn.

## Data Model

- Keep multi-tenancy centered on `companies`.
- Scope users, products, and orders to a single company.
- Keep soft deletes and timestamp columns on primary business entities.

## API

- Keep REST endpoints under `/api/v1`.
- Expose Swagger/OpenAPI through FastAPI defaults.
- Return JSON-only responses for AI and validation-sensitive flows.

## Production Hardening

- Use backend and frontend security headers to reduce browser attack surface without breaking the Next.js application.
- Validate production environment settings at startup so missing secrets fail fast.
- Keep file upload validation server-side and enforce size and MIME checks before storage writes.
- Provide a separate production compose file and Nginx layer to keep local development and deployment concerns distinct.
