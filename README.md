# Kara Orders

Kara Orders is a production-oriented SaaS platform for AI-assisted order and invoice creation.

## Current scope

The repository now includes the full v1.0.0 production stack:

- Next.js 15 frontend scaffold
- FastAPI backend scaffold
- PostgreSQL via Docker Compose
- SQLAlchemy and Alembic wiring
- JWT access and refresh tokens
- Password hashing and password policy validation
- Role-based access control for `owner`, `admin`, `manager`, and `employee`
- Company isolation and protected API routes
- Company profile, branding, invoice settings, user invitations, and logo upload
- Product catalog, categories, tags, inventory ledger, product images, and soft delete/restore flows
- Manual order entry, order review, order history, and invoice PDF generation
- AI order recognition for photo, voice, text, and supplier PDF inputs
- AI history and order review workflow with backend product matching
- Dashboard and analytics APIs for revenue, orders, products, customers, and exports
- Recharts-based dashboard, analytics, and reports pages
- Subscription, usage, billing, audit, notification, admin, and global system settings pages
- SaaS subscription plans, usage tracking, plan limits, audit logs, and notification APIs
- TailwindCSS and shadcn/ui foundation
- Swagger/OpenAPI on the backend
- Security headers, environment validation, health checks, structured logging, and production deployment assets
- GitHub Actions CI for linting, typing, testing, and Docker build validation

## Run

1. Copy `.env.example` to `.env`.
2. Start the stack:

```bash
docker compose up --build
```

3. Open:

- Frontend: `http://localhost:3001`
- Backend docs: `http://localhost:8000/docs`
- Backend OpenAPI: `http://localhost:8000/openapi.json`

## Production

For production deployment, use:

- `.env.example` as the baseline environment template
- `docker-compose.prod.yml` for production orchestration
- `nginx/nginx.conf` for reverse proxying and edge headers
- `DEPLOYMENT.md` and `INSTALL.md` for runbooks

Release materials:

- `RELEASE_NOTES.md`
- `PRODUCTION_CHECKLIST.md`
- `DEPLOYMENT_CHECKLIST.md`
- `KNOWN_LIMITATIONS.md`
- `FUTURE_IMPROVEMENTS.md`
- `API.md`
- `ADMIN_GUIDE.md`
- `USER_GUIDE.md`

## Structure

- `backend/` FastAPI service
- `frontend/` Next.js app
- `docker-compose.yml` local orchestration

## Notes

Authentication uses HTTP-only refresh cookies and bearer access tokens.
The backend exposes `/api/v1/auth/register`, `/login`, `/refresh`, `/logout`, and `/me`.
Company management endpoints live under `/api/v1/companies`.
Product and inventory endpoints live under `/api/v1/products`.
Order and invoice endpoints live under `/api/v1/orders`.
AI recognition endpoints live under `/api/v1/ai/order-recognitions`.
Dashboard and analytics endpoints live under `/api/v1/dashboard` and `/api/v1/analytics/*`.

Role hierarchy:

- `owner`
- `admin`
- `manager`
- `employee`

AI order recognition is designed to start cleanly even when `OPENAI_API_KEY` is missing.
In that case, AI endpoints return a clear `AI is not configured. Please add OPENAI_API_KEY.` error.

Dashboard and analytics metrics are calculated on the backend and exposed through cached REST endpoints.
The SaaS platform layer keeps subscription limits, usage counters, notifications, and audit logging inside the backend so future billing integrations can be added with minimal change.

The application starts cleanly without `OPENAI_API_KEY`; AI routes return a clear configuration error until AI is enabled.
