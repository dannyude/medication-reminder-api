# 🤝 Contributing to Medi-Minder API

Thank you for your interest in contributing to Medi-Minder! This document provides guidelines and instructions for contributing.

---

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Submitting Changes](#submitting-changes)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)

---

## 📜 Code of Conduct

We are committed to providing a welcoming and inclusive experience for everyone. We expect all contributors to:

- Be respectful and considerate
- Accept constructive criticism gracefully
- Focus on what's best for the community
- Show empathy towards other community members

---

## 🚀 Getting Started

### Prerequisites

Before you begin, ensure you have:
- Git installed
- Docker and Docker Compose installed
- A GitHub account
- Basic knowledge of Python and FastAPI

### Fork the Repository

1. Navigate to the [Medi-Minder repository](https://github.com/dannyude/medication-reminder-api)
2. Click the "Fork" button in the top right
3. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/medication-reminder-api.git
   cd medication-reminder-api
   ```

4. Add upstream remote:
   ```bash
   git remote add upstream https://github.com/dannyude/medication-reminder-api.git
   ```

---

## 💻 Development Setup

### Quick Setup with Docker

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings
# At minimum, set SECRET_KEY

# Start development environment
docker-compose up -d

# View logs
docker-compose logs -f api
```

### Manual Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start PostgreSQL and Redis
# (via Docker or locally)

# Run migrations
alembic upgrade head

# Start development server
uvicorn main:app --reload
```

---

## 🔨 Making Changes

### Branch Naming Convention

Create a branch following this pattern:

- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation updates
- `refactor/description` - Code refactoring
- `test/description` - Test additions/modifications

Example:
```bash
git checkout -b feature/add-medication-notes
```

### Development Workflow

1. **Keep your fork updated:**
   ```bash
   git fetch upstream
   git checkout main
   git merge upstream/main
   ```

2. **Create a new branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes:**
   - Write clean, readable code
   - Follow existing code style
   - Add comments where necessary
   - Update documentation

4. **Test your changes:**
   ```bash
   # Run tests
   pytest

   # Test manually via Swagger UI
   # http://localhost:8000/docs
   ```

5. **Commit your changes:**
   ```bash
   git add .
   git commit -m "feat: add medication notes field"
   ```

---

## 📤 Submitting Changes

### Commit Message Convention

Follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting, etc.)
- `refactor:` - Code refactoring
- `test:` - Adding or updating tests
- `chore:` - Maintenance tasks

**Examples:**
```bash
feat: add medication reminder snooze functionality
fix: correct timezone handling in reminder generation
docs: update API documentation for user endpoints
refactor: optimize database query performance
test: add unit tests for reminder CRUD operations
```

### Creating a Pull Request

1. **Push your branch:**
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create Pull Request:**
   - Go to your fork on GitHub
   - Click "Compare & pull request"
   - Fill in the PR template:
     - Clear title following commit conventions
     - Detailed description of changes
     - Link related issues
     - Screenshots (if UI changes)
     - Testing steps

3. **PR Template:**
   ```markdown
   ## Description
   Brief description of what this PR does.

   ## Type of Change
   - [ ] Bug fix
   - [ ] New feature
   - [ ] Breaking change
   - [ ] Documentation update

   ## Related Issues
   Fixes #123

   ## Testing
   - [ ] All tests pass
   - [ ] Added new tests for new functionality
   - [ ] Manually tested via Swagger UI

   ## Screenshots (if applicable)

   ## Checklist
   - [ ] Code follows project style guidelines
   - [ ] Self-review completed
   - [ ] Comments added for complex code
   - [ ] Documentation updated
   - [ ] No new warnings generated
   ```

---

## 📝 Coding Standards

### Python Style Guide

Follow [PEP 8](https://pep8.org/) guidelines:

```python
# Good
def calculate_medication_dosage(
    weight: float,
    age: int,
    medication_strength: str
) -> float:
    """
    Calculate medication dosage based on patient metrics.

    Args:
        weight: Patient weight in kg
        age: Patient age in years
        medication_strength: Strength of medication (e.g., "500mg")

    Returns:
        Calculated dosage in mg
    """
    # Implementation
    pass

# Bad
def calcDose(w,a,m):
    return w*a
```

### Type Hints

Always use type hints:

```python
# Good
from typing import Optional, List
from uuid import UUID

async def get_user_medications(
    user_id: UUID,
    skip: int = 0,
    limit: int = 100
) -> List[Medication]:
    pass

# Bad
async def get_user_medications(user_id, skip=0, limit=100):
    pass
```

### Docstrings

Use Google-style docstrings:

```python
def complex_function(param1: str, param2: int) -> dict:
    """
    One-line summary of function.

    Longer description if needed. Explain what the function does,
    any important implementation details, edge cases, etc.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: When param2 is negative
        HTTPException: When database connection fails

    Example:
        >>> result = complex_function("test", 42)
        >>> print(result)
        {'status': 'success'}
    """
    pass
```

### Async/Await

Properly use async/await:

```python
# Good
async def create_medication(
    medication_data: MedicationCreate,
    session: AsyncSession
) -> Medication:
    medication = Medication(**medication_data.dict())
    session.add(medication)
    await session.commit()
    await session.refresh(medication)
    return medication

# Bad (mixing sync and async incorrectly)
def create_medication(medication_data, session):
    medication = Medication(**medication_data.dict())
    session.add(medication)
    session.commit()  # Missing await
    return medication
```

### Error Handling

```python
from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)

# Good
async def get_medication(medication_id: UUID, session: AsyncSession):
    try:
        medication = await session.get(Medication, medication_id)
        if not medication:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Medication {medication_id} not found"
            )
        return medication
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching medication: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
```

---

## 🧪 Testing Guidelines

### Writing Tests

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_medication(client: AsyncClient, auth_headers):
    """Test medication creation endpoint."""
    medication_data = {
        "medication_name": "Aspirin",
        "dosage": "100mg",
        "frequency": "DAILY",
        "times": ["09:00", "21:00"],
        "start_datetime": "2026-02-01T00:00:00Z"
    }

    response = await client.post(
        "/medications/create",
        json=medication_data,
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["medication_name"] == "Aspirin"
    assert data["dosage"] == "100mg"

@pytest.mark.asyncio
async def test_create_medication_invalid_data(client: AsyncClient, auth_headers):
    """Test medication creation with invalid data."""
    invalid_data = {
        "medication_name": "",  # Invalid: empty name
        "dosage": "100mg"
    }

    response = await client.post(
        "/medications/create",
        json=invalid_data,
        headers=auth_headers
    )

    assert response.status_code == 422
```

### Running Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/test_medications.py

# With coverage
pytest --cov=api --cov-report=html

# Verbose output
pytest -v

# Stop on first failure
pytest -x
```

---

## 📚 Documentation

### API Documentation

When adding new endpoints, ensure:

1. **Clear docstrings:**
   ```python
   @router.post("/medications/create")
   async def create_medication(
       medication: MedicationCreate,
       current_user: User = Depends(get_current_user),
       session: AsyncSession = Depends(get_session)
   ):
       """
       Create a new medication for the authenticated user.

       This endpoint creates a medication schedule and automatically
       generates reminders based on the frequency and times provided.

       - **medication_name**: Name of the medication
       - **dosage**: Dosage amount (e.g., "500mg", "2 tablets")
       - **frequency**: DAILY, INTERVAL, WEEKLY, or MONTHLY
       - **times**: List of time strings in HH:MM format
       """
       pass
   ```

2. **Update README.md** with new endpoint details
3. **Update QUICK_REFERENCE.md** if needed
4. **Add examples** in docstrings

---

## 🎯 Areas for Contribution

We welcome contributions in these areas:

### High Priority
- [ ] Unit test coverage improvements
- [ ] API endpoint testing
- [ ] Documentation enhancements
- [ ] Bug fixes
- [ ] Performance optimizations

### Feature Requests
- [ ] Medication interaction warnings
- [ ] Dosage tracking and analytics
- [ ] Family/caregiver accounts
- [ ] Medication history export
- [ ] Integration with pharmacy APIs
- [ ] Voice assistant integration
- [ ] Wearable device integration

### Documentation
- [ ] Video tutorials
- [ ] API usage examples
- [ ] Deployment guides
- [ ] Troubleshooting guides

---

## ❓ Questions?

- 📧 Email: support@medireminder.com
- 💬 GitHub Discussions
- 🐛 GitHub Issues

---

## 🙏 Thank You!

Your contributions help make Medi-Minder better for everyone. We appreciate your time and effort!

---

**Remember:**
- Write clean, readable code
- Test your changes thoroughly
- Document what you've done
- Be patient and respectful

Happy coding! 🚀
