# 🐳 Docker Quick Start Guide

Get the Medi-Minder API up and running in minutes!

## 📋 Prerequisites

- **Docker Desktop** (Windows/Mac) or **Docker Engine** (Linux)
- **Docker Compose** (usually included with Docker Desktop)
- **Git** (to clone the repository)

### Install Docker

- **Windows/Mac**: Download [Docker Desktop](https://www.docker.com/products/docker-desktop)
- **Linux**: Follow [Docker Engine installation](https://docs.docker.com/engine/install/)

Verify installation:
```bash
docker --version
docker-compose --version
```

## 🚀 Quick Start (Automated)

### Option 1: Windows (PowerShell)
```powershell
# Clone the repository
git clone <your-repo-url>
cd medication_reminder_api

# Run setup script
.\setup.ps1
```

### Option 2: Linux/Mac (Bash)
```bash
# Clone the repository
git clone <your-repo-url>
cd medication_reminder_api

# Make script executable
chmod +x setup.sh

# Run setup script
./setup.sh
```

The setup script will:
1. ✅ Check Docker installation
2. ✅ Create `.env` file from template
3. ✅ Generate secure `SECRET_KEY`
4. ✅ Build Docker images
5. ✅ Start all services
6. ✅ Run database migrations
7. ✅ Verify API health

## 🔧 Manual Setup

If you prefer manual setup or the scripts don't work:

### Step 1: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your settings
# At minimum, generate a secure SECRET_KEY
```

Generate a secure SECRET_KEY:
```bash
# Linux/Mac
openssl rand -hex 32

# Windows PowerShell
[Convert]::ToBase64String((1..32 | ForEach-Object { Get-Random -Maximum 256 }))
```

### Step 2: Build and Start Services

```bash
# Build images
docker-compose build

# Start services in background
docker-compose up -d

# Or start with logs visible
docker-compose up
```

### Step 3: Verify Setup

```bash
# Check if services are running
docker-compose ps

# View API logs
docker-compose logs -f api

# Test API health
curl http://localhost:8000/health
```

## 🌐 Access Points

Once running, access your API:

| Service | URL | Description |
|---------|-----|-------------|
| **API** | http://localhost:8000 | Main API endpoint |
| **Swagger Docs** | http://localhost:8000/docs | Interactive API documentation |
| **ReDoc** | http://localhost:8000/redoc | Alternative API documentation |
| **PostgreSQL** | localhost:5432 | Database (user: medieminder, pass: medieminder) |
| **Redis** | localhost:6379 | Cache & rate limiter |

## 📦 What's Included

The Docker setup provides:

- ✅ **PostgreSQL 15** - Database with persistent storage
- ✅ **Redis 7** - Caching and rate limiting
- ✅ **FastAPI App** - Your API with hot-reload
- ✅ **Auto Migrations** - Database schema auto-applied
- ✅ **Health Checks** - Service monitoring
- ✅ **Persistent Volumes** - Data survives container restarts

## 🛠️ Common Commands

### Service Management

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Restart a service
docker-compose restart api

# View logs
docker-compose logs -f api          # API logs only
docker-compose logs -f              # All services
docker-compose logs --tail=100 api  # Last 100 lines
```

### Database Operations

```bash
# Run migrations
docker-compose exec api alembic upgrade head

# Rollback migration
docker-compose exec api alembic downgrade -1

# Access PostgreSQL
docker-compose exec db psql -U medieminder -d medieminder
```

### Development

```bash
# Rebuild after code changes
docker-compose up -d --build

# Access API container shell
docker-compose exec api /bin/bash

# View container status
docker-compose ps

# View resource usage
docker stats
```

### Cleanup

```bash
# Stop and remove containers
docker-compose down

# Remove containers and volumes (⚠️ deletes data)
docker-compose down -v

# Remove images
docker-compose down --rmi all

# Complete cleanup (⚠️ removes everything)
docker-compose down -v --rmi all --remove-orphans
```

## 🔒 Environment Configuration

### Minimal Configuration (Development)

For local testing, only these are required:
```env
DATABASE_URL=postgresql+asyncpg://medieminder:medieminder@db:5432/medieminder
REDIS_URL=redis://redis:6379
SECRET_KEY=<generate-a-secure-key>
ALGORITHM=HS256
```

### Full Configuration (Production)

See `.env.example` for all available options including:
- Email configuration (password reset)
- SMS configuration (Africa's Talking)
- Rate limiting settings
- Token expiration times

## 🐛 Troubleshooting

### Port Already in Use

```bash
# Check what's using port 8000
# Windows
netstat -ano | findstr :8000

# Linux/Mac
lsof -i :8000

# Change port in docker-compose.yml
ports:
  - "8001:8000"  # Use port 8001 instead
```

### Database Connection Issues

```bash
# Check if database is healthy
docker-compose ps db

# View database logs
docker-compose logs db

# Restart database
docker-compose restart db
```

### Migration Errors

```bash
# Check current migration status
docker-compose exec api alembic current

# View migration history
docker-compose exec api alembic history

# Reset database (⚠️ data loss)
docker-compose down -v
docker-compose up -d
```

### API Not Starting

```bash
# Check API logs
docker-compose logs api

# Common issues:
# - Missing .env file: Copy from .env.example
# - Invalid environment variables: Check .env syntax
# - Port conflict: Change API_PORT in .env
```

### Performance Issues

```bash
# Check resource usage
docker stats

# Increase Docker resources:
# Docker Desktop → Settings → Resources
# - Memory: 4GB minimum, 8GB recommended
# - CPUs: 2 minimum, 4 recommended
```

## 🔥 Hot Reload Development

The Docker setup includes hot-reload for development:

1. **Code changes** - Automatically detected
2. **API restart** - Happens automatically
3. **No rebuild needed** - Unless dependencies change

To disable hot-reload (production):
```yaml
# In docker-compose.yml, change command to:
command: uvicorn main:app --host 0.0.0.0 --port 8000
```

## 📝 Adding Dependencies

When you add Python packages:

```bash
# 1. Add to requirements.txt
echo "new-package==1.0.0" >> requirements.txt

# 2. Rebuild the image
docker-compose build api

# 3. Restart the service
docker-compose up -d api
```

## 🚢 Production Deployment

For production, update:

1. **Environment variables**:
   ```env
   DEBUG=false
   SECRET_KEY=<strong-production-key>
   POSTGRES_PASSWORD=<strong-password>
   ```

2. **Docker Compose**:
   - Remove volume mounts for code
   - Remove `--reload` flag
   - Add reverse proxy (nginx)

3. **Security**:
   - Use secrets management
   - Enable HTTPS
   - Configure firewalls
   - Regular backups

## 💡 Tips

1. **First Time Setup**: Run the automated setup script for easiest experience
2. **Development**: Keep `docker-compose up` running in a separate terminal
3. **Logs**: Use `docker-compose logs -f api` to debug issues
4. **Database**: Data persists in volumes, survives container restarts
5. **Clean Start**: Use `docker-compose down -v` for fresh database

## 📞 Support

If you encounter issues:

1. Check logs: `docker-compose logs -f`
2. Verify .env configuration
3. Ensure Docker has enough resources
4. Try clean rebuild: `docker-compose down -v && docker-compose up --build`

## 🎉 Success!

If you see:
```
✅ API is healthy and responding!
📍 API Endpoint: http://localhost:8000
📚 API Documentation: http://localhost:8000/docs
```

**Congratulations!** Your Medi-Minder API is ready to use! 🚀
