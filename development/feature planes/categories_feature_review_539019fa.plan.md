---
name: Categories feature review
overview: Review of the volunteer categories commit. The backend matches the approved plan. One profile-page path can replace a saved selection with an empty list after a failed load.
todos:
  - id: fix-category-load-save
    content: Do not allow Save until volunteer categories have loaded successfully
    status: pending
isProject: false
---

# Volunteer Categories — Review

No project files were modified. Nothing will be changed until you approve a fix.

## Summary

- **Feature reviewed:** Volunteer category selection in commit `fbd64f0` (`GET` and `PUT /api/volunteers/me/categories`).
- **Approved plan:** [volunteer_categories_848a7877.plan.md](C:\Users\yokhe\.cursor\plans\volunteer_categories_848a7877.plan.md)
- **Files reviewed:** the 17 files in that commit, including [backend/app/commands/update_volunteer_categories.py](backend/app/commands/update_volunteer_categories.py), [backend/app/queries/get_volunteer_categories.py](backend/app/queries/get_volunteer_categories.py), [backend/app/routes/volunteers.py](backend/app/routes/volunteers.py), [backend/app/models/volunteer_category.py](backend/app/models/volunteer_category.py), [backend/app/persistence/category_repository.py](backend/app/persistence/category_repository.py), [backend/tests/test_volunteer_categories.py](backend/tests/test_volunteer_categories.py), [frontend/src/components/VolunteerCategories.jsx](frontend/src/components/VolunteerCategories.jsx), [frontend/src/services/volunteerService.js](frontend/src/services/volunteerService.js), [frontend/src/pages/ProfilePage.jsx](frontend/src/pages/ProfilePage.jsx), [docs/api.md](docs/api.md), [docs/data-model.md](docs/data-model.md), and [docs/features.md](docs/features.md).
- **Overall assessment:** The commit matches the plan. The command, query, route, table, event, docs, and required API tests are in place. The category section can still save an empty selection when the initial load failed.
- **Issues:** 0 critical, 0 high, 1 medium, 0 low
- **Limitations:** The test suite and the browser were not run. The working tree was clean, so this review is only that commit. Unrelated uncommitted work was not part of it.

## Findings

### Issue 1: A failed category load can be saved as an empty selection

- **Severity:** Medium
- **Location:** [frontend/src/components/VolunteerCategories.jsx](frontend/src/components/VolunteerCategories.jsx) `useEffect` catch, and `handleSave`
- **Problem:** `selected` starts as `[]`. If `getMyCategories` fails with anything other than 401, the catch stores the error, sets `loading` to false, and leaves `selected` empty. The form, including Save, is then shown.

```24:34:frontend/src/components/VolunteerCategories.jsx
      .catch((err) => {
        if (cancelled) return;
        if (err.status === 401) {
          setStoredToken(null);
          onLoggedOut(err.message);
          return;
        }
        setError(err.message);
        setLoading(false);
      });
```

```52:54:frontend/src/components/VolunteerCategories.jsx
    try {
      const data = await updateMyCategories(selected);
      setSelected(data.categories);
```

- **Impact:** `PUT` replaces the whole selection. A volunteer whose categories did not load sees every box unchecked and an error under the list. Save sends `categories: []`, which clears the stored rows and writes `VolunteerCategoriesUpdated`. A 401 still logs the user out and does not save. A 403 on Save is rejected by the API, so a client-only token cannot clear rows this way.
- **Recommended fix:** After a failed load, show the error and do not render the save form. Add a retry that calls `getMyCategories` again. Enable Save only after a load succeeds.

## What already matches the plan

- `GetVolunteerCategories` only reads. `UpdateVolunteerCategories` replaces that volunteer’s rows and appends `VolunteerCategoriesUpdated` on aggregate `User`, with `volunteer_id` and the new list. Validation and a missing `VOLUNTEER` role happen before any delete, and a failure rolls back.
- The volunteer id comes from the JWT. A missing token is 401. A client-only user is 403. The current password is not required.
- Unknown names, blanks, and duplicates return 400 and leave the previous rows and events unchanged. An empty array clears the selection and still records an event.
- `volunteer_categories` uses `volunteer_id` and `category` as the composite primary key, with `volunteer_id` referencing `users.id`. `db.create_all()` creates the new table.
- The profile page shows the section only when the saved roles include `VOLUNTEER`, and category save is a separate request from `PUT /api/users/me`.
- The eight labels, including Cooking and Cleaning, match in the command, the checkbox list, [docs/api.md](docs/api.md), [docs/data-model.md](docs/data-model.md), and [docs/features.md](docs/features.md).
- [backend/tests/test_volunteer_categories.py](backend/tests/test_volunteer_categories.py) covers the plan’s API cases: empty read, save, replace, clear, unknown, duplicate, blank, 403, and 401.

## Missing tests

These are not the load-failure case above.

- A user with both `CLIENT` and `VOLUNTEER` can GET and PUT categories.
- Replacing a selection with an overlapping set, such as `["Shopping", "Transportation"]` followed by `["Shopping", "Cooking"]`, keeps only the new rows.

## Final recommendation

**Changes required.** The backend behavior matches the approved plan. The medium finding should be fixed before treating the profile category section as safe to use: a failed load must not be saveable as an empty selection.
