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
| address | User address/location |
| is_client | Indicates CLIENT role |
| is_volunteer | Indicates VOLUNTEER role |
| monthly_hours_goal | Monthly volunteering goal |
| about_me | Free-text volunteer description |
| created_at | Account creation timestamp |

`monthly_hours_goal` and `about_me` are mainly relevant when the user has the VOLUNTEER role.

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
```

The exact category list may be defined during implementation.

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
| location | Task location |
| description | Free-text task description |
| status | Current request state |
| created_at | Request creation timestamp |

`client_id` and `volunteer_id` both reference:

```text
users.id
```

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