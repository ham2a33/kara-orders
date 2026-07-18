# Install

## Prerequisites

- Docker and Docker Compose
- Node.js 22 for local frontend development
- Python 3.12 for local backend development

## Setup

1. Copy `.env.example` to `.env`.
2. Set strong values for `SECRET_KEY`, database credentials, and production URLs.
3. Start the stack:

```bash
docker compose up --build
```

## Health Checks

- Backend liveness: `/api/v1/health/live`
- Backend readiness: `/api/v1/health/ready`
- Backend docs: `/docs`

