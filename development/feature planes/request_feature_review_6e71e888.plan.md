---
name: Request feature review
overview: Approved fixes for the create-volunteer-request review. Keep the server availability check. Show that volunteer’s saved windows on RequestPage so the client picks one. Show a profile-load error instead of a stuck loading message.
todos:
  - id: keep-availability-and-picker
    content: Keep the server availability check; replace the free start-time input with a select of that volunteer’s saved windows; update API and features docs
    status: pending
  - id: show-profile-load-error
    content: Show a non-401 profile load error on RequestPage instead of leaving the address stuck on loading
    status: pending
isProject: false
---

# Create Volunteer Request — Approved Fixes

The review findings stay. The fixes below replace the earlier recommendations.

## Issue 1: Show saved windows and keep the server check

- **Severity:** High
- **Decision:** Keep the availability check in [backend/app/commands/create_volunteer_request.py](backend/app/commands/create_volunteer_request.py). Do not remove `matches_availability`. Keep the existing out-of-window and empty-availability `400` tests.
- **UI problem:** [frontend/src/pages/RequestPage.jsx](frontend/src/pages/RequestPage.jsx) still uses a free date field and a free `type="time"` start-time field. The client cannot see which windows the volunteer saved, so a valid-looking time can fail after submit.

### Request form

In [frontend/src/pages/RequestPage.jsx](frontend/src/pages/RequestPage.jsx), use `volunteer.availability` from the search result. Do not add a new query.

- List every saved window in a required select, using the same labels as search (`Thursday 09:00–13:00`).
- Keep the calendar date field, duration, description, and category.
- Remove the free start-time input.
- On submit, send `start_time` as the chosen window’s `start_time`.
- If the chosen date’s weekday does not match the chosen window’s `day_of_week`, set an error and do not call the API. Map the date with local `YYYY-MM-DD` parts and Sunday-first weekday names (`SUNDAY` through `SATURDAY`), matching the stored day names.
- If `volunteer.availability` is empty, show that the volunteer has no saved availability and disable Send.

Reuse the day labels already used on [frontend/src/pages/SearchPage.jsx](frontend/src/pages/SearchPage.jsx). A small copy on the request page is enough.

The command still rejects a time that is not inside a window on that weekday (`window start <= start_time < window end`). Choosing the window start always satisfies the start bound. The date weekday check on the form stops a Thursday window from being sent with a Friday date.

### Documentation

Update [docs/api.md](docs/api.md) Create Request:

- Keep the existing server availability paragraph.
- Add that the request screen lists that volunteer’s saved windows and the client chooses one. The body `start_time` is that window’s start. The body `date` must fall on that window’s weekday.

Update [docs/features.md](docs/features.md) Create Volunteering Request so start time is chosen from the volunteer’s saved availability windows.

Leave the backend command, tests, and [backend/app/services/availability_match.py](backend/app/services/availability_match.py) as they are, except for any import cleanup that the form change does not require.

## Issue 2: Show a profile-load error

- **Severity:** Medium
- **Location:** [frontend/src/pages/RequestPage.jsx](frontend/src/pages/RequestPage.jsx), the `getCurrentUser` effect.
- **Fix:** In the `catch`, keep the `401` logout path. For every other error, set `error` to `err.message` and stop showing “Loading your address...”. Leave Send disabled until `client` is set.

```24:30:frontend/src/pages/RequestPage.jsx
      .catch((err) => {
        if (cancelled) return;
        if (err.status === 401) {
          setStoredToken(null);
          onLoggedOut(err.message);
        }
      });
```

## Files to change

- [frontend/src/pages/RequestPage.jsx](frontend/src/pages/RequestPage.jsx)
- [docs/api.md](docs/api.md)
- [docs/features.md](docs/features.md)

## Verification

- Search as a client, open Request, confirm every saved window is in the select, pick one plus a matching weekday date, submit, see `PENDING`.
- Pick a date whose weekday does not match the selected window and confirm the form error with no request created.
- Open Request for a volunteer with no windows and confirm Send is disabled.
- Trigger a non-401 `getCurrentUser` failure and confirm the error text, not a stuck loading line.
- Confirm a volunteer-only account still cannot open this flow from search.

No project files have been changed yet. These two fixes wait for explicit approval to implement.
