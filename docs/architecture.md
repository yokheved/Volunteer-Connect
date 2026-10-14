# System Architecture

## Overview

VolunteerConnect is a web-based volunteer coordination system that connects clients who need assistance with volunteers who are available and suitable for the requested task.

The application follows a client-server architecture:

- **Frontend:** React + Vite
- **Backend:** Python + Flask
- **Relational Database:** Microsoft SQL Server hosted on Somee.com
- **Vector Database:** separate vector storage for semantic search and RAG
- **AI Matching:** background Deep Agent
- **External Integrations:** MCP tools and Tavily

The system is designed to remain simple enough for a small academic project while demonstrating the architectural concepts required by the course.

---

## High-Level Architecture

```text
                    ┌───────────────────┐
                    │    React Client   │
                    │     Frontend      │
                    └─────────┬─────────┘
                              │
                              │ HTTP / REST
                              ▼
                    ┌───────────────────┐
                    │       Flask       │
                    │      Backend      │
                    └─────────┬─────────┘
                              │
              ┌───────────────┼────────────────┐
              │               │                │
              ▼               ▼                ▼
        Command Layer     Query Layer      AI / Agent Layer
              │               │                │
              └───────┬───────┘                │
                      │                        │
                      ▼                        ▼
              Relational Database       Vector Database
                  Somee.com                   RAG
                      │                        │
                      └───────────┬────────────┘
                                  │
                                  ▼
                              Deep Agent
                                  │
                    ┌─────────────┼──────────────┐
                    ▼             ▼              ▼
          check_location_   send_match_        Tavily
             distance       notification       MCP
```

---

# Frontend

The frontend is implemented using React and Vite.

Its responsibilities include:

- User registration and login screens
- Client dashboard
- Volunteer dashboard
- Volunteer search
- Volunteer profile display
- Volunteering request creation
- Request approval and rejection
- Volunteer availability management
- Volunteer category management
- Displaying AI matching results

The frontend communicates with the Flask backend through REST API requests.

The frontend does not access the database directly.

---

# Backend

The backend is implemented using Flask.

Its responsibilities include:

- Authentication
- Authorization
- Business logic
- Validation
- REST endpoints
- Commands and queries
- Database access
- Event creation
- Starting or triggering matching processes

The backend acts as the central application layer between the frontend, databases, and AI components.

---

# MVC

The backend follows MVC principles.

## Model

The Model represents application data and database entities.

Examples:

- User
- VolunteerCategory
- Availability
- VolunteerRequest
- DomainEvent

## Controller

Flask routes act as controllers.

Controllers:

1. Receive HTTP requests.
2. Validate basic request data.
3. Invoke the appropriate command or query.
4. Return an HTTP response.

Business logic should not be implemented directly inside route functions.

## View

The React frontend acts as the presentation layer.

---

# CQRS

VolunteerConnect uses CQRS to separate operations that modify state from operations that retrieve data.

## Commands

Commands perform actions that change system state.

Examples:

```text
RegisterUser
UpdateUserProfile
UpdateVolunteerAvailability
UpdateVolunteerCategories
CreateVolunteerRequest
ApproveVolunteerRequest
RejectVolunteerRequest
CompleteVolunteerRequest
```

A typical command flow is:

```text
HTTP Request
     │
     ▼
Flask Route
     │
     ▼
Command
     │
     ▼
Command Handler
     │
     ▼
Database / Domain Event
```

## Queries

Queries retrieve information without modifying application state.

Examples:

```text
GetUserProfile
SearchVolunteers
GetVolunteerDetails
GetPendingRequests
GetVolunteerDashboard
GetClientDashboard
GetUpcomingVolunteering
```

A typical query flow is:

```text
HTTP Request
     │
     ▼
Flask Route
     │
     ▼
Query
     │
     ▼
Query Handler
     │
     ▼
Database
```

CQRS in this project does not require separate physical databases for commands and queries.

The separation is mainly implemented at the application architecture level.

---

# Event Sourcing

Important state-changing operations are represented as domain events.

Possible events include:

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

Events are stored so that the system keeps a historical record of important state changes.

For example:

```text
VolunteerRequestCreated
        │
        ▼
VolunteerRequestApproved
        │
        ▼
VolunteerRequestCompleted
```

The current application state can therefore be associated with the sequence of events that produced it.

For the scope of this project, Event Sourcing is implemented in a simplified form and is focused on important domain actions rather than every database operation.

---

# Relational Database

The main application data is stored in a Microsoft SQL Server relational database hosted on Somee.com.

It stores information such as:

- Users
- Roles
- Volunteer categories
- Volunteer availability
- Volunteering requests
- Request status
- Event history
- AI matching results

The backend accesses this database through the application data-access layer.

---

# Vector Database

Semantic information used by the AI matching process is stored separately in a vector database.

Possible embedded content includes:

- Volunteer About Me text
- Volunteer experience
- Previous volunteering descriptions
- Volunteering request descriptions

The vector database is used for semantic similarity search.

The final vector database technology depends on compatibility with the selected hosting environment.

---

# RAG

Retrieval-Augmented Generation is used to supply the AI agent with semantically relevant volunteer information.

The matching process is divided into two stages.

## Structured Filtering

The system first filters candidates using structured information such as:

- Volunteering category
- Availability
- Location

This prevents unnecessary semantic processing of clearly unsuitable candidates.

## Semantic Retrieval

RAG then searches embedded volunteer information to find candidates whose background, interests, or experience are semantically related to the volunteering request.

Example:

```text
Request:
Help an elderly person with grocery shopping.

Volunteer profile:
I regularly assist senior citizens with errands and transportation.
```

These texts may be considered similar even when they do not contain identical keywords.

---

# Deep Agent

The AI Volunteer Matching Agent runs as a separate background process.

Its responsibility is to evaluate potential volunteers for new volunteering tasks.

The process is:

```text
Client creates volunteering task
            │
            ▼
Flask stores task
            │
            ▼
Structured candidate filtering
            │
            ▼
RAG retrieval
            │
            ▼
Candidate evaluation
            │
            ▼
check_location_distance
            │
            ▼
Optional Tavily search
            │
            ▼
Matching decision and report
            │
            ▼
send_match_notification
            │
            ▼
Result saved in system
```

The agent may evaluate:

- Availability
- Category compatibility
- Geographic distance
- Volunteer interests
- Volunteer experience
- Semantic similarity

The agent produces a reasoned matching report.

The agent does not approve volunteering requests on behalf of volunteers.

The volunteer remains responsible for approving or rejecting a request.

---

# MCP

The project includes two custom MCP tools.

## `check_location_distance`

This tool evaluates geographical compatibility between:

- Volunteer location
- Volunteering task location

It may return information such as distance or estimated travel suitability.

This functionality is kept outside the RAG layer because vector similarity cannot accurately calculate geographical distance.

## `send_match_notification`

This tool sends a notification when the agent identifies a suitable match.

The notification may be delivered through an external email service.

The tool performs the notification action only.

It does not determine whether the volunteer is a suitable match.

---

# Tavily

Tavily is used through MCP as an external internet-search capability.

It may be called by the Deep Agent when current external information is needed.

Tavily is not one of the two MCP tools developed by the project team.

---

# Authentication and Authorization

Users authenticate through the Flask backend.

The system supports two roles:

```text
CLIENT
VOLUNTEER
```

A single user can have either role or both roles.

Example:

```text
User
├── CLIENT
└── VOLUNTEER
```

Authorization checks determine which operations the authenticated user may perform.

Examples:

- Only a client can create a volunteering request.
- Only the assigned volunteer can approve or reject the request.
- A volunteer can manage their own availability.
- Users may update only their own profiles.

---

# Logging

The backend writes operational logs to rotating files under `backend/logs/`. This is request and application monitoring. It is not Event Sourcing, and request log lines are not domain events.

The files are:

```text
access.log  — one line per HTTP request, including CORS preflight
app.log     — application messages at INFO and above
error.log   — ERROR and above, including unhandled exceptions
```

Each access line records timestamp, level, client IP, Origin (or `-`), method, URL path without the query string, and status code. Request bodies, the `Authorization` header, cookies, and JWTs are not logged.

Each file rotates at 1 MB and keeps 5 backups (about 6 MB per stream). Logging setup or write failures must not prevent the API from starting or returning a response.

---

# Main Architectural Principles

The project follows several principles:

- Keep Flask routes small.
- Keep business logic outside controllers.
- Separate commands from queries.
- Represent important state changes as events.
- Perform structured filtering before AI matching.
- Use RAG only where semantic matching is useful.
- Use MCP for external capabilities.
- Keep the project architecture understandable and suitable for the limited project scope.