# 🚀 Developer Quick Reference

**Essential commands and configurations for the Medi-Minder API**

---

## 📦 One-Command Setup

### Windows
```powershell
.\setup.ps1
```

### Linux/Mac
```bash
chmod +x setup.sh && ./setup.sh
```

---

## 🐳 Docker Commands

### Service Management
```bash
# Start everything
docker-compose up -d

# Start with logs
docker-compose up

# Stop everything
docker-compose down

# Stop and remove volumes (⚠️ deletes data)
docker-compose down -v

# Restart specific service
docker-compose restart api

# Rebuild and restart
docker-compose up -d --build

# View status
docker-compose ps
```

### Logs & Debugging
```bash
# All logs
docker-compose logs -f

# API logs only
docker-compose logs -f api

# Last 100 lines
docker-compose logs --tail=100 api

# Database logs
docker-compose logs -f db

# Redis logs
docker-compose logs -f redis
```

### Shell Access
```bash
# API container
docker-compose exec api /bin/bash

# Database
docker-compose exec db psql -U medieminder -d medieminder

# Redis CLI
docker-compose exec redis redis-cli
```

---

## 🗃️ Database Operations

### Migrations
```bash
# Inside container
docker-compose exec api alembic upgrade head

# Rollback one migration
docker-compose exec api alembic downgrade -1

# View history
docker-compose exec api alembic history

# View current version
docker-compose exec api alembic current

# Create new migration
docker-compose exec api alembic revision --autogenerate -m "description"
```

### Direct Database Access
```bash
# Connect to PostgreSQL
docker-compose exec db psql -U medieminder -d medieminder

# Common queries
SELECT * FROM users LIMIT 10;
SELECT * FROM medications WHERE user_id = 'uuid-here';
SELECT * FROM reminders ORDER BY scheduled_time DESC LIMIT 20;

# Exit
\q
```

---

## 🔐 Environment Setup

### Generate Secure Keys
```bash
# Linux/Mac - SECRET_KEY
openssl rand -hex 32

# Windows PowerShell - SECRET_KEY
[Convert]::ToBase64String((1..32 | ForEach-Object { Get-Random -Maximum 256 }))
```

### Minimum Required `.env`
```env
DATABASE_URL=postgresql+asyncpg://medieminder:medieminder@db:5432/medieminder
REDIS_URL=redis://redis:6379
SECRET_KEY=<generate-this>
ALGORITHM=HS256
AT_API_KEY=your-key
AT_USERNAME=your-username
AT_SENDER_ID=your-sender
AT_ENV=sandbox
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_FROM=your-email@gmail.com
```

---

## 🧪 Testing API

### Health Check
```bash
curl http://localhost:8000/health
```

### Interactive Docs
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Sample cURL Commands

**Register User:**
```bash
curl -X POST http://localhost:8000/user/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123!",
    "confirm_password": "SecurePass123!",
    "first_name": "John",
    "last_name": "Doe",
    "mobile_number": "+1234567890"
  }'
```

**Login:**
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=SecurePass123!"
```

**Create Medication (with token):**
```bash
curl -X POST http://localhost:8000/medications/create \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "medication_name": "Aspirin",
    "dosage": "100mg",
    "frequency": "DAILY",
    "times": ["09:00", "21:00"],
    "start_datetime": "2026-02-01T00:00:00Z"
  }'
```

---

## 📊 Monitoring

### Resource Usage
```bash
# Real-time stats
docker stats

# Check specific container
docker stats medieminder-api
```

### Service Health
```bash
# All services
docker-compose ps

# Check if database is healthy
docker-compose exec db pg_isready -U medieminder

# Check Redis
docker-compose exec redis redis-cli ping
```

---

## 🛠️ Troubleshooting

### Port Conflicts
```bash
# Check what's using port 8000
# Windows
netstat -ano | findstr :8000

# Linux/Mac
lsof -i :8000

# Solution: Change port in docker-compose.yml
ports:
  - "8001:8000"
```

### Reset Everything
```bash
# Nuclear option: Clean slate
docker-compose down -v --rmi all
docker system prune -a --volumes

# Then rebuild
docker-compose up --build
```

### View Container Files
```bash
# List files in container
docker-compose exec api ls -la /app

# Check environment variables
docker-compose exec api env | grep DATABASE
```

---

## 🔥 Hot Reload Development

Files are mounted for hot-reload by default:
- `./api` → `/app/api`
- `./main.py` → `/app/main.py`
- `./alembic` → `/app/alembic`

Changes to Python files trigger automatic reload! No rebuild needed unless:
- Changing `requirements.txt`
- Modifying `Dockerfile`
- Changing Docker Compose config

---

## 📝 Common Workflows

### Adding a New Dependency
```bash
# 1. Add to requirements.txt
echo "package-name==1.0.0" >> requirements.txt

# 2. Rebuild
docker-compose build api

# 3. Restart
docker-compose up -d api
```

### Creating a Database Migration
```bash
# 1. Make model changes in code
# 2. Generate migration
docker-compose exec api alembic revision --autogenerate -m "add new column"

# 3. Apply migration
docker-compose exec api alembic upgrade head
```

### Backing Up Database
```bash
# Export
docker-compose exec db pg_dump -U medieminder medieminder > backup.sql

# Import
docker-compose exec -T db psql -U medieminder -d medieminder < backup.sql
```

---

## 🎯 Production Checklist

Before deploying:
- [ ] Change `DEBUG=false`
- [ ] Set strong `SECRET_KEY` (32+ chars)
- [ ] Use strong `POSTGRES_PASSWORD`
- [ ] Configure real email credentials
- [ ] Set up Africa's Talking production API keys
- [ ] Add Firebase `serviceAccountKey.json`
- [ ] Enable HTTPS/SSL
- [ ] Set up reverse proxy (nginx)
- [ ] Configure backups
- [ ] Set up monitoring (Sentry, New Relic, etc.)
- [ ] Review CORS settings
- [ ] Set proper rate limits

---

## 📞 Quick Links

- **API Docs**: http://localhost:8000/docs
- **Health**: http://localhost:8000/health
- **Postgres**: localhost:5432
- **Redis**: localhost:6379

---

## 🆘 Getting Help

1. Check logs: `docker-compose logs -f api`
2. Verify services: `docker-compose ps`
3. Check environment: `docker-compose exec api env`
4. Reset: `docker-compose down -v && docker-compose up --build`

---

**Pro Tip:** Keep this file open in a split terminal while developing! 🚀
