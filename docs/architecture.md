# System Architecture

## Overview

VolunteerConnect is a web-based volunteer coordination system that connects clients who need assistance with volunteers who are available and suitable for the requested task.

The application follows a client-server architecture:

- **Frontend:** React + Vite
- **Backend:** Python + Flask
- **Relational Database:** Microsoft SQL Server hosted on Somee.com
- **Vector Database:** separate vector storage for semantic search and RAG
- **AI Matching:** background Deep Agent
- **External Integrations:** Tavily MCP and Google Maps Grounding Lite MCP

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
          ┌───────────────┬───────┴────────┬──────────────────┐
          ▼               ▼                ▼                  ▼
 get_volunteer_   check_volunteer_   Google Maps        Tavily
    history          schedule        Grounding Lite       MCP
                                     MCP
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

The AI Volunteer Matching Agent runs as a separate background process. It orchestrates matching. It does not approve or reject requests, and it does not send email.

The process is:

1. A client creates a volunteering request through React and Flask.
2. Flask persists the request with the existing command and Event Sourcing flow.
3. Structured filtering keeps candidates that match category, general availability, and the other search criteria already stored by the application.
4. The agent uses RAG and the vector database to judge semantic relevance.
5. The agent calls `get_volunteer_history` for completed work, categories, and participation statistics.
6. The agent calls Google Maps Grounding Lite MCP for the travel distances and estimated travel times it needs.
7. The agent passes those travel times to `check_volunteer_schedule`, which checks conflicts with existing `APPROVED` commitments.
8. The agent calls Tavily MCP only when it needs external, up-to-date information.
9. The agent ranks eligible volunteers by semantic relevance, relevant experience, geographical suitability, and scheduling feasibility.
10. The agent keeps at most six volunteers, highest match score first.
11. The agent writes a reasoned report for those recommendations.
12. The backend stores the results. The frontend reads them later. Matching is not done inside the HTTP request that created the volunteering request.

The volunteer still approves or rejects the request.

---

# MCP

The project develops exactly two custom MCP tools. Two external MCP services are used as well. Google Places Autocomplete in the React app is separate: it selects and stores a Place ID for a user or request. It is not one of these tools.

## `check_volunteer_schedule`

This custom tool decides whether a volunteer can do the requested task without a schedule conflict.

It looks at existing `APPROVED` commitments, including start times and durations. When the volunteer has no earlier task that matters, it uses the volunteer's home location. For back-to-back tasks, it considers travel from the previous task location to the requested task, and whether the volunteer can still reach the next approved task on time.

Travel times are an input. The Deep Agent obtains them from Google Maps Grounding Lite and passes them in. This tool does not call Google Maps.

It returns a structured result: whether the volunteer is available, and an explanation of any conflict.

The Flask backend still enforces request validation and status changes. This tool does not approve a request.

## `get_volunteer_history`

This custom tool reads a volunteer's history from existing records:

- Completed tasks
- Categories from that history
- Relevant experience
- Participation statistics derived from those records

The agent combines that structured history with RAG. The tool does not perform semantic search itself.

## Google Maps Grounding Lite MCP

This is Google's official MCP service, not a tool written for this project.

- Endpoint: `https://mapstools.googleapis.com/mcp`
- The Deep Agent calls it at runtime with `compute_routes`.
- `compute_routes` accepts an origin and a destination. Each waypoint may be an address, latitude and longitude, or a Place ID. Official documentation confirms direct Place ID support. Stored Place IDs from profiles and requests can be used where a waypoint is required.
- The agent chooses the routes: home to the task when there is no preceding task, previous task to the requested task, and the requested task to the next approved task when that next task exists.
- The agent then passes the travel times to `check_volunteer_schedule`. The map service and the schedule tool stay separate.
- `compute_routes` returns route distance and duration for driving or walking. Google's documentation states that Grounding Lite does not provide real-time traffic, turn-by-turn directions, or navigation. Do not treat the duration as a live-traffic or future-departure prediction.
- The Python agent uses a Google Cloud API key from the environment variable `GOOGLE_MAPS_MCP_API_KEY`. The key is not a Cursor MCP connection. The Maps Grounding Lite API must be enabled on that Google Cloud project.
- Google's current Essentials price list gives Maps Grounding Lite (SKU `8CD0-1602-5324`) 10,000 free requests per month, then usage-based billing. The first paid band is $7 per 10,000 requests. Pricing and terms can change; confirm them on Google's pricing page before relying on a bill.

## Tavily MCP

Tavily is an external web-search MCP service. The agent may call it when matching needs additional up-to-date information. It is not one of the two custom tools.

---

# Matching responsibilities

- **Google Maps Grounding Lite MCP** supplies distance and travel time.
- **Deep Agent** runs the workflow above, calls the external services, passes travel times into `check_volunteer_schedule`, ranks candidates, keeps at most six matches, and writes the explanations.
- **`check_volunteer_schedule`** judges schedule feasibility from commitments plus the travel times it was given. It does not call Google.
- **`get_volunteer_history`** returns structured history.
- **Flask** stores requests and matching results, exposes the APIs, and enforces business rules and status transitions.
- **React** shows the top three stored matches first. **Show More** reveals the rest, and only when more than three matches were stored. The client cannot see more than the six the agent saved. Fewer than six eligible volunteers means fewer rows, in the agent's order.

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
- Use the two custom MCP tools and the two external MCP services for matching.
- Keep the project architecture understandable and suitable for the limited project scope.