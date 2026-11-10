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
  "confirm_password": "password",
  "phone": "0500000000",
  "address": "1 Kikar Safra, Jerusalem, Israel",
  "google_place_id": "ChIJi8mnMiQGhk8R0qK2G1jW7Zc",
  "latitude": 31.7788,
  "longitude": 35.2254,
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

The password must be at least 8 characters and must not be only whitespace. `confirm_password` is required. It must match `password`. A missing confirmation or a mismatch returns `400`, and no account is created.

A duplicate email returns `409`.

Invalid input, including a missing role list, returns `400`.

Registration requires a Google Places selection: `address`, `google_place_id`, `latitude`, and `longitude` together. Free-text address without a place id returns `400`. Latitude must be between -90 and 90. Longitude must be between -180 and 180.

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

Returns the authenticated user's profile, including `address`, `google_place_id`, `latitude`, and `longitude`.

The password is never returned.

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
  "current_password": "password",
  "name": "Example User",
  "phone": "0500000000",
  "roles": ["CLIENT", "VOLUNTEER"],
  "address": "1 Kikar Safra, Jerusalem, Israel",
  "google_place_id": "ChIJi8mnMiQGhk8R0qK2G1jW7Zc",
  "latitude": 31.7788,
  "longitude": 35.2254,
  "new_password": "newpassword",
  "confirm_password": "newpassword",
  "about_me": "I enjoy helping elderly people.",
  "monthly_hours_goal": 20
}
```

Only the authenticated user's profile may be modified. The user id comes from the JWT.

`current_password` is required. If it does not match, the API returns `401`, changes nothing, and writes no event.

`email` cannot be changed. Sending `email` returns `400`.

`new_password` and `confirm_password` are optional together. If either is sent, both are required, they must match, and the new password must be at least 8 characters. Omit both to leave the password unchanged.

Address updates require the same four location fields as registration. An address without a place id or coordinates returns `400`. If the stored address is unchanged, resend the stored place id and coordinates.

`about_me` and `monthly_hours_goal` are accepted only when the roles in this request include `VOLUNTEER`. A user who does not include `VOLUNTEER` in that request and sends either field receives `403`. A client may set those fields in the same save that adds the `VOLUNTEER` role.

---

# Volunteer Categories

Allowed category strings:

```text
Elderly Assistance
Transportation
Shopping
Tutoring
Technical Help
Childcare Support
Cooking
Cleaning
```

`PUT` replaces the volunteer's entire selection. An empty `categories` array is valid and clears the selection. Any other string, a blank value, or a duplicate in the same request returns `400`.

Both endpoints require `Authorization: Bearer <access_token>` and the VOLUNTEER role. The volunteer id comes from the JWT. A missing, invalid, expired, or revoked token returns `401`. A user without the VOLUNTEER role receives `403`. Current password is not required.

Both GET and PUT return:

```json
{
  "categories": [
    "Elderly Assistance",
    "Shopping"
  ]
}
```

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

`day_of_week` is one of:

```text
SUNDAY
MONDAY
TUESDAY
WEDNESDAY
THURSDAY
FRIDAY
SATURDAY
```

The week starts on Sunday. GET and PUT return windows ordered Sunday through Saturday, then by `start_time`. The database `id` is not returned.

Times use `HH:MM` on a 24-hour clock, such as `09:00` and `13:00`. `end_time` must be later than `start_time` on the same day.

`PUT` replaces the volunteer's entire set. An empty `availability` array is valid and clears the selection. Windows on the same day must not overlap; an overlap or an exact duplicate returns `400` and leaves the previous rows unchanged. A window that ends at the same minute the next one starts, such as `09:00–13:00` and `13:00–16:00`, does not overlap and is allowed. Windows on different days do not overlap.

Both endpoints require `Authorization: Bearer <access_token>` and the VOLUNTEER role. The volunteer id comes from the JWT. A missing, invalid, expired, or revoked token returns `401`. A user without the VOLUNTEER role receives `403`. Current password is not required.

Both GET and PUT return:

```json
{
  "availability": [
    {
      "day_of_week": "MONDAY",
      "start_time": "09:00",
      "end_time": "13:00"
    }
  ]
}
```

## Get Availability

```http
GET /api/volunteers/me/availability
```

Returns the current volunteer's recurring availability windows.

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

Optional query parameters:

```text
category
date
start_time
latitude
longitude
radius_km
```

Example:

```text
GET /api/volunteers?category=Shopping&date=2026-10-15&start_time=10:00
```

All filters may be omitted. An empty search returns every volunteer. Present filters are combined with AND.

- `category` must be one of the eight allowed category strings. Any other value returns `400`. A volunteer matches when that category is one of their saved categories.
- `date` is `YYYY-MM-DD`. It selects the weekday, with Sunday as the first stored day name (`SUNDAY` through `SATURDAY`). `start_time` is `HH:MM`. Sending one without the other returns `400`. A volunteer matches when one saved window on that weekday satisfies `window start <= start_time < window end`. Monday `10:00` matches `09:00–13:00` and does not match `14:00–18:00`. Monday `13:00` matches `13:00–16:00` and does not match `09:00–13:00`.
- `latitude` and `longitude` are the coordinates of a place the client picked from Google Places autocomplete in the UI. They must be sent together; otherwise `400`. `radius_km` is optional (default `10`, allowed `1`–`100`) and requires coordinates. A volunteer matches when the straight-line (haversine) distance from their saved coordinates is at most `radius_km`. Volunteers without saved coordinates do not match a location filter. This endpoint does not call Google.

Only users with the VOLUNTEER role are candidates. The caller is never returned, even when they are also a volunteer. Results are ordered by name, then id. The `address` field is city and country only. Email, phone, password, street, building number, Google Place ID, latitude, and longitude are not returned.

Example response:

```json
{
  "volunteers": [
    {
      "id": 12,
      "name": "Example Volunteer",
      "address": "Jerusalem, Israel",
      "categories": ["Shopping"],
      "about_me": "I enjoy assisting elderly people.",
      "availability": [
        {
          "day_of_week": "MONDAY",
          "start_time": "09:00",
          "end_time": "13:00"
        }
      ]
    }
  ]
}
```

An empty `volunteers` array is `200`, not `404`.

A missing, invalid, expired, or revoked token returns `401`. A user without the CLIENT role receives `403`.

The initial search uses structured application data.

AI matching may further evaluate suitable candidates later. This endpoint does not run AI matching.

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

The body contains `volunteer_id`, `category`, `date` (`YYYY-MM-DD`), `start_time` (`HH:MM`), `duration` (a whole number of hours, at least 1), and `description` (1–2000 characters).

The task location is optional in the body: `location` (formatted address), `google_place_id`, `latitude`, and `longitude`, from a place the client picked in Google Places autocomplete. The four fields are sent together; sending only some of them returns `400`. When they are sent, `location_cached_at` is set to now (or kept from the profile if the place id is the client's saved one). When they are omitted, all five fields are copied from the client's saved Google place; if the client has no saved place id or coordinates, the command returns `400`. The server makes no Google request.

The request screen fills the task location with the client's profile address by default (or, when searching again from a rejected request, that request's location). The client can change it before sending.

`client_id` comes from the JWT. The body must not include `client_id` or `status`. Sending a request to the caller's own user id returns `400`. `volunteer_id` must be an existing user with the VOLUNTEER role; an unknown id or a non-volunteer returns `404`. `category` must be one of the eight allowed categories and one of that volunteer's saved categories.

The requested `date` and `start_time` are checked against the volunteer's saved availability, using the same weekday rule as search. Sunday is the first stored day name. A volunteer matches when one saved window on that weekday satisfies `window start <= start_time < window end`. Thursday `10:00` matches `09:00–13:00` and does not match `14:00–18:00`. Thursday `13:00` does not match `09:00–13:00`. If no window matches, the command returns `400` and writes no request and no event.

The request screen lists that volunteer's saved windows and the client chooses one. The body `start_time` is that window's start. The body `date` must fall on that window's weekday.

Example request:

```json
{
  "volunteer_id": 12,
  "category": "Shopping",
  "date": "2026-10-15",
  "start_time": "10:00",
  "duration": 2,
  "description": "Help with grocery shopping."
}
```

New requests are created with:

```text
PENDING
```

A successful response is `201`:

```json
{
  "id": 1,
  "client_id": 4,
  "volunteer_id": 12,
  "category": "Shopping",
  "date": "2026-10-15",
  "start_time": "10:00",
  "duration": 2,
  "location": "1 Kikar Safra, Jerusalem, Israel",
  "google_place_id": "ChIJi8mnMiQGhk8R0qK2G1jW7Zc",
  "latitude": 31.7788,
  "longitude": 35.2254,
  "location_cached_at": "2026-10-18T07:31:00",
  "description": "Help with grocery shopping.",
  "status": "PENDING",
  "created_at": "2026-10-18T07:31:01"
}
```

Email, phone, and password are not returned.

A missing, invalid, expired, or revoked token returns `401`. A user without the CLIENT role receives `403`. Validation failures return `400` and write no request and no event.

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
GET /api/requests?status=PENDING
```

Returns the authenticated user's requests from both sides: the requests they sent as a client and the requests sent to them as a volunteer. Sorted by `date`, then `start_time`.

`status` is optional and must be `PENDING`, `APPROVED`, `REJECTED`, or `COMPLETED` (any case). Another value returns `400`.

Before answering, the server closes the user's requests whose time has passed (see [Automatic close](#automatic-close)), so the returned statuses are current.

Each item is the request object returned by create, plus:

- `my_role` — `CLIENT` when the caller sent the request, `VOLUNTEER` when it was sent to them
- `client_name`
- `volunteer_name`

Email, phone, and password are not returned. A missing or invalid token returns `401`.

```json
[
  {
    "id": 1,
    "client_id": 4,
    "volunteer_id": 12,
    "category": "Shopping",
    "date": "2026-11-12",
    "start_time": "10:00",
    "duration": 2,
    "location": "1 Kikar Safra, Jerusalem, Israel",
    "description": "Help with grocery shopping.",
    "status": "PENDING",
    "my_role": "VOLUNTEER",
    "client_name": "Dana Cohen",
    "volunteer_name": "Avi Levi",
    "...": "other create fields"
  }
]
```

---

## Approve Request

```http
POST /api/requests/{request_id}/approve
```

No body.

Requires:

- VOLUNTEER role, otherwise `403`
- The caller is the request's volunteer, otherwise `404` (another volunteer's request is reported as not found)
- Current status is `PENDING`, otherwise `409`
- The start time has not passed. An expired request is closed first as `REJECTED`, so approving it returns `409`.
- No overlap with another `APPROVED` request of the same volunteer on the same date, otherwise `409`. Travel time is not checked here.

Result: `200` with the updated request.

```text
PENDING → APPROVED
```

Writes `VolunteerRequestApproved`.

---

## Reject Request

```http
POST /api/requests/{request_id}/reject
```

No body. Same role, ownership, and `PENDING` rules as approve (`403`, `404`, `409`).

Result: `200` with the updated request.

```text
PENDING → REJECTED
```

Writes `VolunteerRequestRejected`.

---

## Automatic close

There is no complete endpoint. A request closes on its own when its time passes:

```text
APPROVED, and date + start_time + duration has passed → COMPLETED
PENDING,  and date + start_time has passed            → REJECTED
```

The check runs when requests are read: at the start of `GET /api/requests`, and before approve or reject. It uses the server's local time, the same clock as the stored date and time. Each change writes `VolunteerRequestCompleted` or `VolunteerRequestRejected` with `"acted_by": "SYSTEM"`. An expired `PENDING` request also has `"reason": "EXPIRED"`.

Every status change uses a conditional update (`... WHERE id = :id AND status = :expected`). If the status changed in between, a manual action returns `409` and the automatic step skips the request, so no request gets two events for the same change.

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

The agent stores at most six matches for the request, ordered by `match_score` from highest to lowest. If fewer volunteers are eligible, the array is shorter. The endpoint returns that stored order. It does not reorder the list.

The React screen shows the first three matches. **Show More** reveals the remaining stored matches, and only when the array has more than three. That limit of three is a presentation choice. The API still returns the full stored list, up to six.

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

It does not perform the entire AI matching process synchronously as part of the HTTP request. It does not approve or reject the volunteering request.

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

PUT /volunteers/me/categories
        ↓
UpdateVolunteerCategories

PUT /volunteers/me/availability
        ↓
UpdateVolunteerAvailability

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
GET /volunteers/me/categories
        ↓
GetVolunteerCategories

GET /volunteers/me/availability
        ↓
GetVolunteerAvailability

GET /volunteers
        ↓
SearchVolunteers

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