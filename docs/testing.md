# Testing Strategy

## Overview

VolunteerConnect will include automated tests for the main application workflows.

Testing focuses primarily on:

- Authentication
- Authorization
- Business rules
- CQRS handlers
- Request lifecycle
- Database operations
- AI integration boundaries

The goal is to test important behavior without creating unnecessary testing complexity for the scope of the project.

---

# Backend Testing

Backend tests will be written using Python testing tools compatible with Flask.

The tests should verify both successful operations and important failure cases.

---

# Authentication Tests

Test scenarios include:

```text
Register valid user
Reject duplicate email
Login with valid credentials
Reject invalid credentials
Access protected endpoint without authentication
```

---

# Role Authorization Tests

The system supports:

```text
CLIENT
VOLUNTEER
CLIENT + VOLUNTEER
```

Important tests include:

```text
CLIENT can search volunteers
CLIENT can create request
CLIENT cannot approve request

VOLUNTEER can manage availability
VOLUNTEER can approve assigned request
VOLUNTEER cannot approve another volunteer's request

User with both roles can access both feature sets
```

---

# Volunteer Request Tests

The request lifecycle is:

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

Tests should verify valid transitions:

```text
PENDING → APPROVED
PENDING → REJECTED
APPROVED → COMPLETED
```

Tests should also verify that invalid transitions are rejected.

Examples:

```text
REJECTED → COMPLETED     ✗
COMPLETED → APPROVED     ✗
PENDING → COMPLETED      ✗
```

---

# Command Tests

Important command handlers should be tested independently where practical.

Examples:

```text
RegisterUserCommand
UpdateVolunteerAvailabilityCommand
CreateVolunteerRequestCommand
ApproveVolunteerRequestCommand
RejectVolunteerRequestCommand
CompleteVolunteerRequestCommand
```

A command test should verify:

1. Input is validated.
2. Correct state change occurs.
3. Appropriate domain event is generated when required.

---

# Query Tests

Important query handlers include:

```text
SearchVolunteersQuery
GetVolunteerDetailsQuery
GetVolunteerDashboardQuery
GetClientDashboardQuery
GetPendingRequestsQuery
```

Query tests should verify that:

- Correct records are returned.
- Unauthorized information is not returned.
- Filters work correctly.
- Queries do not modify application state.

---

# Event Sourcing Tests

Important state-changing actions should create the expected domain events.

Example:

```text
CreateVolunteerRequest
        │
        ▼
VolunteerRequestCreated
```

Approving the request should produce:

```text
VolunteerRequestApproved
```

Completing the request should produce:

```text
VolunteerRequestCompleted
```

Tests should verify that event information references the correct domain entity.

---

# Monthly Goal Tests

Completed volunteering hours are used to calculate monthly progress.

Example:

```text
Monthly Goal:       20
Completed Requests: 12 hours
Remaining:           8 hours
Progress:           60%
```

Only `COMPLETED` volunteering activities should contribute to completed hours.

Pending, approved, and rejected requests should not count toward the completed-hours total.

---

# Volunteer Search Tests

Structured volunteer search should test:

- Category filtering
- Availability filtering
- Location-related filtering
- Multiple filters together
- No matching volunteers

Example:

```text
Requested category: Shopping
Requested time: Monday 10:00

Volunteer A:
Shopping ✓
Monday 09:00–13:00 ✓

Volunteer B:
Shopping ✓
Monday 14:00–18:00 ✗
```

Only Volunteer A should pass the availability filter.

---

# RAG Tests

RAG tests should verify that semantic retrieval can identify relevant volunteer information.

Example:

```text
Request:
Help an elderly person with grocery shopping.

Volunteer profile:
I regularly assist senior citizens with errands.
```

The system should be capable of retrieving the volunteer profile as semantically relevant.

Testing does not require an exact AI response string.

The important behavior is that relevant information is retrieved and supplied to the matching process.

---

# Deep Agent Tests

The Deep Agent should be tested at the workflow level.

A matching test can verify that the agent:

1. Receives a volunteering request.
2. Uses structured candidate filtering.
3. Retrieves semantic context through RAG.
4. Evaluates candidate information.
5. Uses location information when required.
6. Produces a matching result.
7. Stores the matching report.
8. Requests notification when an appropriate match is found.

AI-generated wording should not be tested using exact string equality.

Tests should focus on expected structure and workflow behavior.

---

# MCP Tool Tests

## check_location_distance

Tests should verify that the tool receives appropriate locations and returns information in the expected format.

External services may be mocked during automated tests.

---

## send_match_notification

Tests should verify that:

- Correct volunteer is targeted.
- Correct volunteering information is supplied.
- Notification is requested only when appropriate.

Automated tests should not send real emails every time the test suite runs.

The external email operation should therefore be mocked or replaced with a test implementation.

---

# API Tests

Important REST endpoints should be tested using the Flask test client.

Example scenarios:

```text
POST /api/auth/register
POST /api/auth/login

GET /api/volunteers
POST /api/requests

POST /api/requests/{id}/approve
POST /api/requests/{id}/reject

GET /api/dashboard/volunteer
GET /api/dashboard/client
```

Tests should verify:

- HTTP status code
- Response structure
- Database state
- Authorization

---

# Frontend Testing

Frontend testing will focus on important user flows rather than exhaustive UI testing.

Important flows include:

```text
Login
Volunteer search
Create volunteering request
Approve/reject request
Dashboard display
```

The exact frontend testing tools will be selected during implementation if required.

---

# Manual End-to-End Test

Before final submission, the complete workflow should be tested manually.

Example scenario:

```text
1. Register Volunteer A.

2. Volunteer A:
   - selects categories
   - defines availability
   - writes About Me
   - defines monthly goal

3. Register Client B.

4. Client B:
   - searches for a volunteer
   - views Volunteer A
   - creates a volunteering request

5. Verify:
   - request status = PENDING
   - agent can evaluate the match
   - matching result is stored
   - notification process can be triggered

6. Volunteer A:
   - views pending request
   - approves request

7. Verify:
   - status = APPROVED

8. Complete the volunteering activity.

9. Verify:
   - status = COMPLETED
   - volunteer dashboard hours are updated
   - monthly progress is updated
```

This scenario covers the primary business flow of VolunteerConnect.

---

# Testing Scope

The project prioritizes tests for important business rules and architectural requirements.

The testing strategy intentionally avoids excessive test infrastructure that would add complexity without improving the educational goals of the project.