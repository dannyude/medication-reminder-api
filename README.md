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
    A secure, scalable, enterprise-grade REST API for medication reminders, user management, and session-based authentication.
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
        <li><a href="#security-architecture">Security Architecture</a></li>
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
    <!-- <li><a href="#usage">Usage</a></li>
    <li><a href="#api-overview">API Overview</a></li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li> -->
    <li><a href="#contact">Contact</a></li>
  </ol>
</details>


<!-- ABOUT THE PROJECT -->
## About The Project

[![MediReminder Swagger UI][product-screenshot]](http://127.0.0.1:8000/docs)

<div align="center">
  <p>
    <img src="images/screenshot_01.png" alt="Feature Screenshot" width="45%">
    &nbsp; &nbsp;
    <img src="images/screenshot_02.png" alt="Feature Screenshot" width="45%">
    &nbsp; &nbsp;
    <img src="images/screenshot_05.png" alt="Feature Screenshot" width="45%">
    &nbsp; &nbsp;
    <img src="images/screenshot_06.png" alt="Feature Screenshot" width="45%">
  </p>
</div>

MediReminder API is a **backend-first, security-focused REST API** designed to power medical reminder applications where **data integrity, session security, and predictable authentication flows are critical**.

The system was built with **real-world attack scenarios in mind**, including token replay, session hijacking, brute-force attempts, and credential misuse.

### Problem Statement

Medication adherence systems require:
- Strong identity verification
- Reliable session control
- Protection against token reuse
- Clear auditability of authentication events

MediReminder API addresses these needs by combining **modern API design** with **enterprise-grade authentication controls**.

<p align="right">(<a href="#readme-top">back to top</a>)</p>


---

### Key Features

- 🔐 **OAuth2 Password Flow with JWT**
- 🛡️ **Redis-based Rate Limiting (Brute-force protection)**
- 🔄 **Refresh token rotation with replay attack detection**
- 📧 **Secure Password Recovery Flow (Email w/ HTML templates)**
- 🧠 **Session versioning for instant global logout**
- 🚫 **Automatic token revocation on security violations**
- 🧑‍⚕️ **User & medication reminder management**
- 📄 **Interactive OpenAPI / Swagger documentation**
- 🐳 **Dockerized deployment**

---

### Security Architecture 

[Image of authentication flow diagram]


MediReminder API treats authentication as a **first-class system**, not a plugin.

**Security mechanisms include:**

- **Rate Limiting:** IP and Email-based throttling via Redis.
- **Access Tokens:** Short-lived JWTs.
- **Refresh Tokens:** Hashed (Argon2), one-time use, with replay detection.
- **Session Versioning:** Password changes invalidate all active sessions instantly.
- **Timing Attack Mitigation:** Generic responses for non-existent users.

This architecture mirrors **enterprise SaaS authentication systems**.

---

### Built With

* [![Python][Python-badge]](https://www.python.org/)
* [![FastAPI][FastAPI-badge]](https://fastapi.tiangolo.com/)
* [![PostgreSQL][Postgres-badge]](https://www.postgresql.org/)
* [![Redis][Redis-badge]](https://redis.io/)
* [![SQLAlchemy][SQLAlchemy-badge]](https://www.sqlalchemy.org/)
* [![Docker][Docker-badge]](https://www.docker.com/)

<p align="right">(<a href="#readme-top">back to top</a>)</p>

---

## Getting Started

### Prerequisites

- Python 3.10+
- PostgreSQL
- Redis (Required for Rate Limiting)
- Docker (optional but recommended)

---

### Installation

1. **Clone the repository**
   ```sh
   git clone [https://github.com/dannyude/medication-reminder-api.git](https://github.com/dannyude/medication-reminder-api.git)
   cd medication-reminder-api
   
2. **Create a virtual environment**
   ```sh
   # Windows
   python -m venv venv
   .\venv\Scripts\activate

   # Mac/Linux
   python3 -m venv venv
   source venv/bin/activate

3. **Install dependencies**
   ```sh
   If using uv (Recommended)
   uv sync

   If using standard pip
   pip install -r requirements.txt

4. **Configure Environment Variables Create a .env file in the root directory and add the following:**
   ```sh
    Database
    DATABASE_URL="postgresql+asyncpg://user:password@localhost:5432/medireminder"

    Redis (Rate Limiting)
    REDIS_URL="redis://127.0.0.1:6379"

    Security
    SECRET_KEY="your-super-secret-key"
    ALGORITHM="HS256"

    Email Configuration
    MAIL_USERNAME="your-email@gmail.com"
    MAIL_PASSWORD="your-app-password"
    MAIL_FROM="noreply@medireminder.com"
    MAIL_SERVER="smtp.gmail.com"
    MAIL_PORT=587

   
5. **Run the Server**
   ```sh
   uvicorn api.src.main:app --reload

    Once running, open the interactive API docs:
    http://127.0.0.1:8000/docs
  
**🐳 Run with Docker (Alternative)**

    If you prefer not to install Python/Redis locally, you can run the entire stack with Docker:

    docker-compose up --build


<!-- CONTACT -->
  **Contact**

    Danny - @Danny_Ude - danielude61@gmail.com

    Project Link: https://github.com/dannyude/medication-reminder-api

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[contributors-shield]: https://img.shields.io/github/contributors/dannyude/medication-reminder-api.svg?style=for-the-badge
[contributors-url]: https://github.com/dannyude/medication-reminder-api/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/dannyude/medication-reminder-api.svg?style=for-the-badge
[forks-url]: https://github.com/dannyude/medication-reminder-api/network/members
[stars-shield]: https://img.shields.io/github/stars/dannyude/medication-reminder-api.svg?style=for-the-badge
[stars-url]: https://github.com/dannyude/medication-reminder-api/stargazers
[issues-shield]: https://img.shields.io/github/issues/dannyude/medication-reminder-api.svg?style=for-the-badge
[issues-url]: https://github.com/dannyude/medication-reminder-api/issues
[license-shield]: https://img.shields.io/github/license/dannyude/medication-reminder-api.svg?style=for-the-badge
[license-url]: https://github.com/dannyude/medication-reminder-api/blob/master/LICENSE.txt
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url]: https://www.linkedin.com/in/daniel-ude-2b750a152/
[product-screenshot]: images/screenshot_01.png
<!-- Shields.io badges. You can a comprehensive list with many more badges at: https://github.com/inttter/md-badges -->
[Next.js]: https://img.shields.io/badge/next.js-000000?style=for-the-badge&logo=nextdotjs&logoColor=white
[Next-url]: https://nextjs.org/
[React.js]: https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB
[React-url]: https://reactjs.org/
[Vue.js]: https://img.shields.io/badge/Vue.js-35495E?style=for-the-badge&logo=vuedotjs&logoColor=4FC08D
[Vue-url]: https://vuejs.org/
[Angular.io]: https://img.shields.io/badge/Angular-DD0031?style=for-the-badge&logo=angular&logoColor=white
[Angular-url]: https://angular.io/
[Svelte.dev]: https://img.shields.io/badge/Svelte-4A4A55?style=for-the-badge&logo=svelte&logoColor=FF3E00
[Svelte-url]: https://svelte.dev/
[Laravel.com]: https://img.shields.io/badge/Laravel-FF2D20?style=for-the-badge&logo=laravel&logoColor=white
[Laravel-url]: https://laravel.com
[Bootstrap.com]: https://img.shields.io/badge/Bootstrap-563D7C?style=for-the-badge&logo=bootstrap&logoColor=white
[Bootstrap-url]: https://getbootstrap.com
[JQuery.com]: https://img.shields.io/badge/jQuery-0769AD?style=for-the-badge&logo=jquery&logoColor=white
[JQuery-url]: https://jquery.com 








