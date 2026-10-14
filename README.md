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
3. The system performs initial structured filtering, such as location and availability.
4. The agent uses RAG and the vector database to retrieve potential volunteers based on semantic compatibility.
5. The Deep Agent evaluates the candidates and may invoke `check_location_distance` to verify geographical compatibility.
6. The agent uses Tavily through MCP when additional external information is relevant.
7. The agent identifies the most suitable volunteer and produces a reasoned matching report.
8. When an appropriate match is identified, the agent invokes `send_match_notification` to notify the volunteer by email.
9. The matching results and report are saved back to the system and displayed in the UI.

The volunteer still approves or rejects volunteering requests.

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
- External services through MCP, including Tavily for internet search

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

Two custom MCP tools will be developed for the project: `send_match_notification` and `check_location_distance`. In addition, Tavily will be used through MCP as an external internet search tool. Tavily is not one of the two custom MCP tools.

### Development

- Git
- GitHub
- Markdown-based specification documents
- AI-assisted development workflow

---

## 🔧 MCP Tools

The project includes two custom MCP tools that allow the Deep Agent to perform external actions that complement RAG. Semantic matching remains the responsibility of the RAG layer, not of these tools.

```text
send_match_notification(...)
check_location_distance(...)
```

`send_match_notification` sends an automatic email to a volunteer when the Deep Agent identifies a highly suitable match between the volunteer and a volunteering request. The agent performs the matching using RAG and then invokes this tool to send the email with the relevant volunteering details. An email integration such as Gmail MCP may be used. This tool is responsible for the external notification action, not for semantic matching.

`check_location_distance` checks the geographical distance or travel compatibility between a volunteer's location and the volunteering request's location. The agent invokes this tool when evaluating potential volunteers identified through the matching process. This complements RAG because semantic search cannot reliably calculate real geographical distances.

In addition to these two custom MCP tools, the agent uses **Tavily** through MCP as an external internet search tool. Tavily is not one of the two MCP tools implemented by the project. The agent uses Tavily when external, up-to-date information is needed to enrich matching decisions, such as relevant guidelines, professional background, or environmental information.

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