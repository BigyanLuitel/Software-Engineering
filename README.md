# School Management System

A full-stack school administration backend built with Django and Django REST Framework. The project is designed for a single-school setup and includes authentication, student management, teacher records, attendance tracking, academic records, library management, fee processing, notifications, reports, assignment workflows, and an AI proxy layer that connects to a FastAPI service for smart features.

This repository is structured as a multi-app Django project and is intended to support internal school operations through REST APIs.

## Overview

The system follows a single-tenant architecture, with one school configuration stored in the `apps.school` app and all operational data tied to that school context. The application uses a custom email-based authentication model and JWT access tokens for secure API access.

### Core modules

- `apps.accounts` — authentication, roles, JWT login, permissions
- `apps.school` — school profile and configuration
- `apps.students` — student profiles and enrollment data
- `apps.teachers` — teacher records and subject mapping
- `apps.academics` — classes, subjects, exams, and academic structures
- `apps.attendance` — attendance tracking and bulk marking
- `apps.results` — results, grading, conduct ratings, and publication logic
- `apps.fees` — fee categories, structures, invoices, and assignments
- `apps.library` — books and circulation records
- `apps.notifications` — notifications and recipient tracking
- `apps.reports` — report generation metadata and records
- `apps.assignments` — assignment management and submissions
- `apps.aiproxy` — AI service integration layer for assistant, question paper, and SQL-style query features

## Tech stack

- Python
- Django
- Django REST Framework
- Django REST Framework SimpleJWT
- PostgreSQL (configured in project settings)
- FastAPI-compatible AI service layer via `apps.aiproxy`
- Media uploads for student photos and school logo

## Project structure

```text
Software-Engineering/
├── README.md
├── HLD/
│   ├── Architecture.drawio
│   ├── dfd.vsdx
│   └── ER-2.vsdx
└── schoolSystem/
    ├── manage.py
    ├── requirements.txt
    ├── db.sqlite3
    ├── media/
    ├── schoolSystem/
    │   ├── __init__.py
    │   ├── asgi.py
    │   ├── settings.py
    │   ├── urls.py
    │   └── wsgi.py
    └── apps/
        ├── accounts/
        ├── school/
        ├── students/
        ├── teachers/
        ├── academics/
        ├── attendance/
        ├── results/
        ├── fees/
        ├── library/
        ├── notifications/
        ├── reports/
        ├── assignments/
        ├── aiproxy/
        └── ...
```

## Authentication and authorization

The project uses a custom user model:

- Model: `apps.accounts.models.User`
- Login identifier: `email`
- Roles: `ADMIN`, `TEACHER`, `STUDENT`
- JWT-based authentication enabled through `rest_framework_simplejwt`

Default settings in `schoolSystem/settings.py` enforce authentication globally, with JWT authentication as the main auth mechanism.

## API entry points

The project exposes REST APIs under the following namespaces:

```text
/api/auth/
/api/students/
/api/teachers/
/api/academics/
/api/attendance/
/api/assignments/
/api/results/
/api/fees/
/api/library/
/api/reports/
/api/notifications/
/api/ai/
```

### Auth endpoints

- `POST /api/auth/login/` — user login, returns JWT token pair
- `POST /api/auth/refresh/` — refresh access token

### AI proxy endpoints

The AI integration layer is exposed via the `aiproxy` app:

- `POST /api/ai/assistant/` — student assistant interaction
- `POST /api/ai/question-paper/` — generate question papers
- `POST /api/ai/query/` — natural-language SQL-style query interface

## Installation and setup

1. Open a terminal in the project root.
2. Navigate to the Django project folder:

```bash
cd schoolSystem
```

3. Create and activate a virtual environment:

```bash
python -m venv .venv
```

On Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

4. Install project dependencies:

```bash
pip install -r requirements.txt
```

5. Configure environment variables for the database. The project expects PostgreSQL settings from environment variables such as:

```env
USER=your_db_user
DB_PASSWORD=your_db_password
HOST=your_db_host
PORT=5432
```

These values are read in `schoolSystem/settings.py`.

6. Run database migrations:

```bash
python manage.py migrate
```

7. Create an admin account:

```bash
python manage.py createsuperuser
```

8. Start the development server:

```bash
python manage.py runserver
```

The backend will be available at:

```text
http://127.0.0.1:8000/
```

## Environment notes

- The codebase includes a local `db.sqlite3` file in the project directory, but the active Django configuration is currently set to PostgreSQL using environment variables.
- Media files are stored under `schoolSystem/media/` and are served in debug mode from `MEDIA_ROOT`.
- `ALLOWED_HOSTS` is currently empty in development mode and should be updated for production deployment.

## Project conventions

- The app uses a custom user model instead of Django's default `User`.
- Data access is primarily handled by Django REST Framework viewsets and serializers.
- The design is organized around clear domain modules, which makes it easy to extend for additional school features.
- The `apps.aiproxy` app acts as a thin integration adapter to an AI service rather than embedding AI logic directly in all domains.

## Typical workflow

1. Create school configuration in the `school` app.
2. Create users with roles such as admin, teacher, or student.
3. Add academic structures: class, subject, and exam definitions.
4. Register students and teachers with related profiles.
5. Track attendance, results, fees, assignments, and library circulation.
6. Generate reports and notifications for communication with stakeholders.
7. Use the AI endpoints for assistant-style queries and question generation.

## Production considerations

Before production deployment, the project should be updated to include:

- secure `SECRET_KEY` management via environment variables
- stricter `DEBUG` configuration
- production database and cache settings
- CORS configuration if frontend apps consume the API
- domain-specific security policies and deployment environment variables
- proper media storage configuration for cloud hosting

## License

This project is currently intended for academic and development use as part of the Software Engineering coursework.

## Notes

This repository is a Django backend project and is best used with a frontend client or API testing tool such as Postman, Insomnia, or Swagger-compatible tooling. The project structure is modular and suitable for extension as the school platform grows.
