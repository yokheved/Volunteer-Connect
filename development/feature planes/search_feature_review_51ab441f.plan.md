---
name: Search feature review
overview: Review of the uncommitted volunteer search work. The query, filters, privacy rules, and API tests match the approved plan. A failed search can still show the previous result list.
todos:
  - id: fix-stale-search-results
    content: Clear the search result list when a search fails so previous volunteers are not shown under the new error
    status: pending
isProject: false
---

# Volunteer Search — Review

No project files were modified. Nothing will be changed until you approve a fix.

## Summary

- **Feature reviewed:** Structured volunteer search (`GET /api/volunteers`, query `SearchVolunteers`).
- **Approved plan:** [volunteer_search_91788c9f.plan.md](c:\Users\yokhe\.cursor\plans\volunteer_search_91788c9f.plan.md)
- **Files reviewed:** [backend/app/queries/search_volunteers.py](backend/app/queries/search_volunteers.py), [backend/app/persistence/user_repository.py](backend/app/persistence/user_repository.py), [backend/app/routes/volunteers.py](backend/app/routes/volunteers.py), [backend/app/queries/__init__.py](backend/app/queries/__init__.py), [backend/tests/test_search_volunteers.py](backend/tests/test_search_volunteers.py), [frontend/src/services/clientService.js](frontend/src/services/clientService.js), [frontend/src/pages/SearchPage.jsx](frontend/src/pages/SearchPage.jsx), [frontend/src/App.jsx](frontend/src/App.jsx), [frontend/src/pages/ProfilePage.jsx](frontend/src/pages/ProfilePage.jsx), [docs/api.md](docs/api.md), and the search styles in [frontend/src/index.css](frontend/src/index.css).
- **Overall assessment:** Search is a read-only query with AND filters, the public response, and the separate search page the plan describes. A failed search leaves the last result list on screen.
- **Issues:** 0 critical, 0 high, 1 medium, 0 low
- **Limitations:** The test suite and the browser were not run. Untracked copies under `development/feature planes/` are not part of this feature.

## Findings

### Issue 1: A failed search still shows the previous volunteers

- **Severity:** Medium
- **Location:** [frontend/src/pages/SearchPage.jsx](frontend/src/pages/SearchPage.jsx) `handleSearch`
- **Problem:** `volunteers` is set only after a successful response. On a 400 or any other error, the catch sets `error` and leaves the previous array in place.

```32:51:frontend/src/pages/SearchPage.jsx
  async function handleSearch(event) {
    event.preventDefault();
    setError("");
    setSearching(true);
    try {
      const data = await searchVolunteers({
        category: filters.category,
        date: filters.date,
        start_time: filters.start_time ? filters.start_time.slice(0, 5) : "",
        location: filters.location,
      });
      setVolunteers(data.volunteers || []);
    } catch (err) {
      if (err.status === 401) {
        setStoredToken(null);
        onLoggedOut(err.message);
        return;
      }
      setError(err.message);
```

The result block renders whenever `volunteers` is not null, including when `error` is set.

- **Impact:** A client can search successfully, change the filters to something the API rejects (for example a date with no start time), and still see the previous people under the error. Those people do not match the filters now on the form. A 401 still logs the user out and does not leave them on the page.
- **Recommended fix:** Clear `volunteers` when a search starts, or at least when it fails, so the list is shown only for the search that just succeeded.

## What already matches the plan

- `SearchVolunteers` is a query. It checks the caller, requires `CLIENT`, validates filters, and reads users, categories, and availability. It does not flush, commit, or write a domain event. There is no command.
- Filters that are present are combined with AND. All four may be omitted, and that returns every volunteer. A blank location is ignored. `category` must be one of the eight allowed strings. `date` and `start_time` must be sent together. The weekday comes from the calendar date, and Monday `10:00` matches `09:00–13:00` while it does not match `14:00–18:00`. The match is `window start <= start_time < window end`.
- Only users with `VOLUNTEER` are candidates, ordered by name, then id. A client who is also a volunteer remains eligible to appear. The response includes id, name, address, categories, about text, and availability. Email, phone, password, place id, latitude, and longitude are omitted. An empty list is 200.
- A missing token is 401. A volunteer-only user is 403. The route only reads the query string and the JWT id.
- Search is its own app view. The profile page is not mounted at the same time. The profile page shows “Search volunteers” only when the saved roles include `CLIENT`, and that button only switches the view. A volunteer-only profile has no search control. The search page owns the form and the results, and Back to profile switches the view back. Leaving the page drops the result list because the page unmounts.
- [docs/api.md](docs/api.md) documents the filter rules, the half-open time match, the address substring rule, the response shape, 400, 401, and 403.
- [backend/tests/test_search_volunteers.py](backend/tests/test_search_volunteers.py) covers the plan’s API cases: Monday `10:00` with Shopping, category alone, location `jerusalem`, all filters together, no match, bad category, bad date, bad time, only one of date or time, private fields, 403, 401, and no new domain event.

## Missing tests

These are not the failed-search display above.

- An empty search returns every volunteer and omits a client-only user.
- Monday `13:00` matches a window that starts at `13:00` and does not match a window that ends at `13:00`.
- A Sunday date matches a `SUNDAY` window.
- A user with both `CLIENT` and `VOLUNTEER` can search, and that user can appear in another client’s results.
- An impossible calendar date such as `2026-02-31` returns 400.

## Final recommendation

**Changes required.** The backend matches the approved plan. The medium finding should be fixed before treating the search page as safe to use: the result list must belong to the search that just succeeded.
