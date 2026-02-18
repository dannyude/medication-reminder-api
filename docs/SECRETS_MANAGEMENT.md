# 🔐 Secrets Management Guide

This guide explains how to securely manage sensitive credentials and API keys for the Medication Reminder API.

## ⚠️ Critical Security Rules

1. **NEVER commit `.env` files to version control**
2. **NEVER share credentials via email, Slack, or chat**
3. **ALWAYS use platform-native secrets management**
4. **ROTATE credentials regularly (at least quarterly)**
5. **AUDIT who has access to production secrets**

## 📋 Environment Variables to Secure

```
DATABASE_URL              # PostgreSQL connection string
SECRET_KEY               # JWT signing key
REDIS_URL               # Redis connection
MAIL_PASSWORD           # Gmail App Password
AT_API_KEY              # Africa's Talking API key
GOOGLE_CLIENT_ID        # Google OAuth credentials
POSTGRES_PASSWORD       # Database password
```

---

## 🚀 Platform-Specific Secrets Management

### 1. **Railway.app** (Recommended for MVP)

```bash
# Connect your GitHub repo
# Go to: Project → Variables → Add from .env

# Or use CLI:
railway token <your-token>
railway variables add \
  DATABASE_URL="postgresql://..." \
  SECRET_KEY="your-key" \
  REDIS_URL="redis://..."

# Variables are encrypted at rest and in transit
# Check: https://docs.railway.app/develop/variables
```

### 2. **DigitalOcean App Platform**

```bash
# Via Dashboard:
# 1. Click "Edit" → "Components" → Your API
# 2. "Environment" → Add each variable
# 3. Mark as "Secret" for sensitive values
# 4. Deploy

# Secrets are not shown in logs or deployment history
```

### 3. **GitHub Secrets** (For CI/CD)

```bash
# Settings → Secrets and variables → New repository secret

# Use in workflows:
- name: Deploy
  env:
    DATABASE_URL: ${{ secrets.DATABASE_URL }}
    SECRET_KEY: ${{ secrets.SECRET_KEY }}
  run: |
    docker build -t app .
    docker push registry/app:latest
```

### 4. **AWS Secrets Manager**

```bash
# Create secret
aws secretsmanager create-secret \
  --name medireminder/prod \
  --secret-string '{"DATABASE_URL":"...","SECRET_KEY":"..."}'

# Retrieve in application
import boto3
client = boto3.client('secretsmanager')
secret = client.get_secret_value(SecretId='medireminder/prod')
```

### 5. **Google Cloud Secret Manager**

```bash
# Create secret
echo -n "YOUR_SECRET_VALUE" | gcloud secrets create DATABASE_URL --data-file=-

# Grant access
gcloud secrets add-iam-policy-binding DATABASE_URL \
  --member=serviceAccount:app@project.iam.gserviceaccount.com \
  --role=roles/secretmanager.secretAccessor

# Access in code
from google.cloud import secretmanager
client = secretmanager.SecretManagerServiceClient()
response = client.access_secret_version(request={"name": "projects/123/secrets/DATABASE_URL/versions/latest"})
secret = response.payload.data.decode('UTF-8')
```

### 6. **Kubernetes Secrets**

```bash
# Create from .env file
kubectl create secret generic medireminder-secrets --from-env-file=.env -n medireminder

# Reference in deployment
apiVersion: v1
kind: Pod
metadata:
  name: medireminder-api
spec:
  containers:
  - name: api
    envFrom:
    - secretRef:
        name: medireminder-secrets
```

---

## 🔑 How to Generate Secure Credentials

### 1. Generate SECRET_KEY (JWT)

```bash
# Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# OpenSSL
openssl rand -base64 32

# Result: Keep this safe! Use in both development and production
```

### 2. Generate Database Password

```bash
# OpenSSL (recommended)
openssl rand -base64 20

# Python
python -c "import secrets; print(secrets.token_urlsafe(20))"

# Store in: DATABASE_URL and POSTGRES_PASSWORD
```

### 3. Gmail App Password

1. Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
2. Select "Mail" and "Windows Computer"
3. Copy the 16-character password
4. Use in: `MAIL_PASSWORD=xxxx xxxx xxxx xxxx`

### 4. Africa's Talking API Key

1. Register at [africastalking.com](https://africastalking.com)
2. Go to Sandbox/Live dashboard
3. Copy API Key under "Settings"
4. Store in: `AT_API_KEY=atsk_...`

### 5. Google OAuth Client ID

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create OAuth 2.0 credentials (Web application)
3. Authorized redirect URIs: `https://yourdomain.com/auth/callback`
4. Copy Client ID
5. Store in: `GOOGLE_CLIENT_ID=...`

---

## 🔄 Local Development Setup

### Option A: Use `.env.example` (Recommended)

```bash
# Never commit actual credentials
cp .env.example .env

# Edit with your local/development values
nano .env

# Git will ignore it
git update-index --assume-unchanged .env
```

### Option B: Use `direnv` (Advanced)

```bash
# Install: https://direnv.net/docs/installation.html
brew install direnv  # macOS
sudo apt install direnv  # Ubuntu

# Create .envrc
echo 'export $(cat .env | xargs)' > .envrc

# Approve
direnv allow

# Credentials auto-loaded when entering directory
```

### Option C: Use `python-dotenv`

```python
# main.py
from dotenv import load_dotenv
load_dotenv()  # Loads from .env automatically
```

---

## 🛡️ Security Best Practices

### 1. Rotate Credentials Regularly

```bash
# Quarterly rotation schedule
# 1. Generate new SECRET_KEY
# 2. Update in all environments
# 3. Keep old key for 1 week grace period
# 4. Document rotation in changelog
```

### 2. Audit Access

```bash
# Who has accessed production secrets?
# - Check CI/CD logs
# - Monitor who has AWS/GCP console access
# - Use audit trails in secret managers
```

### 3. Different Credentials per Environment

```
.env.development    # Local unsafe values ok
.env.staging        # Staging-specific credentials
.env.production     # NEVER on local machine
```

### 4. Use Read-Only Credentials Where Possible

```python
# Example: Firebase read-only service account
# Example: S3 bucket with limited IAM permissions
```

### 5. Immediately Revoke Compromised Credentials

```bash
# If a credential is exposed:
# 1. Immediately rotate it
# 2. Update in all environments
# 3. Check logs for unauthorized access
# 4. Update dependencies/services
# 5. Document the incident
```

---

## 📝 CI/CD Integration Example

### GitHub Actions

```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Build and Push Docker Image
        run: |
          docker build -t myregistry/medireminder:${{ github.sha }} .
          docker push myregistry/medireminder:${{ github.sha }}

      - name: Deploy to Railway
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
          SECRET_KEY: ${{ secrets.SECRET_KEY }}
          REDIS_URL: ${{ secrets.REDIS_URL }}
          MAIL_PASSWORD: ${{ secrets.MAIL_PASSWORD }}
          AT_API_KEY: ${{ secrets.AT_API_KEY }}
          GOOGLE_CLIENT_ID: ${{ secrets.GOOGLE_CLIENT_ID }}
        run: |
          railway up
```

---

## ✅ Checklist Before Deployment

- [ ] All secrets in platform vault, NOT in `.env` file
- [ ] `.env*` files added to `.gitignore`
- [ ] No credentials in commit history (use `git-filter-repo` if needed)
- [ ] Different credentials for dev/staging/prod
- [ ] Secret rotation schedule documented
- [ ] Audit access logs configured
- [ ] Team trained on secrets management
- [ ] Emergency credential rotation process documented

---

## 🆘 If You Accidentally Commit a Secret

```bash
# 1. Immediately rotate the credential
# 2. Remove from commit history
git filter-repo --replace-text <(echo "OLD_SECRET===>REDACTED")

# 3. Force push (only if not yet on main)
git push --force

# 4. Audit git history for leaks
git log --all --oneline

# 5. Notify the team
```

**Better safe than sorry: Always assume committed secrets are compromised.**
