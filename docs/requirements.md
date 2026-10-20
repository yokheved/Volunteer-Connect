# System Requirements

## Roles
- CLIENT
- VOLUNTEER
- A user may have one or both roles.

## Authentication
- Register
- Login
- Logout

## Volunteer
- Update profile
- Select volunteering categories
- Define availability
- Define monthly volunteering-hours goal
- View dashboard
- Approve/reject volunteering requests

## Client
- Update profile
- Search volunteers
- View volunteer details
- Send volunteering request
- View dashboard

## Volunteer Request
Status:
- PENDING
- APPROVED
- REJECTED
- COMPLETED

## AI matching
- A background Deep Agent ranks eligible volunteers and stores at most six matches, highest score first.
- The agent uses RAG, `get_volunteer_history`, `check_volunteer_schedule`, Google Maps Grounding Lite, and Tavily when needed.
- The agent does not approve or reject requests and does not send email.
- The client UI shows the first three stored matches, then **Show More** for any remaining matches.

## Non-functional
- The backend writes request, application, and error logs to rotating files.
- Passwords and tokens are not written to those logs.