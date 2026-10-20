# Data Model

## Overview

VolunteerConnect uses a relational database for structured application data.

The main entities are:

```text
User
VolunteerCategory
Availability
VolunteerRequest
DomainEvent
```

Additional tables may be added during implementation for AI matching results or vector-document references.

---

# User

The `User` entity represents every registered user in the system.

A single account may act as:

- CLIENT
- VOLUNTEER
- both CLIENT and VOLUNTEER

```text
users
------------------------
id
name
email
password_hash
phone
address
google_place_id
latitude
longitude
location_cached_at
is_client
is_volunteer
monthly_hours_goal
about_me
created_at
```

## Fields

| Field | Description |
|---|---|
| id | Unique user identifier |
| name | User's display name |
| email | Login email |
| password_hash | Secure password hash |
| phone | User phone number |
| address | String Human-readable address selected through Google Maps Places Autocomplete |
| google_place_id | String Google Maps Place ID identifying the selected location. Stored permanently. |
| latitude | Decimal Geographic latitude of the selected location |
| longitude | Decimal Geographic longitude of the selected location |
| location_cached_at | Timestamp when latitude and longitude were last stored |
| is_client | Indicates CLIENT role |
| is_volunteer | Indicates VOLUNTEER role |
| monthly_hours_goal | Monthly volunteering goal |
| about_me | Free-text volunteer description |
| created_at | Account creation timestamp |

`monthly_hours_goal` and `about_me` are mainly relevant when the user has the VOLUNTEER role.

**Location rules:**

- Users select their address through Google Maps Places Autocomplete.
- The Google Place ID identifies the selected location.
- Latitude and longitude are used for geographic distance calculations.
- When a user changes their address, the associated location information must be updated consistently.
- The location information is shared across all roles of the same User.
- Location changes should be reflected in the system's Event Sourcing mechanism.

**Google Maps data policy:** Place IDs may be stored permanently. `address` is the formatted address the user confirmed for that account; it is not a shared geocoding cache. `latitude` and `longitude` are stored with `location_cached_at`. Google's current Places terms allow coordinates to be cached for 30 consecutive calendar days, after which they must be deleted. A later matching step may send the stored Place ID to Google Maps Grounding Lite, which the Deep Agent calls. This profile feature only records the timestamp; it does not refresh coordinates or call that MCP service. Do not draw these coordinates on a non-Google map. Showing the formatted address as text is allowed.

---

# VolunteerCategory

This table stores the volunteering categories selected by each volunteer.

```text
volunteer_categories
------------------------
volunteer_id
category
```

Examples of categories:

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

The allowed category list is those eight strings.

A volunteer may select multiple categories.

Example:

```text
Volunteer 14
├── Transportation
├── Shopping
└── Elderly Assistance
```

`volunteer_id` references:

```text
users.id
```

---

# Availability

The `Availability` entity represents the recurring times during which a volunteer is available.

```text
availability
------------------------
id
volunteer_id
day_of_week
start_time
end_time
```

## Fields

| Field | Description |
|---|---|
| id | Availability record identifier |
| volunteer_id | Volunteer user |
| day_of_week | Day of week |
| start_time | Start of available time |
| end_time | End of available time |

Example:

```text
volunteer_id: 14
day_of_week: MONDAY
start_time: 09:00
end_time: 13:00
```

A volunteer may have multiple availability records.

---

# VolunteerRequest

The `VolunteerRequest` entity represents a request sent by a client to a volunteer.

```text
volunteer_requests
------------------------
id
client_id
volunteer_id
category
date
start_time
duration
location
google_place_id
latitude
longitude
location_cached_at
description
status
created_at
```

## Fields

| Field | Description |
|---|---|
| id | Unique request identifier |
| client_id | User requesting assistance |
| volunteer_id | Requested volunteer |
| category | Volunteering category |
| date | Requested date |
| start_time | Starting time |
| duration | Expected duration |
| location | Task location (the client's formatted address at creation time) |
| google_place_id | Copied from the client at creation time |
| latitude | Copied from the client at creation time |
| longitude | Copied from the client at creation time |
| location_cached_at | Copied from the client at creation time; this copy does not start a new 30-day cache |
| description | Free-text task description |
| status | Current request state |
| created_at | Request creation timestamp |

`client_id` and `volunteer_id` both reference:

```text
users.id
```

`location`, `google_place_id`, `latitude`, `longitude`, and `location_cached_at` are copied from the client when the request is created. They are not typed in the request body and are not selected again through Google Places.

---

# Volunteer Request Status

A volunteering request has one of the following states:

```text
PENDING
APPROVED
REJECTED
COMPLETED
```

The normal lifecycle is:

```text
PENDING
   │
   ├───────────────┐
   ▼               ▼
APPROVED         REJECTED
   │
   ▼
COMPLETED
```

A newly created request starts as:

```text
PENDING
```

The assigned volunteer may change it to:

```text
APPROVED
```

or:

```text
REJECTED
```

An approved request becomes:

```text
COMPLETED
```

after the volunteering activity has been performed.

Completed duration contributes to the volunteer's monthly-hours progress.

---

# Domain Events

The project uses Event Sourcing for important state-changing actions.

A domain event record may contain:

```text
domain_events
------------------------
id
aggregate_type
aggregate_id
event_type
event_data
created_at
```

## Fields

| Field | Description |
|---|---|
| id | Event identifier |
| aggregate_type | Type of domain entity |
| aggregate_id | Entity affected by the event |
| event_type | Name of the event |
| event_data | Event-specific data |
| created_at | Event creation timestamp |

`event_data` may be stored as JSON.

Example:

```json
{
  "request_id": 27,
  "client_id": 4,
  "volunteer_id": 14,
  "status": "PENDING"
}
```

Possible event types include:

```text
UserRegistered
UserProfileUpdated
VolunteerCategoriesUpdated
VolunteerAvailabilityUpdated
VolunteerRequestCreated
VolunteerRequestApproved
VolunteerRequestRejected
VolunteerRequestCompleted
```

---

# AI Matching Results

The Deep Agent produces matching results that should be available to the application.

A possible table is:

```text
matching_results
------------------------
id
request_id
volunteer_id
match_score
report
created_at
```

## Fields

| Field | Description |
|---|---|
| id | Match result identifier |
| request_id | Related volunteering request |
| volunteer_id | Evaluated volunteer |
| match_score | Agent-generated compatibility score |
| report | Explanation of the match |
| created_at | Matching timestamp |

This table is optional until the AI matching implementation is built, but some persistent representation of the matching report will be required because the report is displayed in the UI.

The agent stores at most six rows for one request, highest `match_score` first. The API returns that ranked list. Showing only the first three until the client chooses **Show More** is a frontend choice and does not need another column.

Travel times used by `check_volunteer_schedule` are inputs the agent passes at runtime. They are not a column on this table. The written `report` can explain the travel and schedule result. A separate column for the numeric travel time would be a later data-model change.

---

# Vector Data

Semantic text is stored in the vector database rather than directly replacing relational data.

Possible vector documents include:

```text
Volunteer About Me
Volunteer experience
Previous volunteering descriptions
Volunteering request descriptions
```

Each vector record should retain a reference to the corresponding relational entity.

Conceptually:

```text
vector_document
------------------------
id
entity_type
entity_id
text
embedding
```

Example:

```text
entity_type = VOLUNTEER_PROFILE
entity_id = 14
```

The relational database remains the source of structured application information.

The vector database is used only for semantic retrieval.

---

# Relationships

```text
                    User
                ┌────┴────┐
                │         │
             Client    Volunteer
                │         │
                │         ├──────── VolunteerCategory
                │         │
                │         └──────── Availability
                │
                └──────── VolunteerRequest ─────── Volunteer
                              │
                              │
                              └──────── MatchingResult
```

More explicitly:

```text
User 1 ─── N VolunteerCategory

User 1 ─── N Availability

User(client) 1 ─── N VolunteerRequest

User(volunteer) 1 ─── N VolunteerRequest

VolunteerRequest 1 ─── N MatchingResult
```

---

# Data Separation

VolunteerConnect uses two types of storage.

## Relational Database

Used for:

- Users
- Authentication-related data
- Roles
- Availability
- Categories
- Requests
- Status
- Event history
- Matching reports

## Vector Database

Used for:

- Embeddings
- Semantic similarity
- RAG retrieval

The same information does not need to be fully duplicated in both systems.

The vector database stores only the text and metadata required for semantic search.

---

# Current Hosting Decision

The main cloud operational database is Microsoft SQL Server hosted using Somee.com.

The vector database is handled separately because vector support depends on the selected service and database compatibility.

The exact vector-storage implementation may change without affecting the logical data model described in this document.