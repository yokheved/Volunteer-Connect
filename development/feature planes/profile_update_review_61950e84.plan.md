---
name: Profile update review
overview: Review of the uncommitted User Profile update. The command, route, password checks, and backend tests match the approved plan, but the Google address control can fail silently and the location timestamp is refreshed on every save.
todos:
  - id: fix-places-loader
    content: Load Places with importLibrary, surface load failures, and avoid clearing a valid selection
    status: pending
  - id: fix-cache-timestamp
    content: Update location_cached_at only when the place id changes, and test a name-only save
    status: pending
  - id: fix-update-event
    content: Include google_place_id on UserProfileUpdated and adjust the test
    status: pending
  - id: align-volunteer-rule
    content: Document that volunteer fields follow the roles in the request, and test the combined save
    status: pending
  - id: add-missing-tests
    content: Cover email rejection, partial password fields, coordinate range, clearing volunteer fields, and the column add
    status: pending
isProject: false
---

# User Profile Update — Review

No project files were modified. Fixes below are proposed only. Nothing will be changed until you approve them.

## Summary

- **Feature reviewed:** Update User Profile (`PUT /api/users/me`), including Google Places address selection on registration and profile update.
- **Approved plan:** [update_user_profile_c6ac3dd6.plan.md](C:\Users\yokhe\.cursor\plans\update_user_profile_c6ac3dd6.plan.md)
- **Files reviewed:** [backend/app/commands/update_user_profile.py](backend/app/commands/update_user_profile.py), [backend/app/commands/location.py](backend/app/commands/location.py), [backend/app/commands/register_user.py](backend/app/commands/register_user.py), [backend/app/persistence/schema.py](backend/app/persistence/schema.py), [backend/app/routes/users.py](backend/app/routes/users.py), [backend/app/queries/get_user_profile.py](backend/app/queries/get_user_profile.py), [backend/app/models/user.py](backend/app/models/user.py), [backend/app/errors.py](backend/app/errors.py), [backend/tests/test_update_profile.py](backend/tests/test_update_profile.py), [backend/tests/test_auth.py](backend/tests/test_auth.py), [backend/tests/test_register_user.py](backend/tests/test_register_user.py), [frontend/src/components/AddressAutocomplete.jsx](frontend/src/components/AddressAutocomplete.jsx), [frontend/src/services/googlePlaces.js](frontend/src/services/googlePlaces.js), [frontend/src/pages/ProfilePage.jsx](frontend/src/pages/ProfilePage.jsx), [frontend/src/pages/RegisterPage.jsx](frontend/src/pages/RegisterPage.jsx), [frontend/src/services/authService.js](frontend/src/services/authService.js), [docs/api.md](docs/api.md), [docs/data-model.md](docs/data-model.md)
- **Overall assessment:** CQRS, the current-password rule, password hashing, and the required API tests are in place. The address widget and the coordinate cache timestamp do not yet match the plan.
- **Issues:** 1 high, 3 medium, 1 low
- **Limitations:** Tests and the browser were not run. Google was not called. Untracked [`.cursor/skills/review-feature/`](.cursor/skills/review-feature/) and [`development/TODO.txt`](development/TODO.txt) are not part of this feature.

## Findings

### Issue 1: Places library can fail to attach, with no error

- **Severity:** High
- **Location:** [frontend/src/services/googlePlaces.js](frontend/src/services/googlePlaces.js) `loadGooglePlaces`; [frontend/src/components/AddressAutocomplete.jsx](frontend/src/components/AddressAutocomplete.jsx) lines 20–27
- **Problem:** The script URL uses `loading=async`, and the promise resolves on the script `load` event. With that loader, `google.maps.places` is not guaranteed to exist yet. The component then returns when `window.google.maps.places` is missing and does not set `mapsError`. If the script tag already exists, a new listener waits for a `load` event that will not fire again.
- **Impact:** Register and profile can show a plain address box. Free text cannot be saved, and the user never sees “Google Maps failed to load.” That blocks the required suggestion flow.
- **Recommended fix:** Load Places with `google.maps.importLibrary("places")` after the bootstrap script is ready. If the library is missing, reject the promise and show that error. Request only the place id, formatted address, and coordinates.

### Issue 2: Every profile save restarts the 30-day coordinate clock

- **Severity:** Medium
- **Location:** [backend/app/commands/update_user_profile.py](backend/app/commands/update_user_profile.py) `UpdateUserProfile.execute`, assignment of `location_cached_at`
- **Problem:** `latitude`, `longitude`, and `location_cached_at = utc_now()` are written on every successful update, including a name or phone change that resends the same place.

```98:102:backend/app/commands/update_user_profile.py
        user.address = payload["address"]
        user.google_place_id = payload["google_place_id"]
        user.latitude = payload["latitude"]
        user.longitude = payload["longitude"]
        user.location_cached_at = utc_now()
```

- **Impact:** [docs/data-model.md](docs/data-model.md) says coordinates may be cached for 30 days from when they were stored, and a later distance feature must treat older coordinates as expired. Refreshing the timestamp without a new Google result keeps stale coordinates looking fresh.
- **Recommended fix:** Set `location_cached_at` only when `google_place_id` changes. Registration still sets it once. Add a test that a name-only update keeps the previous timestamp.

### Issue 3: Profile-update events omit the place id

- **Severity:** Medium
- **Location:** [backend/app/commands/update_user_profile.py](backend/app/commands/update_user_profile.py) `written` dict; contrast [backend/app/commands/register_user.py](backend/app/commands/register_user.py) `UserRegistered` payload
- **Problem:** `UserRegistered` stores `google_place_id`, latitude, and longitude. `UserProfileUpdated` stores address, latitude, longitude, and `password_changed`, and the test asserts the place id is absent. The plan asks for location changes in the event history and also says the place id is the permanent location key. Password is correctly absent.
- **Impact:** An address change in `domain_events` cannot show which place was selected, so the update history does not match registration history.
- **Recommended fix:** Add `google_place_id` to `UserProfileUpdated`, still without the password or password hash. Update the assertion in [backend/tests/test_update_profile.py](backend/tests/test_update_profile.py).

### Issue 4: Volunteer-field rule does not match the API doc

- **Severity:** Medium
- **Location:** [backend/app/commands/update_user_profile.py](backend/app/commands/update_user_profile.py) lines 87–92; [docs/api.md](docs/api.md) update section
- **Problem:** The 403 check uses the roles in the request body. [docs/api.md](docs/api.md) says `about_me` and `monthly_hours_goal` are accepted only when the **saved** roles include `VOLUNTEER`. The profile form sends those fields in the same save that first checks Volunteer, which is why the code uses the submitted roles. A client who stays a client is correctly rejected; that case is tested.
- **Impact:** The documented contract and the running behavior disagree. A client can set About Me in the same request that adds `VOLUNTEER`.
- **Recommended fix:** Keep the one-save behavior, because the form and the plan’s UI depend on it. Change the API sentence so the roles **in this request** must include `VOLUNTEER`. Add a test for that combined save.

### Issue 5: A selection can be cleared by the widget’s own input event

- **Severity:** Low
- **Location:** [frontend/src/components/AddressAutocomplete.jsx](frontend/src/components/AddressAutocomplete.jsx) `handleChange` and `place_changed`
- **Problem:** Any input text that is not exactly `selectedAddressRef` clears the place id. That ref is set only inside `place_changed`, to `formatted_address`. The widget also writes into the same input and can emit an input event with a different string, before or after `place_changed`. Cleanup removes the listener and does not destroy the Autocomplete instance, so React StrictMode can attach a second widget in development.
- **Impact:** A successful suggestion can be wiped, and Save then reports that no suggestion was selected. In Vite dev, two dropdowns can appear.
- **Recommended fix:** Ignore input events that originate from the widget while applying a selection, and compare against both the prediction text and `formatted_address`. On cleanup, unbind the Autocomplete instance.

## What already matches the plan

- `UpdateUserProfile` is the write path. `GetUserProfile` is the read path. `PUT /api/users/me` stays thin and takes the user id from the JWT.
- `current_password` is required. A wrong password returns 401 and writes no event. Email in the body returns 400. Passwords are hashed and are not returned or stored in events.
- New password and confirmation must both be sent, must match, and must be at least 8 characters after trimming.
- Registration and update require address, place id, latitude, and longitude. Out-of-range coordinates fail validation.
- `ForbiddenError` is 403. Location columns are on `User`, and startup adds them if `users` already exists.
- `UserProfileUpdated` is committed with the user change and rolled back on failure.
- Backend tests cover the plan’s main API cases without calling Google. The profile page asks for the current password, keeps email read-only, and shows About Me and the monthly goal only when Volunteer is checked.

## Missing tests

These are not repeats of the findings above.

- `email` on `PUT /api/users/me` returns 400 and does not change the row.
- Only `new_password` or only `confirm_password` returns 400.
- Latitude or longitude outside range returns 400.
- A volunteer can clear `about_me` with an empty string and `monthly_hours_goal` with JSON `null`.
- An existing `users` table that lacks the location columns gains them through `ensure_user_location_columns`.

## Final recommendation

**Changes required.** The high-severity Maps loader issue can block registration and profile update in the browser. The coordinate timestamp should be fixed before this is committed, because it undermines the 30-day rule already written into the data model.
