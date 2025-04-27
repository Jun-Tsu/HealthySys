Health Information System
A robust, API-first health information system built with FastAPI and SQLite, designed to manage health programs and clients. Deployed on Railway, it features role-based access control (RBAC), audit logging, and secure JWT authentication, addressing the challenge of simulating a healthcare system for doctors to create programs, register/enroll clients, and manage profiles.
Features

Health Program Management: Admins create programs (e.g., TB, Malaria, HIV) with name and description.
Client Registration: Staff register clients with personal details (name, DOB, gender, contact).
Program Enrollment: Staff enroll clients in one or more programs.
Client Search: All users search clients by name.
Client Profile: View client details and enrolled programs via API.
RBAC: Roles (admin, staff, viewer) restrict access to endpoints.
Security: JWT authentication, input sanitization, contact hashing, audit logging.
Deployment: Live on Railway with persistent SQLite database.
Demo: Presentation (HealthySys_Presentation.pptx) and video (HealthySys_Demo.mp4) showcase functionality.

Tech Stack

Backend: FastAPI, SQLAlchemy, aiosqlite
Authentication: fastapi-users with JWT
Database: SQLite (health_system.db)
Deployment: Railway with volume at /app
Testing: pytest (basic endpoint tests)
Python: 3.9+

Setup
Prerequisites

Python 3.9+
pip
Git
SQLite (for local database inspection)

Installation

Clone the Repository:
git clone <your-repo-url>
cd HealthySys


Create Virtual Environment:
python -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\activate


Install Dependencies:
pip install -r requirements.txt


Set Environment Variables:Create a .env file in the root directory:
echo "JWT_SECRET=your-secret-key" > .env

Replace your-secret-key with a secure string.

Run the Application:
uvicorn main:app --host 127.0.0.1 --port 8000

Access at http://localhost:8000. OpenAPI docs at http://localhost:8000/docs.


Database Initialization

The app initializes health_system.db on startup.
Default admin: mary@q.com (password: z8jv6).
Default staff: john@q.com (password: 1234).

Access Details
Test the live application at https://web-copy-production-7415.up.railway.app. Use the OpenAPI docs at https://web-copy-production-7415.up.railway.app/docs for interactive testing.
Default Credentials

Admin:
Email: mary@q.com
Password: z8jv6


Staff:
Email: john@q.com
Password: 1234



Testing with cURL

Login (Get JWT Token):
curl -X POST "https://web-copy-production-7415.up.railway.app/auth/jwt/login" \
-H "Content-Type: application/x-www-form-urlencoded" \
-d "username=mary@q.com&password=z8jv6"

Copy the access_token from the response.

Create a Program (Admin Only):
curl -X POST "https://web-copy-production-7415.up.railway.app/api/programs" \
-H "Authorization: Bearer <admin-token>" \
-H "Content-Type: application/json" \
-d '{"name": "TB Program", "description": "Tuberculosis treatment"}'


Register a Client (Staff Only):
curl -X POST "https://web-copy-production-7415.up.railway.app/api/clients" \
-H "Authorization: Bearer <staff-token>" \
-H "Content-Type: application/json" \
-d '{"first_name": "Jane", "last_name": "Doe", "dob": "1990-01-01", "gender": "F", "contact": "1234567890"}'


Enroll a Client in a Program (Staff Only):
curl -X POST "https://web-copy-production-7415.up.railway.app/api/enrollments" \
-H "Authorization: Bearer <staff-token>" \
-H "Content-Type: application/json" \
-d '{"client_id": "<client-uuid>", "program_id": "<program-uuid>"}'

Replace <client-uuid> and <program-uuid> with actual IDs from previous responses.

Search Clients:
curl -X POST "https://web-copy-production-7415.up.railway.app/api/clients/search" \
-H "Authorization: Bearer <token>" \
-H "Content-Type: application/json" \
-d '{"search_term": "Jane"}'


View Client Profile:
curl -X GET "https://web-copy-production-7415.up.railway.app/api/clients/<client-uuid>" \
-H "Authorization: Bearer <token>"



Demo Screenshots
The following screenshots demonstrate key functionalities of the live application:

Program Creation: Admin creates a new health program.

Client Registration: Staff registers a new client.

Client Enrollment: Staff enrolls a client in a program.

Audit Logs: Logs of user actions for security and tracking.

Railway Deployment: Successful program creation on Railway.


API Endpoints
All endpoints require JWT authentication. RBAC restricts access.



Endpoint
Method
Role
Description



/auth/register
POST
Any
Register a new user (viewer by default)


/auth/jwt/login
POST
Any
Authenticate and get JWT token


/api/set-role
POST
Admin
Update user role (admin, staff, viewer)


/api/programs
POST
Admin
Create a health program


/api/clients
POST
Staff
Register a new client


/api/enrollments
POST
Staff
Enroll a client in a program


/api/clients/search
POST
Any
Search clients by name


/api/clients/{client_id}
GET
Any
View client profile and enrolled programs


Deployment

Platform: Railway (https://web-copy-production-7415.up.railway.app)
Configuration:
Volume mounted at /app for health_system.db persistence.
Procfile: web: uvicorn main:app --host 0.0.0.0 --port $PORT
Environment: JWT_SECRET set in Railway dashboard.


Challenges Overcome:
Fixed ASGI import error (Could not import module "main") by ensuring main.py and Procfile.
Resolved database reinitialization by uploading local health_system.db to volume.
Fixed syntax error in /set-role (circa to except).



Testing
Basic endpoint tests are implemented using pytest.

Install Testing Dependencies:
pip install pytest pytest-asyncio


Run Tests:
pytest test_main.py -v



Example test (test_main.py):
def test_create_program(admin_token):
    response = client.post(
        "/api/programs",
        json={"name": "TB Program", "description": "Tuberculosis treatment"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 201

Security Considerations

Authentication: JWT via fastapi-users, with tokens expiring after 1 hour.
Authorization: RBAC restricts endpoints (e.g., require_role("admin")).
Input Sanitization: sanitize_input prevents injection attacks.
Data Protection: Contacts hashed using hash_contact.
Audit Logging: Middleware logs all actions to audit_log table.
Temporary Endpoints: /upload-db, /download-db, /init-admin used for database management (removed post-deployment).

Demo

Presentation: HealthySys_Presentation.pptx details approach, design, and results (see Slide 8 for demo).
Video: HealthySys_Demo.mp4 shows login, database upload, role changes, and program creation.
Live Demo: https://web-copy-production-7415.up.railway.app

Project Structure
HealthySys/
├── main.py             # FastAPI app with endpoints
├── db.py              # Database operations
├── models.py          # Pydantic and SQLAlchemy models
├── utils.py           # Sanitization and hashing utilities
├── requirements.txt   # Dependencies
├── Procfile           # Railway deployment config
├── health_system.db   # SQLite database
├── test_main.py       # Unit tests
├── HealthySys_Presentation.md  # PowerPoint source
├── HealthySys_Presentation.pptx  # Presentation
├── HealthySys_Demo.mp4  # Demo video
├── screenshots/       # Demo screenshots
│   ├── admin_program_success.png
│   ├── staff_create_client.png
│   ├── staff_create_enrollment.png
│   ├── staff_audit_log.png
│   ├── railway_admin_program_success.png
└── .env               # Environment variables

Contributing

Fork the repository.
Create a feature branch (git checkout -b feature/xyz).
Commit changes (git commit -m "Add xyz feature").
Push to the branch (git push origin feature/xyz).
Open a pull request.

License
MIT License. See LICENSE for details.
Contact
For issues or inquiries, contact [Your Name] at [Your Email].
