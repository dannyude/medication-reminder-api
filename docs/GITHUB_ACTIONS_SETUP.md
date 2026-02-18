# GitHub Actions CI/CD Setup Guide

## Overview

This guide shows how to configure GitHub Secrets and Variables for the CI/CD pipeline defined in `.github/workflows/deploy.yml`.

## 🔒 Secrets vs ⚙️ Variables

| Type | Use For | Visibility |
|------|---------|------------|
| **Secrets** | Passwords, API keys, tokens | Hidden in logs, encrypted at rest |
| **Variables** | Non-sensitive config (URLs, ports) | Visible in logs |

## 📋 Step-by-Step Setup

### 1. Navigate to GitHub Settings

1. Go to your repository on GitHub
2. Click **Settings** → **Secrets and variables** → **Actions**

### 2. Add Secrets (🔒 Tab: "Secrets")

Click **New repository secret** for each:

| Secret Name | Example Value | How to Get |
|-------------|---------------|------------|
| `DATABASE_URL` | `postgresql+asyncpg://user:pass@host:5432/db` | Your PostgreSQL connection string |
| `POSTGRES_PASSWORD` | `a3f!kL9$mQz7` | Strong random password (min 16 chars) |
| `SECRET_KEY` | `vK8xN2pL4qR9...` | Run: `python -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `MAIL_USERNAME` | `yourapp@gmail.com` | Your Gmail address |
| `MAIL_PASSWORD` | `abcd efgh ijkl mnop` | [Gmail App Password](https://myaccount.google.com/apppasswords) |
| `AT_API_KEY` | `atsk_...` | [Africa's Talking Dashboard](https://account.africastalking.com/apps/sandbox/settings/key) |
| `REDIS_URL` | `redis://redis:6379/0` | Your Redis connection string |

### 3. Add Variables (⚙️ Tab: "Variables")

Click **New repository variable** for each:

| Variable Name | Example Value | Purpose |
|---------------|---------------|---------|
| `ENVIRONMENT` | `production` | Environment name |
| `FRONTEND_URL` | `https://app.medireminder.com` | Frontend domain |
| `CORS_ORIGINS` | `https://app.medireminder.com` | Comma-separated allowed origins |
| `ALGORITHM` | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | JWT expiration |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token expiration |
| `PASSWORD_RESET_TOKEN_EXPIRE_MINUTES` | `15` | Password reset link expiration |
| `MAX_ATTEMPTS_PER_EMAIL` | `3` | Rate limit per email |
| `MAX_ATTEMPTS_PER_IP` | `10` | Rate limit per IP |
| `WINDOW_HOURS` | `1` | Rate limit window |
| `COOLDOWN_MINUTES` | `15` | Rate limit cooldown |
| `MAIL_SERVER` | `smtp.gmail.com` | SMTP server |
| `MAIL_PORT` | `465` | SMTP port |
| `MAIL_FROM` | `noreply@medireminder.com` | From email address |
| `MAIL_FROM_NAME` | `Medi Reminder` | From display name |
| `MAIL_SSL_TLS` | `True` | Use SSL/TLS |
| `MAIL_STARTTLS` | `False` | Use STARTTLS |
| `AT_USERNAME` | `sandbox` | Africa's Talking username |
| `AT_ENV` | `production` | Africa's Talking environment |
| `GOOGLE_CLIENT_ID` | `123456789...apps.googleusercontent.com` | [Google Cloud Console](https://console.cloud.google.com/) OAuth Client ID |

## 🧪 Testing the Workflow

### Option 1: Manual Trigger

1. Go to **Actions** tab in GitHub
2. Select **Deploy to Production** workflow
3. Click **Run workflow** → **Run workflow**

### Option 2: Push Trigger

```bash
git add .
git commit -m "feat: trigger deployment"
git push origin main
```

The workflow runs automatically on every push to `main`.

## 📊 Performance Gates

The workflow includes automated performance testing:

```yaml
- name: Run Performance Gate
  run: |
    python -m pip install locust
    powershell -File run_load_gate.ps1 -AuthProfile light
```

**Thresholds:**
- p95 latency ≤ 400ms
- p99 latency ≤ 1000ms
- Failure rate ≤ 1%

If any threshold is exceeded, the deployment is **blocked** ❌.

## 🔐 Security Best Practices

### ✅ DO

- ✅ Rotate secrets every 90 days
- ✅ Use strong passwords (min 16 chars, mixed case, symbols)
- ✅ Use GitHub Environment Secrets for production deployments
- ✅ Enable branch protection rules (require PR reviews)
- ✅ Use least-privilege service accounts

### ❌ DON'T

- ❌ Commit `.env` files with real credentials
- ❌ Echo secrets in workflow logs (`echo ${{ secrets.SECRET_KEY }}`)
- ❌ Share secrets via Slack/email/screenshots
- ❌ Reuse production passwords in development
- ❌ Grant write access to CI/CD tokens

## 🚀 Deployment Platforms

### GitHub Actions (Self-Hosted)

The current `deploy.yml` has a placeholder deployment step. Replace with your actual deployment commands:

```yaml
- name: Deploy to Production
  run: |
    # Example: Deploy to your server via SSH
    ssh user@your-server.com 'cd /app && git pull && docker-compose up -d'
```

### Railway

Add Railway token as secret:

```yaml
- name: Deploy to Railway
  run: |
    npm i -g @railway/cli
    railway up
  env:
    RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
```

### Render

Render deploys automatically via GitHub integration. Just connect your repo in the Render dashboard.

### Docker Hub

```yaml
- name: Push to Docker Hub
  run: |
    echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
    docker build -t yourorg/medication-api:${{ github.sha }} .
    docker push yourorg/medication-api:${{ github.sha }}
```

## 🆘 Troubleshooting

### "Secret not found" Error

**Cause:** Secret name mismatch between workflow and GitHub settings.

**Fix:** Verify secret names match exactly (case-sensitive):
```yaml
# ❌ Wrong
${{ secrets.database_url }}

# ✅ Correct
${{ secrets.DATABASE_URL }}
```

### "Performance gate failed" Error

**Cause:** API latency exceeds thresholds.

**Fix:**
1. Run locally: `.\run_load_gate.ps1 -AuthProfile light`
2. Review [docs/PERFORMANCE_BENCHMARKING.md](PERFORMANCE_BENCHMARKING.md)
3. Optimize slow endpoints
4. Scale infrastructure (more CPU/RAM)

### "Tests failed" Error

**Cause:** Unit tests failing on CI.

**Fix:**
1. Run locally: `pytest -v`
2. Check test logs in GitHub Actions → Job → Test step
3. Fix failing tests before pushing

## 📚 Related Documentation

- [SECRETS_MANAGEMENT.md](SECRETS_MANAGEMENT.md) - Comprehensive secrets guide
- [PERFORMANCE_BENCHMARKING.md](PERFORMANCE_BENCHMARKING.md) - Load testing guide
- [DEPLOYMENT.md](DEPLOYMENT.md) - General deployment guide
- [HARDENING_SUMMARY.md](HARDENING_SUMMARY.md) - Security checklist

## ✅ Pre-Deployment Checklist

Before going live:

- [ ] All GitHub Secrets configured
- [ ] All GitHub Variables configured
- [ ] `.env.prod` contains only placeholders (no real credentials)
- [ ] Tests passing: `pytest -v` (72/72 tests)
- [ ] Load gate passing: `.\run_load_gate.ps1 -AuthProfile light`
- [ ] Secrets rotated (not using development credentials)
- [ ] CORS_ORIGINS set to production domain (no wildcards)
- [ ] Email sending tested (password resets, welcome emails)
- [ ] Database backups configured
- [ ] Monitoring/logging enabled (sentry, datadog, etc.)
- [ ] DNS records configured
- [ ] SSL certificates valid
- [ ] Firewall rules configured (allow ports 80/443, block 5432/6379)

---

**Last Updated:** 2025-01-01
**Maintained By:** DevOps Team
