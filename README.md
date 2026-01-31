<a id="readme-top"></a>

<!-- PROJECT SHIELDS -->
[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![MIT License][license-shield]][license-url]
[![LinkedIn][linkedin-shield]][linkedin-url]

<!-- PROJECT LOGO -->
<br />
<div align="center">
	<a href="https://github.com/dannyude/medireminder-api">
		<img src="images/logo.png" alt="Logo" width="80" height="80">
	</a>

<h3 align="center">MediReminder API</h3>

	<p align="center">
		A production-ready, enterprise-grade REST API for medication adherence tracking with intelligent reminders, real-time notifications, and comprehensive health analytics.
		<br />
		<a href="https://github.com/dannyude/medication-reminder-api"><strong>Explore the docs »</strong></a>
		<br />
		<br />
		<a href="#">View Demo</a>
		·
		<a href="https://github.com/dannyude/medication-reminder-api/issues">Report Bug</a>
		·
		<a href="https://github.com/dannyude/medication-reminder-api/issues">Request Feature</a>
	</p>
</div>

---

<!-- TABLE OF CONTENTS -->
<details>
	<summary>Table of Contents</summary>
	<ol>
		<li>
			<a href="#about-the-project">About The Project</a>
			<ul>
				<li><a href="#problem-statement">Problem Statement</a></li>
				<li><a href="#key-features">Key Features</a></li>
				<li><a href="#architecture-overview">Architecture Overview</a></li>
				<li><a href="#built-with">Built With</a></li>
			</ul>
		</li>
		<li>
			<a href="#getting-started">Getting Started</a>
			<ul>
				<li><a href="#prerequisites">Prerequisites</a></li>
				<li><a href="#installation">Installation</a></li>
				<li><a href="#running-with-docker">Running with Docker</a></li>
			</ul>
		</li>
		<li><a href="#api-documentation">API Documentation</a></li>
		<li><a href="#security-features">Security Features</a></li>
		<li><a href="#notification-system">Notification System</a></li>
		<li><a href="#deployment">Deployment</a></li>
		<li><a href="#roadmap">Roadmap</a></li>
		<li><a href="#contributing">Contributing</a></li>
		<li><a href="#license">License</a></li>
		<li><a href="#contact">Contact</a></li>
	</ol>
</details>

---

<!-- ABOUT THE PROJECT -->
## About The Project

[![MediReminder Swagger UI][product-screenshot]](http://127.0.0.1:8000/docs)

<div align="center">
	<p>
		<img src="images/screenshot_01.png" alt="Authentication Flow" width="45%">
		&nbsp; &nbsp;
		<img src="images/screenshot_02.png" alt="Medication Management" width="45%">
		<br><br>
		<img src="images/screenshot_05.png" alt="Reminder System" width="45%">
		&nbsp; &nbsp;
		<img src="images/screenshot_06.png" alt="Analytics Dashboard" width="45%">
	</p>
</div>

**MediReminder API** is a **comprehensive, production-ready backend system** designed to solve medication adherence challenges through intelligent automation, real-time notifications, and data-driven insights.

Built with **security-first principles** and **enterprise-grade architecture**, this API powers mobile and web applications that help patients maintain medication schedules, track adherence, and manage their health effectively.

### Problem Statement

**Medication non-adherence** is a global healthcare crisis:
- 🚨 **50%** of patients don't take medications as prescribed
- 💰 **$100B+** in preventable healthcare costs annually (US alone)
- 🏥 **125,000** deaths per year from poor medication adherence
- 📱 Traditional reminder apps lack intelligence and fail to close the feedback loop

**MediReminder solves this by providing:**
- ✅ **Intelligent, timezone-aware medication scheduling**
- ✅ **Multi-channel notifications (SMS, Push)**
- ✅ **Real-time inventory tracking with low-stock alerts**
- ✅ **Adherence analytics and streak tracking**
- ✅ **Secure, HIPAA-ready authentication**
- ✅ **Background workers for reliable delivery**

<p align="right">(<a href="#readme-top">back to top</a>)</p>

---

## Key Features

### 🔐 **Enterprise Authentication & Security**
- **OAuth2 Password Flow** with JWT access tokens
- **Refresh Token Rotation** with replay attack detection
- **Session Versioning** for instant global logout
- **Redis-based Rate Limiting** (brute-force protection)
- **Secure Password Reset** with OTP verification
- **Token Reuse Detection** - automatic session revocation on security violations

### 💊 **Medication Management**
- **CRUD operations** for medications
- **Timezone-aware scheduling** (handles DST correctly)
- **Multiple frequency types**: Once daily, twice daily, every X hours, as-needed
- **Stock management** with automatic inventory tracking
- **Low stock alerts** with actionable notifications
- **Medication history** with comprehensive analytics

### ⏰ **Intelligent Reminder System**
- **Background scheduler** (APScheduler) for reliable delivery
- **Automatic reminder generation** (up to 30 days ahead)
- **Smart missed detection** (auto-mark after 2 hours)
- **Multi-status tracking**: Pending, Sent, Taken, Missed, Skipped
- **Quick mark as taken** with single-tap confirmation
- **Side effects logging** for health monitoring

### 📲 **Multi-Channel Notifications**
- **SMS via Termii** (optimized for Nigeria/Africa)
- **Alternative SMS via Twilio** (global coverage)
- **Push Notifications** via Firebase Cloud Messaging
- **Smart delivery**: SMS first, push as fallback
- **Low stock alerts** with urgency-based messaging

### 📊 **Health Analytics & Tracking**
- **Streak tracking** (current and longest)
- **Medication logs** with notes and side effects
- **Dashboard statistics** (today's summary, weekly trends)
- **Medication history** with next scheduled dose
- **Comprehensive reporting** for healthcare providers

### 🔄 **Background Processing**
- **Automatic reminder checks** (every minute)
- **Missed reminder marking** (hourly)
- **Daily reminder generation** (3 AM)
- **Low stock alerts** (daily at 9 AM)
- **Weekly adherence reports** (configurable)
- **Scalable to Celery** for production

<p align="right">(<a href="#readme-top">back to top</a>)</p>

---

## Architecture Overview
```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Layer                            │
│  (Mobile App, Web App, Third-party Integrations)                │
└────────────────────────┬────────────────────────────────────────┘
												 │
												 ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Application                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │   Auth API   │  │ Medication   │  │  Reminder    │           │
│  │   Endpoints  │  │   Endpoints  │  │  Endpoints   │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │   Logs API   │  │   Health     │  │   Admin      │           │
│  │   Endpoints  │  │   Check      │  │   Endpoints  │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
└────────────────────────┬────────────────────────────────────────┘
												 │
					┌──────────────┼──────────────┐
					│              │              │
					▼              ▼              ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  PostgreSQL  │  │    Redis     │  │ Background   │
│   Database   │  │ Rate Limiter │  │  Scheduler   │
│              │  │   & Cache    │  │ (APScheduler)│
└──────────────┘  └──────────────┘  └──────┬───────┘
																						│
																						▼
																		┌──────────────┐
																		│ Notification │
																		│   Services   │
																		│ (SMS/Push)   │
																		└──────────────┘
```

### Security Architecture
```
User Login Request
				│
				▼
┌─────────────────────┐
│ Rate Limit Check    │ ◄──── Redis (10 attempts/hour per IP)
│ (Email & IP)        │
└──────────┬──────────┘
					 │
					 ▼
┌─────────────────────┐
│ Verify Password     │
│ (Argon2 Hash)       │
└──────────┬──────────┘
					 │
					 ▼
┌─────────────────────┐
│ Check Account       │
│ Status & Session    │
│ Version             │
└──────────┬──────────┘
					 │
					 ▼
┌─────────────────────┐
│ Issue Tokens:       │
│ - Access (15 min)   │
│ - Refresh (7 days)  │
└──────────┬──────────┘
					 │
					 ▼
┌─────────────────────┐
│ Store Refresh Token │ ◄──── PostgreSQL (hashed + metadata)
│ Hash in Database    │
└─────────────────────┘
```

### Reminder Flow
```
										┌─────────────────────┐
										│ Daily @ 3 AM:       │
										│ Generate Reminders  │
										│ (Next 30 Days)      │
										└──────────┬──────────┘
															 │
															 ▼
										┌─────────────────────┐
										│ Every Minute:       │
										│ Check Pending       │
										│ Reminders           │
										└──────────┬──────────┘
															 │
					 ┌───────────────────┴───────────────────┐
					 │                                       │
					 ▼                                       ▼
┌─────────────────────┐                ┌─────────────────────┐
│ Send Notification   │                │ No Reminder Due     │
│ (SMS/Push/Email)    │                │ (Skip)              │
└──────────┬──────────┘                └─────────────────────┘
					 │
					 ▼
┌─────────────────────┐
│ Mark as SENT        │
│ Record Timestamp    │
└──────────┬──────────┘
					 │
					 ▼
┌─────────────────────┐
│ Wait for User       │
│ Action...           │
└──────────┬──────────┘
					 │
		┌──────┴──────┬──────────┐
		│             │          │
		▼             ▼          ▼
┌────────┐   ┌────────┐  ┌────────┐
│ TAKEN  │   │SKIPPED │  │MISSED  │
│        │   │        │  │(Auto)  │
└───┬────┘   └────────┘  └────────┘
		│
		▼
┌─────────────────────┐
│ Create Log Entry    │
│ Reduce Stock        │
│ Check Low Stock     │
│ Send Alert if Low   │
└─────────────────────┘
```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

---

## Built With

### **Core Technologies**
* [![Python][Python-badge]](https://www.python.org/) - Python 3.10+
* [![FastAPI][FastAPI-badge]](https://fastapi.tiangolo.com/) - High-performance async web framework
* [![PostgreSQL][Postgres-badge]](https://www.postgresql.org/) - Primary database
* [![Redis][Redis-badge]](https://redis.io/) - Rate limiting & caching
* [![SQLAlchemy][SQLAlchemy-badge]](https://www.sqlalchemy.org/) - Async ORM
* [![Docker][Docker-badge]](https://www.docker.com/) - Containerization

### **Security & Authentication**
* **PyJWT** - JSON Web Token implementation
* **Passlib** (Argon2) - Password hashing
* **python-multipart** - OAuth2 form data handling

### **Background Processing**
* **APScheduler** - Background job scheduling
* **AsyncIO** - Async task management

### **Notifications**
* **Termii API** - SMS (Nigeria-optimized)
* **Twilio** - SMS (global alternative)
* **Firebase Admin SDK** - Push notifications
* **FastAPI-Mail** - Email with HTML templates

### **Monitoring & Observability**
* **Logging** - Structured logging with Python logging
* **Pydantic** - Request/response validation
* **Alembic** - Database migrations

<p align="right">(<a href="#readme-top">back to top</a>)</p>

---

## Getting Started

### Prerequisites

Ensure you have the following installed:

- **Python 3.10+**
- **PostgreSQL 14+**
- **Redis 7+**
- **Docker & Docker Compose** (optional but recommended)

### Installation

#### **1. Clone the Repository**
```bash
git clone https://github.com/dannyude/medication-reminder-api.git
cd medication-reminder-api
```

#### **2. Create Virtual Environment**
```bash
# Using venv
python -m venv venv

# Activate on Windows
.\venv\Scripts\activate

# Activate on Mac/Linux
source venv/bin/activate
```

#### **3. Install Dependencies**
```bash
# Using uv (recommended - faster)
uv sync

# Or using pip
pip install -r requirements.txt
```

#### **4. Configure Environment Variables**

Create a `.env` file in the root directory:
```env
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/medireminder

# Redis
REDIS_URL=redis://127.0.0.1:6379

# Security
SECRET_KEY=your-super-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Rate Limiting
MAX_ATTEMPTS_PER_EMAIL=3
MAX_ATTEMPTS_PER_IP=10
WINDOW_HOURS=1
COOLDOWN_MINUTES=15

# Email Configuration
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_FROM=noreply@medireminder.com
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_FROM_NAME=MediReminder
FRONTEND_URL=http://localhost:3000

# SMS - Termii (Nigeria)
TERMII_API_KEY=your-termii-api-key
TERMII_SENDER_ID=MediRemind

# Alternative: Twilio
TWILIO_ACCOUNT_SID=your-account-sid
TWILIO_AUTH_TOKEN=your-auth-token
TWILIO_PHONE_NUMBER=+1234567890

# Push Notifications
FIREBASE_CREDENTIALS_PATH=path/to/firebase-credentials.json

# Notification Toggles
ENABLE_SMS=true
ENABLE_PUSH=true
ENABLE_EMAIL=true
```

#### **5. Initialize Database**
```bash
# Run migrations
alembic upgrade head
```

#### **6. Start Redis**
```bash
# Using Docker
docker run -d -p 6379:6379 redis:alpine

# Or install locally
# Mac: brew install redis && brew services start redis
# Ubuntu: sudo apt install redis-server && sudo systemctl start redis
```

#### **7. Run the Application**
```bash
uvicorn api.src.main:app --reload --host 0.0.0.0 --port 8000
```

#### **8. Access the API**
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

<p align="right">(<a href="#readme-top">back to top</a>)</p>

---

### Running with Docker

For a complete production-like environment:

#### **1. Build and Start**
```bash
docker-compose up --build
```

#### **2. Run Migrations**
```bash
docker-compose exec api alembic upgrade head
```

#### **3. Access Services**
- API: http://localhost:8000
- PostgreSQL: localhost:5432
- Redis: localhost:6379

#### **Docker Compose Services**
```yaml
services:
	- api (FastAPI application)
	- postgres (Database)
	- redis (Rate limiting & cache)
	- scheduler (Background worker)
```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

---

## API Documentation

### **Authentication Endpoints**

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/user/register` | Create new user account | ❌ |
| POST | `/user/fcm-token` | Update FCM token | ✅ |
| POST | `/auth/login` | Login with email/password | ❌ |
| POST | `/auth/refresh` | Refresh access token | ❌ |
| GET | `/auth/me` | Get current user info | ✅ |
| POST | `/auth/change-password` | Change password | ✅ |
| POST | `/auth/logout` | Logout current session | ✅ |
| POST | `/auth/logout-all` | Logout all devices | ✅ |
| POST | `/auth/forgot-password` | Request password reset | ❌ |
| POST | `/auth/reset-password` | Reset password with token | ❌ |

### **User Endpoints**

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/user/me` | Get current user profile | ✅ |
| GET | `/user/{user_id}` | Get user by ID | ✅ |
| GET | `/user/by-email/{email}` | Get user by email | ✅ |
| PATCH | `/user/{user_id}` | Update user profile | ✅ |
| DELETE | `/user/{user_id}` | Soft delete user | ✅ |
| DELETE | `/user/{user_id}/hard` | Hard delete user | ✅ |

### **Medication Endpoints**

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/medications/create` | Create medication | ✅ |
| GET | `/medications/get_all` | List medications (paginated) | ✅ |
| GET | `/medications/get_specific/{medication_id}` | Get medication | ✅ |
| PATCH | `/medications/{medication_id}` | Update medication | ✅ |
| GET | `/medications/low_stock` | Get low stock alerts | ✅ |
| PATCH | `/medications/{medication_id}/stock` | Update stock | ✅ |
| DELETE | `/medications/{medication_id}` | Delete medication | ✅ |

### **Reminder Endpoints**

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/reminders` | List reminders (filter + pagination) | ✅ |
| GET | `/reminders/{reminder_id}` | Get reminder details | ✅ |
| GET | `/reminders/medications/{medication_id}` | List reminders for medication | ✅ |
| POST | `/reminders/{reminder_id}/taken` | Mark as taken (with notes) | ✅ |
| POST | `/reminders/{reminder_id}/skipped` | Mark as skipped | ✅ |
| POST | `/reminders/{reminder_id}/missed` | Mark as missed | ✅ |
| DELETE | `/reminders/{reminder_id}` | Delete reminder | ✅ |
| POST | `/reminders/medications/{medication_id}/generate` | Generate reminders | ✅ |

### **Logging & Analytics Endpoints**

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/logs` | Create medication log | ✅ |
| GET | `/logs` | List medication logs | ✅ |
| GET | `/logs/adherence` | Get adherence stats | ✅ |
| GET | `/logs/history/{medication_id}` | Get medication history | ✅ |
| GET | `/logs/dashboard` | Get dashboard stats | ✅ |

### **Example: Mark Reminder as Taken**
```bash
POST /reminders/{reminder_id}/taken
Authorization: Bearer {access_token}

Response:
{
	"reminder_id": "abc-123-def",
	"status": "taken",
	"message": "✅ Done! ⚠️ Only 4 left - refill soon!",
	"medication_name": "Paracetamol",
	"stock_remaining": 4,
	"low_stock_warning": true,
	"taken_at": "2026-01-23T08:15:00Z"
}
```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

---

## Security Features

### **Authentication Flow**
```
1. User registers → Password hashed with Argon2
2. User logs in → Returns access + refresh tokens
3. Access token expires (30 min) → Use refresh token
4. Refresh token used → Old token invalidated, new pair issued
5. Suspicious activity → All sessions revoked
```

### **Security Mechanisms**

#### **Rate Limiting**
- **Email-based**: 3 attempts per hour
- **IP-based**: 10 attempts per hour
- **Cooldown**: 15 minutes between requests
- **Implementation**: Redis-backed, distributed-safe

#### **Token Security**
- **Access tokens**: Short-lived (30 minutes)
- **Refresh tokens**: 
	- Hashed before storage (SHA-256)
	- One-time use (replay detection)
	- Tracked with IP and user agent
	- Automatic revocation on suspicious activity

#### **Session Management**
- **Session versioning**: Instant global logout
- **Password change**: All sessions invalidated
- **Token reuse detection**: Auto-revoke all tokens

#### **Password Reset**
- **Multi-step flow**: Email → Token → Reset
- **15-minute token expiry**
- **Rate limited**: Same as login
- **User enumeration protection**: Generic responses

### **Data Security**
- **Password hashing**: Argon2 (industry standard)
- **SQL injection protection**: SQLAlchemy parameterized queries
- **XSS protection**: Pydantic input validation
- **CORS**: Configurable origins
- **HTTPS ready**: Production deployment with TLS

<p align="right">(<a href="#readme-top">back to top</a>)</p>

---

## Notification System

### **SMS Notifications (Termii)**

**Optimized for Nigeria/Africa:**
```python
# Medication reminder
"🏥 Medi Reminder: Time to take Paracetamol (500mg). Stay healthy!"

# Low stock alert
"⚠️ LOW STOCK: Your Paracetamol has only 4 pill(s) left. ~3 days remaining. Refill this week."

# Weekly report
"📊 Weekly Report: You took 27 doses this week (90.0% adherence). Keep it up! 💪"
```

### **Push Notifications (Firebase)**
```json
{
	"notification": {
		"title": "💊 Medication Reminder",
		"body": "Time to take Paracetamol (500mg)"
	},
	"data": {
		"type": "medication_reminder",
		"reminder_id": "abc-123",
		"medication_id": "xyz-789"
	}
}
```

### **Email Notifications**

- **HTML templates** with responsive design
- **Password reset links**
- **Weekly adherence reports**
- **Account security alerts**

### **Background Jobs**

| Job | Frequency | Description |
|-----|-----------|-------------|
| Check Reminders | Every minute | Send due notifications |
| Mark Missed | Every hour | Auto-mark late reminders |
| Generate Reminders | Daily @ 2 AM | Create next 30 days |
| Low Stock Alerts | Daily @ 9 AM | Check inventory |
| Weekly Reports | Weekly @ Sunday | Adherence summaries |

<p align="right">(<a href="#readme-top">back to top</a>)</p>

---

## Deployment

### **Production Checklist**

- [ ] Change `SECRET_KEY` to a strong random value
- [ ] Set `DATABASE_URL` to production database
- [ ] Configure production Redis instance
- [ ] Set up HTTPS/TLS certificates
- [ ] Configure CORS for your frontend domain
- [ ] Set up monitoring (Sentry, Datadog)
- [ ] Configure SMS provider (Termii/Twilio)
- [ ] Set up Firebase for push notifications
- [ ] Configure email provider (SendGrid, SES)
- [ ] Set up backup strategy for PostgreSQL
- [ ] Configure log aggregation (ELK, CloudWatch)
- [ ] Set up health check monitoring
- [ ] Configure rate limiting for production load
- [ ] Set up CI/CD pipeline

### **Environment-Specific Configs**
```env
# Production
DEBUG=false
ALLOWED_HOSTS=api.medireminder.com
DATABASE_URL=postgresql+asyncpg://user:pass@prod-db:5432/medireminder
REDIS_URL=redis://prod-redis:6379
ENABLE_DOCS=false  # Disable Swagger in production

# Staging
DEBUG=true
ALLOWED_HOSTS=staging-api.medireminder.com
ENABLE_DOCS=true
```

### **Scaling Considerations**

- **Database**: Use connection pooling (already configured in SQLAlchemy)
- **Redis**: Use Redis Cluster for high availability
- **Background Jobs**: Migrate to Celery with multiple workers
- **API**: Deploy multiple instances behind load balancer
- **Monitoring**: Set up Prometheus + Grafana for metrics

<p align="right">(<a href="#readme-top">back to top</a>)</p>

---

## Roadmap

### **Phase 1: Core Features** ✅ (Completed)
- [x] User authentication with JWT
- [x] Medication CRUD operations
- [x] Reminder system with scheduling
- [x] Medication logging and tracking
- [x] SMS notifications (Termii)
- [x] Background worker (APScheduler)
- [x] Adherence analytics
- [x] Low stock alerts

### **Phase 2: Enhanced Features** 🚧 (In Progress)
- [ ] Push notifications (Firebase)
- [ ] Email templates and reports
- [ ] Medication interaction warnings
- [ ] Doctor/caregiver access sharing
- [ ] Pharmacy integration for refills
- [ ] Health report exports (PDF)
- [ ] Multi-language support

### **Phase 3: Advanced Features** 📋 (Planned)
- [ ] WhatsApp notifications (Business API)
- [ ] Voice call reminders (Twilio)
- [ ] AI-powered medication insights
- [ ] Predictive adherence modeling
- [ ] Integration with wearables (Apple Health, Google Fit)
- [ ] Telemedicine integration
- [ ] Insurance claims automation
- [ ] Clinical trial support features

### **Phase 4: Enterprise Features** 🔮 (Future)
- [ ] Multi-tenant architecture
- [ ] Hospital/clinic management portal
- [ ] Advanced analytics dashboard
- [ ] HIPAA compliance certification
- [ ] HL7/FHIR integration
- [ ] Blockchain-based health records
- [ ] Real-time video consultations
- [ ] Prescription scanning (OCR)

See the [open issues](https://github.com/dannyude/medication-reminder-api/issues) for a full list of proposed features and known issues.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

---

## Contributing

Contributions make the open-source community an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

### **How to Contribute**

1. **Fork the Project**
2. **Create your Feature Branch** (`git checkout -b feature/AmazingFeature`)
3. **Commit your Changes** (`git commit -m 'Add some AmazingFeature'`)
4. **Push to the Branch** (`git push origin feature/AmazingFeature`)
5. **Open a Pull Request**

### **Development Guidelines**

- Follow PEP 8 style guide
- Write unit tests for new features
- Update documentation for API changes
- Keep commits atomic and descriptive
- Add type hints for new functions
- Run linters before committing (`ruff`, `black`)

### **Testing**
```bash
# Run tests
pytest

# Run with coverage
pytest --cov=api --cov-report=html

# Run linters
ruff check .
black --check .
```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

---

## License

Distributed under the MIT License. See `LICENSE.txt` for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

---

## Contact

**Daniel Ude**
- LinkedIn: [@daniel-ude](https://www.linkedin.com/in/daniel-ude-2b750a152/)
- Email: danielude61@gmail.com
- Twitter: [@Danny_Ude](https://twitter.com/Danny_Ude)

**Project Link**: [https://github.com/dannyude/medication-reminder-api](https://github.com/dannyude/medication-reminder-api)

<p align="right">(<a href="#readme-top">back to top</a>)</p>

---

## Acknowledgments

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Async Tutorial](https://docs.sqlalchemy.org/en/14/orm/extensions/asyncio.html)
- [Termii API](https://termii.com/)
- [Firebase Cloud Messaging](https://firebase.google.com/docs/cloud-messaging)
- [Best README Template](https://github.com/othneildrew/Best-README-Template)

<p align="right">(<a href="#readme-top">back to top</a>)</p>

---

<!-- MARKDOWN LINKS & IMAGES -->
[contributors-shield]: https://img.shields.io/github/contributors/dannyude/medication-reminder-api.svg?style=for-the-badge
[contributors-url]: https://github.com/dannyude/medication-reminder-api/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/dannyude/medication-reminder-api.svg?style=for-the-badge
[forks-url]: https://github.com/dannyude/medication-reminder-api/network/members
[stars-shield]: https://img.shields.io/github/stars/dannyude/medication-reminder-api.svg?style=for-the-badge
[stars-url]: https://github.com/dannyude/medication-reminder-api/stargazers
[issues-shield]: https://img.shields.io/github/issues/dannyude/medication-reminder-api.svg?style=for-the-badge
[issues-url]: https://github.com/dannyude/medication-reminder-api/issues
[license-shield]: https://img.shields.io/github/license/dannyude/medication-reminder-api.svg?style=for-the-badge
[license-url]: https://github.com/dannyude/medication-reminder-api/blob/main/LICENSE
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url]: https://linkedin.com/in/daniel-ude-2b750a152/

[Python-badge]: https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white
[FastAPI-badge]: https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white
[Postgres-badge]: https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white
[Redis-badge]: https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white
[SQLAlchemy-badge]: https://img.shields.io/badge/SQLAlchemy-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white
[Docker-badge]: https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white

[product-screenshot]: images/screenshot_01.png
