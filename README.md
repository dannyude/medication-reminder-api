<a id="readme-top"></a>

<div align="center">

[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![MIT License][license-shield]][license-url]
[![LinkedIn][linkedin-shield]][linkedin-url]

</div>

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

```mermaid
graph TD
    Client[Client Layer] --> API[FastAPI Application]
    API --> Auth[Authentication Service]
    API --> Med[Medication Service]
    API --> Remind[Reminder Service]
    API --> DB[(PostgreSQL Database)]
    API --> Cache[(Redis Cache & Rate Limiter)]
    API --> Scheduler[Background Scheduler]
    Scheduler --> ReminderGen[Reminder Generation]
    Scheduler --> StockCheck[Stock Monitoring]
    Scheduler --> MissedCheck[Missed Reminder Detection]
    Scheduler --> Notifications[Notification Services]
    Notifications --> SMS[SMS - Termii/Twilio]
    Notifications --> Push[Push - Firebase FCM]
    Auth --> JWT[JWT Token Manager]
    Auth --> Session[Session Manager]
```

### Technology Stack

#### **Backend Framework**
- **FastAPI** - High-performance async API framework
- **Python 3.11+** - Modern Python with type hints
- **Pydantic V2** - Data validation and serialization
- **SQLAlchemy 2.0** - Modern ORM with async support

#### **Database & Caching**
- **PostgreSQL** - Primary database for ACID compliance
- **Redis** - Session storage, rate limiting, caching
- **Alembic** - Database migrations

#### **Authentication & Security**
- **OAuth2** with Password & Bearer flows
- **JWT** (PyJWT) - Secure token generation
- **bcrypt** - Password hashing
- **python-multipart** - Form data handling

#### **Background Processing**
- **APScheduler** - Scheduled tasks and background jobs
- **asyncio** - Asynchronous task execution

#### **Notifications**
- **Termii** - SMS service (Africa-optimized)
- **Twilio** - Global SMS fallback
- **Firebase Admin SDK** - Push notifications

#### **Development & DevOps**
- **Docker & Docker Compose** - Containerization
- **pytest** - Testing framework
- **Uvicorn** - ASGI server
- **Python-dotenv** - Environment management

<p align="right">(<a href="#readme-top">back to top</a>)</p>

---

## Getting Started

### Prerequisites

- **Python 3.11+**
- **PostgreSQL 14+**
- **Redis 7+**
- **Docker & Docker Compose** (optional)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/dannyude/medication-reminder-api.git
   cd medication-reminder-api
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

   **Required environment variables:**
   ```env
   # Database
   DATABASE_URL=postgresql://user:password@localhost:5432/medireminder

   # Redis
   REDIS_URL=redis://localhost:6379/0

   # JWT
   SECRET_KEY=your-secret-key-here
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   REFRESH_TOKEN_EXPIRE_DAYS=30

   # SMS Providers
   TERMII_API_KEY=your-termii-api-key
   TERMII_SENDER_ID=MediRemind
   TWILIO_ACCOUNT_SID=your-twilio-sid
   TWILIO_AUTH_TOKEN=your-twilio-token
   TWILIO_PHONE_NUMBER=+1234567890

   # Firebase (for push notifications)
   FIREBASE_CREDENTIALS_PATH=path/to/firebase-credentials.json

   # Email (optional)
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=your-email@gmail.com
   SMTP_PASSWORD=your-app-password
   ```

5. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

6. **Start the development server**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

7. **Access the API**
   - API Docs: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc
   - Health Check: http://localhost:8000/health

### Running with Docker

1. **Build and start containers**
   ```bash
   docker-compose up -d
   ```

2. **Run migrations**
   ```bash
   docker-compose exec api alembic upgrade head
   ```

3. **View logs**
   ```bash
   docker-compose logs -f api
   ```

4. **Stop containers**
   ```bash
   docker-compose down
   ```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

---

## API Documentation

### Authentication Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register new user |
| POST | `/api/v1/auth/login` | Login and get tokens |
| POST | `/api/v1/auth/refresh` | Refresh access token |
| POST | `/api/v1/auth/logout` | Logout (revoke session) |
| POST | `/api/v1/auth/logout-all` | Logout all sessions |
| POST | `/api/v1/auth/forgot-password` | Request password reset OTP |
| POST | `/api/v1/auth/reset-password` | Reset password with OTP |
| GET | `/api/v1/auth/me` | Get current user profile |

### Medication Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/medications` | Create medication |
| GET | `/api/v1/medications` | List all medications |
| GET | `/api/v1/medications/{id}` | Get medication details |
| PUT | `/api/v1/medications/{id}` | Update medication |
| DELETE | `/api/v1/medications/{id}` | Delete medication |
| POST | `/api/v1/medications/{id}/refill` | Refill medication stock |

### Reminder Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/reminders` | List reminders (with filters) |
| GET | `/api/v1/reminders/{id}` | Get reminder details |
| POST | `/api/v1/reminders/{id}/mark-taken` | Mark reminder as taken |
| POST | `/api/v1/reminders/{id}/skip` | Skip reminder |
| POST | `/api/v1/reminders/{id}/log-side-effects` | Log side effects |

### Analytics Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/analytics/dashboard` | Get dashboard statistics |
| GET | `/api/v1/analytics/streaks` | Get adherence streaks |
| GET | `/api/v1/analytics/history` | Get medication history |
| GET | `/api/v1/analytics/adherence-report` | Generate adherence report |

### Example Requests

**Register User:**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!",
    "full_name": "John Doe",
    "phone_number": "+2348012345678",
    "timezone": "Africa/Lagos"
  }'
```

**Create Medication:**
```bash
curl -X POST "http://localhost:8000/api/v1/medications" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Aspirin",
    "dosage": "100mg",
    "frequency_type": "daily_once",
    "time_of_day": ["08:00"],
    "stock_count": 30,
    "low_stock_threshold": 5,
    "notes": "Take with food"
  }'
```

**Mark Reminder as Taken:**
```bash
curl -X POST "http://localhost:8000/api/v1/reminders/{reminder_id}/mark-taken" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "notes": "Took with breakfast",
    "side_effects": null
  }'
```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

---

## Security Features

### Authentication Security
- **Secure password hashing** with bcrypt (cost factor 12)
- **JWT token validation** with expiration checking
- **Refresh token rotation** - new refresh token on every use
- **Token reuse detection** - automatic session revocation
- **Session versioning** - instant global logout capability

### API Security
- **Rate limiting** - Redis-based request throttling
- **CORS configuration** - Controlled cross-origin requests
- **Input validation** - Pydantic models for all inputs
- **SQL injection prevention** - SQLAlchemy ORM parameterization
- **XSS protection** - Output sanitization

### Data Security
- **Encrypted connections** - TLS/SSL for all communications
- **Environment variables** - Sensitive data never in code
- **Database encryption** - PostgreSQL encrypted at rest
- **Redis security** - Password-protected cache access

### HIPAA Compliance Considerations
- **Audit logging** - All data access tracked
- **Data retention policies** - Configurable retention periods
- **Access controls** - User-based data isolation
- **Encryption in transit** - All communications encrypted
- **Regular backups** - Automated database backups

<p align="right">(<a href="#readme-top">back to top</a>)</p>

---

## Notification System

### SMS Notifications (Termii)
```python
# Medication reminder
"Hi {name}, it's time to take your {medication} ({dosage}).
Tap here to confirm: {link}"

# Low stock alert
"⚠️ Your {medication} is running low ({count} left).
Time to refill!"
```

### Push Notifications (Firebase)
```python
{
    "title": "Medication Reminder",
    "body": "Time to take Aspirin (100mg)",
    "data": {
        "reminder_id": "123",
        "medication_id": "456",
        "type": "medication_reminder"
    }
}
```

### Notification Channels
1. **SMS** - Primary channel for critical reminders
2. **Push Notifications** - Secondary channel for in-app alerts
3. **Email** - Weekly summaries and reports (optional)

### Smart Delivery Logic
```python
async def send_reminder(reminder):
    # Try SMS first
    if user.phone_number and user.sms_enabled:
        await send_sms(reminder)

    # Fallback to push notification
    if user.fcm_token and user.push_enabled:
        await send_push(reminder)

    # Log delivery attempt
    await log_notification(reminder, status="sent")
```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

---

## Deployment

### Production Checklist

- [ ] Set strong `SECRET_KEY` in environment
- [ ] Configure production database (PostgreSQL RDS/managed)
- [ ] Set up Redis cluster for caching
- [ ] Configure SMS provider credentials
- [ ] Set up Firebase for push notifications
- [ ] Enable HTTPS/TLS
- [ ] Configure CORS for production domains
- [ ] Set up monitoring (Sentry, DataDog, etc.)
- [ ] Configure automated backups
- [ ] Set up CI/CD pipeline
- [ ] Enable rate limiting
- [ ] Configure log aggregation
- [ ] Set up health check endpoints
- [ ] Configure auto-scaling rules

### Deployment Options

#### **Option 1: Docker Deployment**
```bash
docker build -t medireminder-api .
docker run -d \
  --name medireminder \
  -p 8000:8000 \
  --env-file .env.production \
  medireminder-api
```

#### **Option 2: Railway**
```bash
railway login
railway init
railway up
```

#### **Option 3: AWS Elastic Beanstalk**
```bash
eb init -p python-3.11 medireminder-api
eb create medireminder-prod
eb deploy
```

#### **Option 4: Google Cloud Run**
```bash
gcloud run deploy medireminder \
  --source . \
  --region us-central1 \
  --allow-unauthenticated
```

### Environment-Specific Configurations

**Development:**
```env
DEBUG=True
RELOAD=True
LOG_LEVEL=DEBUG
```

**Production:**
```env
DEBUG=False
RELOAD=False
LOG_LEVEL=INFO
WORKERS=4
```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

---

## Roadmap

### Phase 1: Core Features ✅
- [x] User authentication with OAuth2
- [x] Medication CRUD operations
- [x] Intelligent reminder system
- [x] SMS notifications
- [x] Basic analytics

### Phase 2: Enhanced Features 🚧
- [x] Push notifications (Firebase)
- [x] Stock management
- [x] Adherence tracking
- [ ] Multi-language support
- [ ] Voice reminders

### Phase 3: Advanced Features 📋
- [ ] Family/caregiver accounts
- [ ] Healthcare provider portal
- [ ] Drug interaction checker
- [ ] Prescription image upload (OCR)
- [ ] Integration with pharmacy APIs
- [ ] Telemedicine integration

### Phase 4: Enterprise Features 🔮
- [ ] White-label solution
- [ ] Multi-tenant architecture
- [ ] Advanced analytics dashboard
- [ ] Machine learning adherence predictions
- [ ] IoT device integration (smart pill bottles)
- [ ] Blockchain-based audit trails

See the [open issues](https://github.com/dannyude/medication-reminder-api/issues) for a full list of proposed features and known issues.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

---

## Contributing

Contributions make the open-source community an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

### How to Contribute

1. **Fork the Project**
2. **Create your Feature Branch** (`git checkout -b feature/AmazingFeature`)
3. **Commit your Changes** (`git commit -m 'Add some AmazingFeature'`)
4. **Push to the Branch** (`git push origin feature/AmazingFeature`)
5. **Open a Pull Request**

### Development Guidelines

- Follow PEP 8 style guidelines
- Write unit tests for new features
- Update documentation for API changes
- Use type hints for all functions
- Add docstrings to all public methods
- Ensure all tests pass before submitting PR

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py

# Run specific test
pytest tests/test_auth.py::test_user_registration
```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

---

## License

Distributed under the MIT License. See `LICENSE` for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

---

## Contact

**Daniel Ude**

- LinkedIn: [daniel-ude-2b750a152](https://linkedin.com/in/daniel-ude-2b750a152/)
- GitHub: [@dannyude](https://github.com/dannyude)
- Email: daniel.ude@example.com

**Project Link:** [https://github.com/dannyude/medication-reminder-api](https://github.com/dannyude/medication-reminder-api)

<p align="right">(<a href="#readme-top">back to top</a>)</p>

---

## Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - Modern, fast web framework
- [SQLAlchemy](https://www.sqlalchemy.org/) - Python SQL toolkit
- [Pydantic](https://docs.pydantic.dev/) - Data validation
- [Termii](https://termii.com/) - SMS service provider
- [Firebase](https://firebase.google.com/) - Push notifications
- [APScheduler](https://apscheduler.readthedocs.io/) - Background scheduling
- [Redis](https://redis.io/) - In-memory data structure store
- [PostgreSQL](https://www.postgresql.org/) - Open source database
- [Choose an Open Source License](https://choosealicense.com)
- [Img Shields](https://shields.io)

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
[product-screenshot]: images/swagger_ui.png
