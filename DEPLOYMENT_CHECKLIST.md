# Deployment Checklist

- [ ] Copy `.env.example` to `.env`
- [ ] Replace all placeholder secrets
- [ ] Configure production database URL
- [ ] Configure production API and frontend URLs
- [ ] Run `alembic upgrade head`
- [ ] Start `docker-compose.prod.yml`
- [ ] Verify `/api/v1/health/ready`
- [ ] Verify frontend login and order flow

