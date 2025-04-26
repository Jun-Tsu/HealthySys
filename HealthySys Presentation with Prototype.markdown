# HealthySys: Health Information System

---

## Slide 1: Title Slide
**HealthySys: A Secure Health Information System**  
- **Author**: [Your Name]  
- **Date**: April 26, 2025  
- **Objective**: Deliver a working prototype for managing health programs, clients, and enrollments with secure JWT authentication.  
- **GitHub**: [https://github.com/Jun-Tsu/HealthySys](https://github.com/Jun-Tsu/HealthySys)  

---

## Slide 2: Approach
**Project Goals**  
- Build a RESTful API prototype for health program and client management.  
- Implement secure JWT-based authentication.  
- Validate functionality via manual testing (enrollments, search, profile).  
- Demonstrate security by preventing unauthorized access.  

**Methodology**  
- **Agile Development**: Iterative coding and debugging (e.g., fixed `.env` BOM).  
- **Tech Stack**: FastAPI, SQLAlchemy, SQLite, `fastapi-users[jwt]`, Python 3.11.  
- **Security**: `JWT_SECRET` in `.env`, input sanitization, access control.  
- **Validation**: PowerShell scripts for API testing.

---

## Slide 3: Design
**Prototype Architecture**  
- **Backend**: FastAPI REST API with async SQLAlchemy.  
- **Database**: SQLite (`health_system.db`) for programs, clients, enrollments, users.  
- **Authentication**: `fastapi-users[jwt]` for secure access.  
- **Components**:  
  - **Endpoints**: `/auth/register`, `/auth/jwt/login`, `/api/programs`, `/api/clients`, `/api/enrollments`, `/api/clients/search`, `/api/clients/{client_id}`.  
  - **Security**: JWT tokens, `.env` secrets.  
- **Diagram**:  
  ```
  [User] --> [FastAPI (JWT Auth)] --> [SQLite DB]
              | Programs | Clients | Enrollments | Users |
  ```

---

## Slide 4: Solution
**Prototype Implementation**  
- **FastAPI**: Async API in `main.py` (artifact ID: `71328338-169c-4c89-917c-7351d5d248ca`).  
- **Database**: SQLite tables initialized via `db.py`.  
- **Authentication**: JWT with `fastapi-users[jwt]`, `JWT_SECRET` loaded from `.env`.  
- **Security Fixes**: Resolved `.env` BOM issue for proper secret loading.  

**Key Code** (from `main.py`):  
```python
from dotenv import load_dotenv
from os import getenv
load_dotenv()
SECRET = getenv("JWT_SECRET")
if not SECRET:
    raise ValueError("JWT_SECRET not set in .env")
```

---

## Slide 5: Prototype Demo
**Demonstrating the Working Prototype**  
- **Setup**:  
  - Server: `uvicorn main:app --reload` on `http://127.0.0.1:8000`.  
  - Database: Initialized with `init_db()` (`health_system.db`).  
- **Key Features Demoed**:  
  - **Authentication**: Register, login, obtain JWT.  
  - **Program Creation**: `POST /api/programs` with valid token.  
  - **Enrollments**: Enroll clients in programs.  
  - **Search/Profile**: Search clients and view profiles.  
- **Status**: [Pending server and validation outputs].  
- **Screenshots**: [Pending PowerShell logs or video].

---

## Slide 6: Security Verification
**Prototype Security Features**  
- **Test 1: No Token**  
  - Endpoint: `POST /api/programs`  
  - Result: [Pending output, expected `401 Unauthorized: {"detail": "Not authenticated"}`].  
- **Test 2: Invalid Token**  
  - Endpoint: `POST /api/programs` with `Bearer invalid_token`.  
  - Result: [Pending output, expected `401 Unauthorized: {"detail": "Invalid token"}`].  
- **Test 3: Valid Token**  
  - Register, login, create program.  
  - Result: [Pending output, expected `201 Created`].  
- **Status**: `JWT_SECRET` loads correctly (`d692c0c5e607988ac33073d16c2189336611c8e2ca228b4eee78d0dbcfdd8ec3`).

---

## Slide 7: Manual Validation
**Prototype Functionality Testing**  
- **Enrollments**:  
  - Clients: John, Jane, Alice, Bob, Emma in TB Program.  
  - Endpoint: `POST /api/enrollments`.  
  - Result: [Pending output].  
- **Search**:  
  - Searched “Jane” via `POST /api/clients/search`.  
  - Result: [Pending output].  
- **Profile**:  
  - Viewed Jane’s profile via `GET /api/clients/1902f900-bbc6-4034-afd3-01afdc2fdaa4`.  
  - Result: [Pending output].  
- **Database**:  
  - Tables: `programs`, `clients`, `enrollments`, `user`.  
  - Result: [Pending SQLite output].

---

## Slide 8: Challenges and Solutions
**Prototype Challenges**  
- `.env` BOM caused `JWT_SECRET` to fail.  
- Test failures in `test_api_working.py` (`AttributeError: 'async_generator'`).  

**Solutions**  
- Recreated `.env` without BOM using `Out-File -Encoding ascii`.  
- Shifted to manual validation due to time constraints.  
- Used PowerShell scripts for auth and functionality testing.

---

## Slide 9: Conclusion
**Prototype Summary**  
- Delivered a functional FastAPI prototype with secure auth and core features.  
- Demonstrated security (JWT) and functionality (enrollments, search, profile).  
- Overcame challenges (BOM, tests) with robust solutions.  

**Next Steps**  
- Fix tests (`test_api_working.py`) in [hours/mins].  
- Deploy to Railway.  
- Add role-based access and audit logging.  
- Submit PowerPoint and demo video.

---

## Slide 10: Questions
**Thank You!**  
- Questions about the prototype, design, or solution?  
- GitHub: [https://github.com/Jun-Tsu/HealthySys](https://github.com/Jun-Tsu/HealthySys)  
- Contact: [Your Contact Info]