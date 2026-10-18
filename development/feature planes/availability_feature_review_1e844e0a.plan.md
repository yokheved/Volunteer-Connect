---
name: Availability feature review
overview: Review of the uncommitted volunteer availability work. The API, overlap rules, and tests match the approved plan. Saving the profile can enable an empty save before the stored lists have loaded, and two quickly added windows can share one key.
todos:
  - id: fix-availability-load-save
    content: Keep availability and category Save disabled until the stored list has loaded after canLoad becomes true
    status: pending
  - id: fix-window-key
    content: Give each added availability window a key that stays unique when two windows are added back to back
    status: pending
isProject: false
---

# Volunteer Availability — Review

No project files were modified. Nothing will be changed until you approve a fix.

## Summary

- **Feature reviewed:** Recurring volunteer availability (`GET` and `PUT /api/volunteers/me/availability`).
- **Approved plan:** [volunteer_availability_91dce2a6.plan.md](c:\Users\yokhe\.cursor\plans\volunteer_availability_91dce2a6.plan.md)
- **Files reviewed:** [backend/app/models/availability.py](backend/app/models/availability.py), [backend/app/persistence/availability_repository.py](backend/app/persistence/availability_repository.py), [backend/app/commands/update_volunteer_availability.py](backend/app/commands/update_volunteer_availability.py), [backend/app/queries/get_volunteer_availability.py](backend/app/queries/get_volunteer_availability.py), [backend/app/routes/volunteers.py](backend/app/routes/volunteers.py), [backend/tests/test_volunteer_availability.py](backend/tests/test_volunteer_availability.py), [frontend/src/components/VolunteerAvailability.jsx](frontend/src/components/VolunteerAvailability.jsx), [frontend/src/services/volunteerService.js](frontend/src/services/volunteerService.js), [frontend/src/pages/ProfilePage.jsx](frontend/src/pages/ProfilePage.jsx), [frontend/src/components/VolunteerCategories.jsx](frontend/src/components/VolunteerCategories.jsx), [docs/api.md](docs/api.md), and the model/command/query exports in [backend/app/__init__.py](backend/app/__init__.py).
- **Overall assessment:** The command, query, table, event, overlap rules, and API tests match the plan. The profile page can save an empty local list after the volunteer role is saved and before the stored list returns. Two windows added back to back can also share one key.
- **Issues:** 0 critical, 0 high, 2 medium, 1 low
- **Limitations:** The test suite and the browser were not run. Untracked copies under `development/feature planes/` are not part of this feature.

## Findings

### Issue 1: Save is enabled before the stored list is loaded

- **Severity:** Medium
- **Location:** [frontend/src/components/VolunteerAvailability.jsx](frontend/src/components/VolunteerAvailability.jsx) initial state, load effect, and `handleSave`; the same pattern in [frontend/src/components/VolunteerCategories.jsx](frontend/src/components/VolunteerCategories.jsx)
- **Problem:** While `canLoad` is false, both components start with `loaded` true and `loading` false so a draft can be edited, and Save stays disabled. After the profile save, `canLoad` becomes true. The effect starts the GET but does not set `loading` back to true. `loaded` is already true, so `handleSave` no longer returns early, and the Save button is enabled (`disabled` only checks `saving` and `canLoad`).

```45:67:frontend/src/components/VolunteerAvailability.jsx
  const [loading, setLoading] = useState(canLoad);
  const [loaded, setLoaded] = useState(!canLoad);
  ...
    getMyAvailability()
      .then((data) => {
        if (cancelled) return;
        setWindows((current) =>
          current.length > 0 ? current : withKeys(data.availability),
        );
```

The categories effect used to call `setLoading(true)` at the start of that fetch. This change removes that line. A non-empty local list is also kept, so the response from the server is ignored.

- **Impact:** `PUT` replaces the whole set. A volunteer who saves the profile and then clicks Save availability or Save categories before the GET returns sends whatever is on screen. If that local list is still empty, stored windows or categories are cleared and a new event is written. This shows up when the volunteer role was turned off and back on, because those rows are not deleted with the role. A first-time volunteer has no stored rows, so the same click only writes the draft.
- **Recommended fix:** When `canLoad` becomes true, set `loading` to true before the request and keep Save off until that request succeeds. After a successful load, show the stored rows. Keep a draft only once the stored list has been received.

### Issue 2: Added windows can share one key

- **Severity:** Medium
- **Location:** [frontend/src/components/VolunteerAvailability.jsx](frontend/src/components/VolunteerAvailability.jsx) `newWindow`, used by `addWindow`
- **Problem:** A new row’s key is `Date.now()` plus `Math.random()`. `Date.now()` only changes once per millisecond. Two clicks on Add window in that same millisecond can draw the same random value as well, so both rows get the same key.

```19:26:frontend/src/components/VolunteerAvailability.jsx
function newWindow() {
  return {
    key: `${Date.now()}-${Math.random()}`,
    day_of_week: "SUNDAY",
    start_time: "09:00",
    end_time: "13:00",
  };
}
```

`updateWindow` and `removeWindow` find rows by that key. The list also uses the key as the React `key`.

- **Impact:** This is uncommon, and it happens when two windows are added immediately one after the other. React then treats the two rows as one row. Editing the day or time updates both, and Remove deletes both. Save sends that collapsed list, so the stored availability is not the set the volunteer meant to enter.
- **Recommended fix:** Keep a counter in the component, or use `crypto.randomUUID()` when it is available, and assign that value in `addWindow`. Do not derive the key only from the clock. Keys assigned in `withKeys` already include the row index, so loaded rows are not part of this collision.

### Issue 3: The availability row is wider than the profile card

- **Severity:** Low
- **Location:** [frontend/src/index.css](frontend/src/index.css) `.availability-row`; `main` is `max-width: 28rem`
- **Problem:** Each window is a four-column grid: day, start, end, and Remove. The card content width is about 360px after page and card padding, so the native time controls and the day select do not fit on one line.
- **Impact:** On a phone-width window the row overflows the card instead of wrapping.
- **Recommended fix:** Stack the day, times, and Remove button vertically when the card is narrow. Leave the wide layout for a wider window.

## What already matches the plan

- `GetVolunteerAvailability` only reads. `UpdateVolunteerAvailability` checks the user and the `VOLUNTEER` role, then validates, and only then replaces rows. `VolunteerAvailabilityUpdated` is written on aggregate `User` with `volunteer_id` and the new windows. `flush`, `commit`, and `rollback` follow the category command. The route does not validate or touch the database.
- Days are `SUNDAY` through `SATURDAY`. Times must be `HH:MM`. `end_time` must be later than `start_time` on the same day. Same-day overlaps, including an exact duplicate, return 400 and leave the previous rows and events unchanged. Touching windows (`09:00–13:00` and `13:00–16:00`) are saved. An empty array clears the rows and still records the event.
- Returned windows are ordered Sunday through Saturday, then by start time. The database `id` is not returned.
- `availability` has `id`, `volunteer_id`, `day_of_week`, `start_time`, and `end_time`, with `volunteer_id` referencing `users.id`. `db.create_all()` creates the new table.
- The profile page shows both volunteer sections when the Volunteer checkbox is on, and passes `canLoad` from the saved role. Availability is not sent with `PUT /api/users/me`. A failed availability load shows Try again and does not show Save.
- [docs/api.md](docs/api.md) documents the weekday order, `HH:MM`, end-after-start, overlap, touching windows, the empty array, the response shape, 401, and 403.
- [backend/tests/test_volunteer_availability.py](backend/tests/test_volunteer_availability.py) covers the plan’s API cases: Sunday-first read, replace, clear, bad day, bad time, end-before-start, duplicate, overlap, touching windows, 403, and 401.
- Debug calls to a local ingest URL were removed from the profile page and the category component.

## Missing tests

These are not the save-before-load case above.

- A user with both `CLIENT` and `VOLUNTEER` can GET and PUT availability.
- The same clock times on two different days are saved.
- `start_time` equal to `end_time` returns 400 and leaves the previous rows unchanged.

## Final recommendation

**Changes required.** The backend matches the approved plan. Both medium findings should be fixed before treating the profile availability section as safe: Save must stay off until the stored list has loaded, and each added window needs its own key.
