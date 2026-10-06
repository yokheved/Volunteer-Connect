# REST API Specification

## Overview

VolunteerConnect exposes a REST API through the Flask backend.

The API is used by the React frontend for:

- Authentication
- User profile management
- Volunteer configuration
- Volunteer search
- Volunteering request management
- Dashboard information
- AI matching results

Base path:

```text
/api
```

All request and response bodies use JSON unless otherwise specified.

---

# Authentication

## Register

```http
POST /api/auth/register
```

Creates a new user account.

Example request:

```json
{
  "name": "Example User",
  "email": "user@example.com",
  "password": "password",
  "phone": "0500000000",
  "address": "Jerusalem",
  "roles": ["CLIENT", "VOLUNTEER"]
}
```

Example response:

```json
{
  "id": 1,
  "name": "Example User",
  "email": "user@example.com",
  "roles": ["CLIENT", "VOLUNTEER"]
}
```

The password itself is never stored or returned.

The password must be at least 8 characters and must not be only whitespace.

A duplicate email returns `409`.

Invalid input, including a missing role list, returns `400`.

---

## Login

```http
POST /api/auth/login
```

Example request:

```json
{
  "email": "user@example.com",
  "password": "password"
}
```

Example response:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "name": "Example User",
    "email": "user@example.com",
    "roles": ["CLIENT", "VOLUNTEER"]
  }
}
```

Authentication uses JWT bearer tokens. Later requests send:

```http
Authorization: Bearer <access_token>
```

Invalid credentials return `401`.

A malformed email or missing password returns `400`. The error identifies the field problem and does not indicate whether the account exists.

---

## Logout

```http
POST /api/auth/logout
```

Requires the current bearer token.

Logout adds that token's id to an in-memory blocklist for this application process so the same token is rejected by protected endpoints. The blocklist is not stored in SQL Server and is cleared when the process restarts. Tokens also expire after their configured lifetime.

A missing, invalid, expired, or revoked token returns `401` with `{"error": "..."}`.

---

# User Profile

## Get Current User

```http
GET /api/users/me
```

Returns the authenticated user's profile.

Requires `Authorization: Bearer <access_token>`.

A missing, invalid, expired, or revoked token returns `401`.

---

## Update Profile

```http
PUT /api/users/me
```

Example request:

```json
{
  "name": "Example User",
  "phone": "0500000000",
  "address": "Jerusalem",
  "about_me": "I enjoy helping elderly people.",
  "monthly_hours_goal": 20
}
```

Only the authenticated user's profile may be modified.

---

# Volunteer Categories

## Get Volunteer Categories

```http
GET /api/volunteers/me/categories
```

Returns the current volunteer's selected categories.

---

## Update Volunteer Categories

```http
PUT /api/volunteers/me/categories
```

Example request:

```json
{
  "categories": [
    "Elderly Assistance",
    "Shopping",
    "Transportation"
  ]
}
```

Requires the VOLUNTEER role.

---

# Volunteer Availability

## Get Availability

```http
GET /api/volunteers/me/availability
```

---

## Update Availability

```http
PUT /api/volunteers/me/availability
```

Example:

```json
{
  "availability": [
    {
      "day_of_week": "MONDAY",
      "start_time": "09:00",
      "end_time": "13:00"
    },
    {
      "day_of_week": "WEDNESDAY",
      "start_time": "16:00",
      "end_time": "20:00"
    }
  ]
}
```

Requires the VOLUNTEER role.

---

# Volunteer Search

## Search Volunteers

```http
GET /api/volunteers
```

Possible query parameters:

```text
category
date
start_time
location
```

Example:

```text
GET /api/volunteers?category=Shopping&date=2026-10-15&start_time=10:00
```

The initial search uses structured application data.

AI matching may further evaluate suitable candidates.

Requires the CLIENT role.

---

# Volunteer Details

## Get Volunteer

```http
GET /api/volunteers/{volunteer_id}
```

Returns information that a client may view about a volunteer.

Possible response:

```json
{
  "id": 12,
  "name": "Example Volunteer",
  "categories": [
    "Shopping",
    "Elderly Assistance"
  ],
  "about_me": "I enjoy assisting elderly people.",
  "availability": []
}
```

Private account information is not returned.

---

# Volunteering Requests

## Create Request

```http
POST /api/requests
```

Requires the CLIENT role.

Example request:

```json
{
  "volunteer_id": 12,
  "category": "Shopping",
  "date": "2026-10-15",
  "start_time": "10:00",
  "duration": 2,
  "location": "Jerusalem",
  "description": "Help with grocery shopping."
}
```

The backend determines `client_id` from the authenticated user.

The client must not provide another user's `client_id`.

New requests are created with:

```text
PENDING
```

---

## Get Request

```http
GET /api/requests/{request_id}
```

Returns request details when the authenticated user is authorized to view the request.

---

## Get My Requests

```http
GET /api/requests
```

Returns requests associated with the authenticated user.

Possible filter:

```text
status
```

Example:

```text
GET /api/requests?status=PENDING
```

---

## Approve Request

```http
POST /api/requests/{request_id}/approve
```

Requires:

- VOLUNTEER role
- Authenticated user must be the volunteer assigned to the request
- Current status must be `PENDING`

Result:

```text
PENDING → APPROVED
```

---

## Reject Request

```http
POST /api/requests/{request_id}/reject
```

Requires:

- VOLUNTEER role
- Authenticated user must be the assigned volunteer
- Current status must be `PENDING`

Result:

```text
PENDING → REJECTED
```

---

## Complete Request

```http
POST /api/requests/{request_id}/complete
```

Marks an approved volunteering activity as completed.

Result:

```text
APPROVED → COMPLETED
```

The exact authorization rule for marking an activity completed will be finalized during implementation.

---

# Dashboards

## Volunteer Dashboard

```http
GET /api/dashboard/volunteer
```

Requires the VOLUNTEER role.

Possible response:

```json
{
  "monthly_goal": 20,
  "completed_hours": 12,
  "remaining_hours": 8,
  "next_volunteering": {},
  "pending_requests": [],
  "upcoming_activities": []
}
```

---

## Client Dashboard

```http
GET /api/dashboard/client
```

Requires the CLIENT role.

Possible response:

```json
{
  "next_volunteering": {},
  "pending_requests": [],
  "approved_requests": [],
  "completed_requests": []
}
```

---

# AI Matching

## Get Matching Results

```http
GET /api/requests/{request_id}/matches
```

Returns matching results generated by the Deep Agent.

Example response:

```json
{
  "request_id": 27,
  "matches": [
    {
      "volunteer_id": 12,
      "match_score": 91,
      "report": "Volunteer is available and has relevant experience."
    }
  ]
}
```

The endpoint retrieves stored matching results.

It does not perform the entire AI matching process synchronously as part of the HTTP request.

---

# HTTP Status Codes

The API should use standard HTTP status codes.

```text
200 OK
201 Created
400 Bad Request
401 Unauthorized
403 Forbidden
404 Not Found
409 Conflict
500 Internal Server Error
```

Examples:

- Invalid input → `400`
- User not authenticated → `401`
- User does not have required role → `403`
- Requested entity does not exist → `404`
- Invalid state transition → `409`

---

# CQRS Mapping

State-changing endpoints invoke Commands.

Examples:

```text
POST /auth/register
        ↓
RegisterUserCommand

POST /requests
        ↓
CreateVolunteerRequestCommand

POST /requests/{id}/approve
        ↓
ApproveVolunteerRequestCommand
```

Read-only endpoints invoke Queries.

Examples:

```text
GET /volunteers
        ↓
SearchVolunteersQuery

GET /dashboard/volunteer
        ↓
GetVolunteerDashboardQuery
```

Flask routes should remain thin and delegate business logic to the appropriate command/query handlers.

---

# API Design Status

This document defines the planned API before implementation.

Endpoint names, request structures, and response structures may be refined during development.

Any significant API change should be reflected in this document so that the frontend and backend remain consistent.