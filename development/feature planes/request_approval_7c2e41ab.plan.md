---
name: Request approval and automatic close
overview: The assigned volunteer approves or rejects a PENDING request. Requests close automatically when their time passes (APPROVED → COMPLETED after the end time, PENDING → REJECTED after the start time). A "My requests" page shows both sides. Dashboards and AI matching stay later.
todos:
  - id: repo-time
    content: Status constants, request_time helpers, RequestRepository lookups and conditional update
    status: completed
  - id: commands
    content: ApproveVolunteerRequest, RejectVolunteerRequest, CloseEndedRequests with events
    status: completed
  - id: list-query
    content: ListMyRequests with status filter, my_role and names
    status: completed
  - id: routes
    content: GET /api/requests, POST /api/requests/{id}/approve and /reject
    status: completed
  - id: tests
    content: backend/tests/test_request_status.py
    status: completed
  - id: ui
    content: MyRequestsPage, requestService, My requests buttons
    status: completed
  - id: docs
    content: api.md, features.md, data-model.md, testing.md
    status: completed
isProject: false
---

# Request Approval and Automatic Close

## Context

A client can already create a `PENDING` request (`POST /api/requests`), but nothing moves it forward. The remaining features (dashboards, `check_volunteer_schedule`, `get_volunteer_history`) need `APPROVED` and `COMPLETED` requests. This slice implements **Request Approval** from [docs/features.md](docs/features.md):

- The assigned volunteer approves or rejects a request.
- Requests close automatically when their time passes. This replaces the earlier idea of a client "Mark completed" button.
- A "My requests" page.


## Data: no new table

- **Requests:** the existing table `volunteer_requests` ([backend/app/models/volunteer_request.py](backend/app/models/volunteer_request.py)) already has a `status` column. Today it is always `PENDING`.
- **Status constants:** add `APPROVED`, `REJECTED`, `COMPLETED`, and `STATUSES` next to `PENDING`.
- **Events:** every status change also writes a row to the existing `domain_events` table, in the same transaction.

## Lifecycle

```text
PENDING ──approve (volunteer)──► APPROVED ──end time passed (auto)──► COMPLETED
   ├────reject (volunteer)────► REJECTED
   └──start time passed (auto)► REJECTED
```

## Business rules

### Approve / Reject (manual): `POST /api/requests/{id}/approve` and `POST /api/requests/{id}/reject`

- The caller must have the VOLUNTEER role, otherwise `403`.
- The request must exist and belong to the caller (`volunteer_id`), otherwise `404`.
- The status must be `PENDING`, otherwise `409` (the existing `ConflictError` in [errors.py](backend/app/errors.py)).
- **Approve only:**
  - The start time must not have passed. Otherwise the auto-close step rejects the request first, so the result is `409`.
  - The request must not overlap another `APPROVED` request of the same volunteer on the same date. Otherwise `409`.
- No request body. The response is `200` with the updated request.

### Automatic close at read time

There is no background job and no new library. Each read of requests runs a close step before the data is returned.

- **`CloseEndedRequests.execute(user_id)`** runs over the caller's requests, as client or as volunteer:
  - `APPROVED` with `date + start_time + duration` in the past: changes to `COMPLETED` and writes the event `VolunteerRequestCompleted`.
  - `PENDING` with `date + start_time` in the past: changes to `REJECTED` and writes the event `VolunteerRequestRejected` with `"reason": "EXPIRED"`.
  - Event data: `request_id`, `client_id`, `volunteer_id`, `previous_status`, `status`, and `acted_by: "SYSTEM"`.
- **Where it runs:** at the start of `GET /api/requests`, and before approve or reject so a stale request cannot be approved. The future dashboards will call it too.
- **Clock:** server local time, the same clock as the stored naive date and time.
- **Frontend:** it does not calculate times. It shows the status the backend returns, which is already updated, so the frontend and the database match.

### Safe status change

Every status change, manual or automatic, goes through one repository method:

```sql
UPDATE volunteer_requests SET status = :to WHERE id = :id AND status = :from
```

If no row changes, someone else changed the request first. A manual action then returns `409`. The automatic step just skips that request. This way Approve and the automatic Reject cannot both succeed.

### List: `GET /api/requests?status=...`

- Runs `CloseEndedRequests` first, then returns the caller's requests from both sides.
- The optional `status` filter accepts one of the four statuses. Anything else returns `400`.
- Each item is the existing `public_request(...)` dictionary plus:
  - `my_role` (`CLIENT` or `VOLUNTEER`)
  - `client_name` and `volunteer_name`
- No email or phone. Sorted by `date`, then `start_time`.

## Screen: "My requests"

- **How to open it:** a new **My requests** button on the profile page, next to the existing Search button. It opens a separate screen (`view === "requests"`). Search and the request form use the same pattern.
- **Who sees which section:**
  - A volunteer sees **Requests sent to me**.
  - A client sees **Requests I sent**.
  - A user with both roles sees both sections, one under the other.

```text
My requests                              [Back to profile]
Status: [All ▾]

Requests sent to me            (volunteer)
┌──────────────────────────────────────────────────────┐
│ Dana Cohen · Shopping · 12/11/2026 10:00 · 2h          │
│ Herzl 5, Tel Aviv                                      │
│ "Help with grocery shopping"                           │
│ PENDING                          [Approve] [Reject]    │
└──────────────────────────────────────────────────────┘

Requests I sent                (client)
┌──────────────────────────────────────────────────────┐
│ To: Avi Levi · Tutoring · 15/11/2026 16:00 · 1h        │
│ APPROVED                                              │
└──────────────────────────────────────────────────────┘
```

- **Approve and Reject:** appear only on `PENDING` rows in the volunteer section.
- **Client section:** has no buttons. It only shows the status (`PENDING`, `APPROVED`, `REJECTED`, `COMPLETED`), which the backend has already updated.

## Files

### Create

- [backend/app/services/request_time.py](backend/app/services/request_time.py): `activity_start(r)`, `activity_end(r)`, and `overlaps(a, b)`.
- [backend/app/commands/change_request_status.py](backend/app/commands/change_request_status.py):
  - `ApproveVolunteerRequest` and `RejectVolunteerRequest`, built on a shared base that checks the role, ownership, and current status.
  - The base then runs the conditional update, adds the event, and commits; on failure it rolls back. This is the same pattern as [create_volunteer_request.py](backend/app/commands/create_volunteer_request.py). It reuses `public_request` from that file.
- [backend/app/commands/close_ended_requests.py](backend/app/commands/close_ended_requests.py): `CloseEndedRequests`.
- [backend/app/queries/list_my_requests.py](backend/app/queries/list_my_requests.py): `ListMyRequests`.
- [backend/tests/test_request_status.py](backend/tests/test_request_status.py): reuses the helpers and fixtures pattern from [test_create_volunteer_request.py](backend/tests/test_create_volunteer_request.py).
- [frontend/src/services/requestService.js](frontend/src/services/requestService.js): `listMyRequests`, `approveRequest`, and `rejectRequest`, all through `apiRequest`.
- [frontend/src/pages/MyRequestsPage.jsx](frontend/src/pages/MyRequestsPage.jsx):
  - A status filter.
  - **Requests sent to me**, with Approve and Reject buttons on `PENDING` rows.
  - **Requests I sent**, with a status badge only.
  - After an action, the list reloads. A `401` calls `onLoggedOut`.

### Modify

- [backend/app/persistence/request_repository.py](backend/app/persistence/request_repository.py): add `get_by_id`, `list_for_user(user_id, status=None)`, `list_approved_for_volunteer_on(volunteer_id, date)`, and `transition_status(id, from, to) -> bool`.
- [backend/app/routes/requests.py](backend/app/routes/requests.py): add thin `GET ""`, `POST /<int:request_id>/approve`, and `POST /<int:request_id>/reject`.
- [backend/app/commands/__init__.py](backend/app/commands/__init__.py) and [backend/app/queries/__init__.py](backend/app/queries/__init__.py): export the new classes.
- [frontend/src/App.jsx](frontend/src/App.jsx): add a `requests` view. Add a **My requests** button in [ProfilePage.jsx](frontend/src/pages/ProfilePage.jsx).
- Docs:
  - [docs/api.md](docs/api.md):
    - Document the list and the approve and reject endpoints.
    - Replace the `POST /complete` section with the automatic-close rule.
    - Note that `complete` is not a client endpoint.
  - [docs/features.md](docs/features.md): in the lifecycle section, add the automatic COMPLETED and the expired PENDING → REJECTED.
  - [docs/data-model.md](docs/data-model.md) and [docs/testing.md](docs/testing.md): update to match.

Not in scope: dashboards, email, cancelling a request, and AI matching.

## Verification

### Backend tests

Run `pytest` in `backend/`. Add these cases:

- Approve and reject:
  - Approve a pending future request: `200`, status `APPROVED`, one `VolunteerRequestApproved` event.
  - Reject a pending future request: `200`, status `REJECTED`, one event.
- Permissions:
  - A client-only user calls approve: `403`.
  - Another volunteer's request: `404`.
  - Unknown request id: `404`.
  - No token: `401`.
- Invalid transitions:
  - Approve an `APPROVED` or `REJECTED` request: `409`.
  - Each of these leaves the status unchanged and writes no event.
- Overlap: approving a request that overlaps another approved request returns `409`.
- Automatic close (requests are seeded directly with past dates):
  - `APPROVED` whose end time has passed: after `GET /api/requests` it is `COMPLETED` and has a SYSTEM event.
  - `PENDING` whose start time has passed: becomes `REJECTED`.
  - `APPROVED` still in progress (started but not ended): stays `APPROVED`.
  - Approving an expired `PENDING` request: `409`, and the status is `REJECTED`.
  - Running the close step twice writes no second event.
- List:
  - A user with both roles gets the correct `my_role` on each item.
  - The `status` filter works.
  - A bad `status` returns `400`.
  - No email or phone in the items.

### Browser

- As a client, create a request.
- As the volunteer, open My requests and approve it.
- As the client, see it as `APPROVED`.
- Change a past-dated request in the database. After a refresh it shows `COMPLETED`, and an old `PENDING` shows `REJECTED`.
