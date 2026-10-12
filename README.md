
# Week 3 — Project & Task Management REST API

## Overview

A multi-tenant Project and Task Management REST API
developed using Django REST Framework and PostgreSQL
as part of the NERUOS Full-Stack Engineering Internship.

## Technology Stack

- Python
- Django
- Django REST Framework
- PostgreSQL
- Simple JWT
- django-filter
- drf-spectacular (OpenAPI / Swagger)

## Features

- Project CRUD operations
- Task CRUD operations
- API versioning (v1 and v2)
- JWT authentication and token refresh
- Role-Based Access Control (RBAC)
- Object-level permissions
- Multi-tenant organization isolation
- Task ownership restrictions
- Task-to-Project relationships
- Filtering, searching, ordering and pagination
- Request validation and structured errors
- API throttling
- Idempotent Task creation
- Interactive Swagger documentation
- Automated API tests

## User Roles

| Role | Permissions |
|------|-------------|
| Viewer | View permitted tasks and projects |
| Editor | Create tasks/projects and update authorized records |
| Manager | Create, update and delete authorized records |

All operations are restricted to the authenticated
user's organization.

## API Endpoints

### Tasks

- GET /api/v1/tasks/
- POST /api/v1/tasks/
- GET /api/v1/tasks/{id}/
- PUT /api/v1/tasks/{id}/
- PATCH /api/v1/tasks/{id}/
- DELETE /api/v1/tasks/{id}/

### Projects

- GET /api/v1/projects/
- POST /api/v1/projects/
- GET /api/v1/projects/{id}/
- PUT /api/v1/projects/{id}/
- PATCH /api/v1/projects/{id}/
- DELETE /api/v1/projects/{id}/

Equivalent endpoints are available under /api/v2/.

## Local Setup

### 1. Create a virtual environment

python -m venv .venv

### 2. Activate it (Windows PowerShell)

.\.venv\Scripts\Activate.ps1

### 3. Install dependencies

python -m pip install -r requirements.txt

### 4. Configure PostgreSQL

Create the project database and configure the database
connection and environment settings.

Refer to .env.example for documented configuration
values if environment variables are supported.

### 5. Apply migrations

python manage.py migrate

### 6. Create an administrator

python manage.py createsuperuser

Configure organizations, memberships and RBAC groups
through Django Admin before testing protected APIs.

### 7. Start the server

python manage.py runserver

## API Documentation

Swagger v1:
http://127.0.0.1:8000/api/docs/

Swagger v2:
http://127.0.0.1:8000/api/docs/v2/

## Automated Tests

Run:

python manage.py test tasks -v 2

The test suite covers authentication, RBAC, ownership,
tenant isolation, validation, idempotency and
Task/Project relationships.

## Security

- JWT-protected endpoints
- Organization-scoped querysets
- Role-based and object-level authorization
- Cross-tenant Project assignment validation
- Protected task ownership
- Request throttling
- Idempotency safeguards

## Internship

NERUOS Full-Stack Engineering Internship
Week 3 — REST API Development
