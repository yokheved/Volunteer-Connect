# System Features

## Overview

VolunteerConnect provides functionality for two user roles:

- CLIENT
- VOLUNTEER

A single registered user may have one or both roles.

The following sections describe the main system features.

---

# Authentication

## Registration

A new user can create an account using personal information such as:

- Name
- Email
- Password
- Phone
- Address

During registration or profile configuration, the user may choose:

- CLIENT
- VOLUNTEER
- both roles

---

## Login

Registered users can authenticate using their account credentials.

After authentication, the available functionality is determined by their roles.

---

## Logout

Authenticated users can end their current session by logging out.

Logout revokes the current access token in this application process using an in-memory blocklist. Revocation is not stored in the database and does not persist across process restarts or multiple server processes. The token also expires on its own after its configured lifetime.

---

# User Profile

Users can view and update their personal information.
Before any update, the user must enter his current password.

Possible editable fields include:

- Name
- Phone
- Address
- Roles

Volunteer-specific profile fields include:

- About Me
- Monthly volunteering-hours goal
- Volunteering categories
- Availability

## Change Password

Authenticated users can change their account password.

To change the password, the user must:

1. Enter a new password.
2. Confirm the new password.

The system verifies that the current password is correct and that the new password meets the password requirements.

If validation succeeds, the password is securely hashed and updated in the system.

If the current password is incorrect or the new passwords do not match, an appropriate error message is displayed.

The user's existing password is never stored or exposed in plain text.

### Google Maps Address Autocomplete

When a user registers or updates their address, the system must use Google Maps Places Autocomplete to provide real-time address suggestions.

- Users must select an address from Google's suggestions rather than submitting arbitrary free-text input.
- After selecting an address, the system retrieves the corresponding Google Place ID and geographic coordinates.
- The selected location is associated with the user's profile.
- The address field must be validated before saving.
- If the user edits the address after selecting a suggestion, they must select a valid suggestion again.
- The stored location information will support future volunteer matching and the `check_location_distance` MCP Tool.

The integration should use Google Maps Platform and follow its API usage and data storage policies.

---

# Volunteer Features

## Volunteer Categories

Volunteers can select the types of volunteering activities they are interested in.

Examples may include:

- Elderly Assistance
- Transportation
- Shopping
- Tutoring
- Technical Help
- Childcare Support
- Cooking
- Cleaning

A volunteer may select multiple categories.

---

## Availability

Volunteers can define recurring availability.

For example:

```text
Monday:    09:00–13:00
Wednesday: 16:00–20:00
Friday:    09:00–12:00
```

Availability is used during volunteer search and AI matching.

---

## About Me

Volunteers can write a free-text description containing information such as:

- Volunteering interests
- Previous experience
- Relevant abilities
- Preferred volunteering activities

This text can also be embedded into the vector database and used by the RAG system.

---

## Monthly Goal

A volunteer can define a target number of volunteering hours per month.

Example:

```text
Monthly goal: 20 hours
Completed:    12 hours
Remaining:     8 hours
```

Only completed volunteering activities count toward this goal.

---

## Volunteer Dashboard

The volunteer dashboard displays:

- Monthly-hours goal
- Completed hours
- Remaining hours
- Progress indicator
- Upcoming volunteering activities
- Next volunteering activity
- Pending volunteering requests
- Schedule

---

## Request Approval

When a client sends a volunteering request, the volunteer can:

```text
APPROVE
```

or:

```text
REJECT
```

The system updates the request status accordingly.

---

# Client Features

## Volunteer Search

Clients can search for volunteers using structured criteria.

Possible filters include:

- Volunteering category
- Date
- Time
- Availability
- Location

The search may later be enhanced using semantic matching results.

---

## Volunteer Profile

Clients can view relevant volunteer information before sending a request.

Information may include:

- Name
- City and country
- Volunteering categories
- Availability
- About Me
- Relevant AI matching information

Street, building number, and other sensitive account information are not exposed.

---

## Create Volunteering Request

A client can send a volunteering request to a volunteer.

The request includes:

```text
Volunteer
Category
Location
Date
Start time
Duration
Description
```

Start time is chosen from the volunteer's saved availability windows. The selected date must fall on that window's weekday.

A new request starts with:

```text
PENDING
```

---

## Client Dashboard

The client dashboard displays:

- Upcoming volunteering activity
- Pending requests
- Approved requests
- Completed volunteering activities
- Schedule

---

# Volunteering Request Lifecycle

The request lifecycle is:

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

---

# AI Volunteer Matching

The system includes a Deep Agent that evaluates volunteer suitability.

The AI matching system is not intended to replace the volunteer's approval decision.

Its purpose is to identify and explain potentially strong matches.

---

## Structured Candidate Filtering

Before AI processing, the system filters volunteers using structured data.

Typical filters include:

- Category
- Availability
- Location

This reduces the number of candidates passed to the semantic matching stage.

---

## Semantic Matching

The system uses RAG and a vector database to compare volunteering requests with semantic volunteer information.

Possible volunteer information includes:

- About Me
- Experience
- Volunteering interests
- Previous volunteering descriptions

Example:

```text
Task:
Help an elderly person buy groceries.

Volunteer:
I enjoy assisting senior citizens with errands and shopping.
```

The system can identify the semantic relationship even when the wording is different.

---

## Matching Report

The agent produces a result explaining the suitability of a volunteer.

Example:

```text
Match Score: 91%

Category:       Match
Availability:   Match
Location:       Suitable
Semantic Match: High

Reason:
The volunteer is available at the requested time and has
experience assisting elderly people with shopping and errands.
```

The report is stored and can be displayed in the application.

---

# Location Distance Tool

The custom MCP tool:

```text
check_location_distance
```

is used by the agent to evaluate geographical suitability.

It compares:

```text
Volunteer location
        │
        ▼
Volunteering task location
```

The result helps the agent determine whether the candidate is realistically located near the requested task.

---

# Match Notification Tool

The custom MCP tool:

```text
send_match_notification
```

is used when the agent identifies an appropriate volunteer match.

The tool sends a notification or email containing relevant volunteering information.

Receiving such a notification does not mean that the volunteering request has been approved.

The volunteer still chooses whether to approve or reject the request.

---

# Tavily Integration

The Deep Agent may use Tavily through MCP when external up-to-date information is needed.

Tavily is an external search capability and is not one of the two MCP tools developed by the project team.

It is used only when the matching process requires additional external context.

---

# Event History

Important system actions generate domain events.

Examples include:

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

This provides an auditable history of important changes.

---

# Role-Based Access

Functionality is restricted according to user roles.

Examples:

| Feature | CLIENT | VOLUNTEER |
|---|---:|---:|
| Search volunteers | Yes | No |
| Send request | Yes | No |
| Set availability | No | Yes |
| Set monthly goal | No | Yes |
| Approve request | No | Yes |
| Reject request | No | Yes |
| View personal profile | Yes | Yes |
| Update personal profile | Yes | Yes |

A user who has both roles can access both sets of functionality.

---

# Scope

The project intentionally focuses on the core volunteering workflow.

Features such as:

- Payments
- Public social networks
- Complex reputation systems
- Advanced messaging systems
- Large administrative portals

are currently outside the project scope unless they become necessary for course requirements.

The goal is to demonstrate the required software-engineering and AI concepts without unnecessary complexity.