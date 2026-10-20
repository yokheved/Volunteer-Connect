# VolunteerConnect

VolunteerConnect is a smart volunteer coordination platform designed to connect people who need assistance with volunteers who are available, nearby, and interested in the relevant type of volunteering.

The system allows users to act as **clients**, **volunteers**, or both under a single account. Clients can search for suitable volunteers and send volunteering requests, while volunteers manage their interests and availability, approve or reject requests, and track their monthly volunteering goals.

An AI-based matching agent enhances the matching process by combining structured data such as availability, location, and volunteering categories with semantic information retrieved using RAG and a vector database.

---

## 🎯 Project Goals

The goal of VolunteerConnect is to simplify the process of finding suitable volunteers while providing volunteers with an organized way to manage their activities and track their contribution.

The system focuses on:

- Connecting clients with suitable volunteers
- Matching by volunteering category, availability, and location
- Managing volunteering requests and approvals
- Tracking completed volunteering hours
- Providing personalized dashboards
- Using AI and semantic search to improve volunteer matching

---

## 👥 User Roles

VolunteerConnect uses a single user account system with role-based functionality.

A user may have one or both of the following roles:

### Volunteer

A volunteer can:

- Update personal information such as name, phone number, and address
- Select preferred volunteering categories
- Define volunteering availability
- Write a short personal description about volunteering interests and experience
- Set a monthly volunteering-hours goal
- Receive volunteering requests from clients
- Approve or reject volunteering requests
- View upcoming volunteering activities
- Track completed volunteering hours

### Client

A client can:

- Update personal information
- Search for volunteers
- Filter volunteers by:
  - Volunteering category
  - Availability
  - Location
- View volunteer details
- Send a volunteering request
- Track pending and approved requests
- View upcoming volunteering activities

### Multiple Roles

A user does not need to create separate accounts in order to volunteer and request assistance.

For example:

```text
User
├── CLIENT
└── VOLUNTEER
```

Authorization and available functionality are determined according to the user's active roles.

---

## 📅 Volunteering Request Flow

A client searches for a suitable volunteer and sends a request containing:

- Volunteering category
- Date and time
- Location
- Expected duration
- Description

The request then follows the following lifecycle:

```text
Request Created
      │
      ▼
   PENDING
      │
      ├───────────────┐
      ▼               ▼
   APPROVED        REJECTED
      │
      ▼
  COMPLETED
```

A volunteering activity is counted toward the volunteer's monthly goal only after it has been completed.

---

## 📊 Dashboards

### Volunteer Dashboard

The volunteer dashboard provides an overview of the volunteer's activity.

It includes:

- Monthly volunteering goal
- Completed volunteering hours
- Remaining hours
- Circular progress indicator
- Upcoming volunteering activity
- Volunteering schedule
- Pending requests requiring approval

Example:

```text
Monthly Goal

       12 / 20 hours
          ◯ 60%

8 hours remaining
```

### Client Dashboard

The client dashboard includes:

- Upcoming volunteering activity
- Pending requests
- Approved requests
- Completed volunteering activities
- Volunteering schedule

Summary cards provide a quick overview of the client's current requests.

---

## 🔎 Volunteer Search

Clients can search for volunteers based on structured criteria such as:

- Volunteering category
- Requested date and time
- Location

The system first filters volunteers according to these requirements.

Potential matches can then be evaluated by the AI matching process to provide more meaningful recommendations.

---

## 🤖 AI Volunteer Matching Agent

VolunteerConnect includes an independent Deep Agent that runs as a separate background process and is responsible for evaluating potential volunteer matches.

The agent processes volunteering requests and relevant volunteer information and evaluates the suitability of potential volunteers.

The Deep Agent manages the matching workflow as follows:

1. A client submits a new volunteering request through the application.
2. Flask saves the request in the cloud-hosted database (Somee.com), using the existing Event Sourcing design.
3. Structured filtering keeps candidates by category, general availability, and the other stored criteria.
4. The agent uses RAG and the vector database to judge semantic relevance.
5. The agent calls `get_volunteer_history` for completed work and related experience.
6. The agent calls Google Maps Grounding Lite MCP for travel distance and estimated travel time.
7. The agent passes those travel times to `check_volunteer_schedule`, which looks for conflicts with approved commitments.
8. The agent uses Tavily through MCP when additional external information is relevant.
9. The agent ranks eligible volunteers by semantic relevance, experience, geography, and schedule feasibility.
10. The agent keeps at most six volunteers, highest match score first, and writes a reasoned report.
11. The matching results and report are saved and shown in the UI. The screen lists the top three first. **Show More** reveals the rest only when more than three were saved.

The volunteer still approves or rejects volunteering requests. The agent does not send email.

The matching process may consider:

1. Volunteer availability
2. Selected volunteering categories
3. Location and distance
4. Volunteer profile and interests
5. Relevant previous volunteering experience
6. Semantic similarity between the request and volunteer information

The agent can combine information from:

- The relational database
- A vector database using RAG
- External services through MCP: Tavily for web search, and Google Maps Grounding Lite for travel time

A possible result:

```text
Volunteer Match Score: 91%

Availability:        ✓
Category Match:      ✓
Location:            ✓
Semantic Match:      High

Recommendation:
Highly suitable volunteer for this request.
```

---

## 🧠 RAG & Semantic Search

Structured information such as availability and categories is stored and queried using the relational database.

Free-text information can be embedded and stored in a vector database, including:

- Volunteer "About Me" descriptions
- Volunteering interests
- Relevant volunteering experience
- Descriptions of previous volunteering activities

Example volunteer description:

> I enjoy helping elderly people with shopping and errands. I have a car and previous volunteering experience assisting seniors.

A client request such as:

> I need someone to help me with grocery shopping.

can therefore be semantically matched with relevant volunteers even when the exact same keywords are not used.

The RAG layer provides relevant semantic context to the AI agent when evaluating a match.

---

## 🗄️ Data Model

The main entities include:

### Users

```text
users
-----
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
```

### Volunteer Categories

```text
volunteer_categories
--------------------
volunteer_id
category
```

### Volunteer Availability

```text
availability
------------
id
volunteer_id
day_of_week
start_time
end_time
```

### Volunteering Requests

```text
volunteer_requests
------------------
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

Request status can be:

```text
PENDING
APPROVED
REJECTED
COMPLETED
```

---

## 🏗️ Architecture

The backend is implemented using **Flask** and organized according to **CQRS/MVC principles**.

### CQRS

Commands are responsible for operations that change the system state, such as:

- Create volunteering request
- Approve request
- Reject request
- Complete volunteering activity
- Update volunteer availability
- Update volunteering preferences

Queries are responsible for retrieving information, such as:

- Search volunteers
- Get volunteer details
- Get pending requests
- Get volunteer dashboard
- Get client dashboard

Example:

```text
                  Flask API
                      │
             ┌────────┴────────┐
             │                 │
          Commands           Queries
             │                 │
             ▼                 ▼
       Command Handlers    Query Handlers
             │                 │
             └────────┬────────┘
                      ▼
                  Database
```

### Logging

The Flask backend writes rotating files under `backend/logs/`:

- `access.log` — one line per HTTP request
- `app.log` — application messages
- `error.log` — errors and unhandled exceptions

These files are operational logs, not domain events.

---

## 📝 Event Sourcing

Important state-changing actions are represented as domain events.

Examples:

```text
UserRegistered
VolunteerProfileUpdated
AvailabilityUpdated
VolunteeringRequestCreated
VolunteeringRequestApproved
VolunteeringRequestRejected
VolunteeringCompleted
```

These events provide a history of important changes in the system and support the Event Sourcing architecture.

---

## 🔐 Authentication & Authorization

Users must authenticate before accessing protected system functionality.

Authentication is handled by the Flask backend.

Authorization is role-based:

```text
CLIENT
VOLUNTEER
CLIENT + VOLUNTEER
```

The same authenticated user can therefore access both client and volunteer functionality when both roles are enabled.

---

## 🛠️ Technology Stack

### Frontend

- React
- Vite
- JavaScript / TypeScript
- Responsive UI

### Backend

- Python
- Flask
- REST API
- CQRS / MVC architecture

### Database

- Microsoft SQL Server
- Cloud-hosted operational database (Somee.com)

### Vector Search

- PostgreSQL with pgvector or another compatible vector database
- Embeddings
- Semantic similarity search
- RAG

### AI

- Deep Agent (separate background matching process)
- Retrieval-Augmented Generation (RAG)
- AI-based volunteer matching

### External Services

External services can be accessed through **MCP (Model Context Protocol)**.

Two custom MCP tools will be developed for the project: `check_volunteer_schedule` and `get_volunteer_history`. Tavily and Google Maps Grounding Lite are external MCP services. They are not custom tools. Google Places Autocomplete in the web app is separate from these MCP tools.

### Development

- Git
- GitHub
- Markdown-based specification documents
- AI-assisted development workflow

---

## 🔧 MCP Tools

The project includes two custom MCP tools. Semantic matching stays in the RAG layer. Travel time comes from Google Maps Grounding Lite, which the agent calls itself.

```text
check_volunteer_schedule(...)
get_volunteer_history(...)
```

`check_volunteer_schedule` decides whether a volunteer can take the task without conflicting with approved commitments. It uses start times, durations, and travel times the agent supplies. Home location is used when there is no earlier task. Consecutive tasks include travel from the previous task and onward to the next approved task. The tool does not call Google Maps.

`get_volunteer_history` returns completed tasks, categories, relevant experience, and participation statistics from existing records. The agent combines that history with RAG.

**Tavily** is an external web-search MCP service. The agent uses it when matching needs up-to-date outside information. It is not a custom tool.

**Google Maps Grounding Lite** is Google's official MCP service at `https://mapstools.googleapis.com/mcp`. The agent calls `compute_routes` with stored Place IDs where a waypoint allows it. Results are distance and estimated duration, not live traffic. The API key is `GOOGLE_MAPS_MCP_API_KEY` on the Python agent. Google's current Essentials list includes 10,000 free Grounding Lite requests per month, then usage-based billing. Confirm the current price before a deployment that may exceed that cap.

---

## 📁 Proposed Project Structure

```text
VolunteerConnect/
│
├── backend/
│   ├── app/
│   │   ├── commands/
│   │   ├── queries/
│   │   ├── models/
│   │   ├── services/
│   │   ├── agents/
│   │   ├── rag/
│   │   └── routes/
│   │
│   ├── tests/
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   └── hooks/
│   └── package.json
│
├── docs/
│   ├── requirements.md
│   ├── architecture.md
│   ├── database.md
│   ├── api.md
│   └── testing.md
│
├── skills/
├── rules/
│
└── README.md
```

---

## 🚀 Main Features

- User registration and authentication
- Client and volunteer roles
- Multiple roles per account
- Volunteer profiles
- Volunteering categories
- Volunteer availability management
- Volunteer search and filtering
- Volunteering request creation
- Request approval/rejection
- Volunteering schedule
- Monthly volunteering goal tracking
- Client dashboard
- Volunteer dashboard
- AI volunteer matching
- Semantic search
- RAG
- Vector database integration
- MCP tools
- CQRS/MVC architecture
- Event Sourcing

---

## 📌 Project Status

🚧 Currently under development.

### Our Workflow

        ┌── Plan Agent ───────────┐
        │   plans the feature     │
        └────────────┬────────────┘
                     ↓
        ┌── Build Agent ──────────┐
        │   implements feature    │
        │   using the Skill       │
        └────────────┬────────────┘
                     ↓
             Code Review Agent
                     ↓
              Review findings
                     ↓
                    YOU
          accept / reject / modify
                     ↓
          Original Build Agent
             implements fixes
                     ↓
                  Tests
                     ↓
              Debug Agent
          investigates failures
          and fixes actual bugs
                     ↓
                  Tests
                     ↓
               Final Review
                     ↓
                  Commit

---

## 👩‍💻 Authors

### [Yokheved Rose](mailto:yokheved.rose@gmail.com)
### [Yael Rosenbom](mailto:glick.yael3@gmail.com)
Developed as a final project for the **Software Engineering in the AI Era** course at the Jerusalem College of Technology (JCT).