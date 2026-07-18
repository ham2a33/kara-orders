# Deployment

## Production Stack

- `docker-compose.prod.yml` for orchestration
- `nginx/nginx.conf` as reverse proxy
- FastAPI backend on an internal `8000` port
- Next.js frontend on an internal `3000` port
- PostgreSQL as the primary datastore

## Recommended Flow

1. Copy `.env.example` to `.env`.
2. Fill production secrets and URLs.
3. Run migrations with `alembic upgrade head`.
4. Start production services with:

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

## Backup and Restore

- Back up PostgreSQL using `pg_dump` on a schedule.
- Verify restore by loading backups into a staging database before production use.

