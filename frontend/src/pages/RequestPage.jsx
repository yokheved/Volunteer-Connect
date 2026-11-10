import { useCallback, useEffect, useState } from "react";
import AddressAutocomplete from "../components/AddressAutocomplete";
import { getCurrentUser, setStoredToken } from "../services/authService";
import { createVolunteerRequest } from "../services/clientService";

const DAY_LABELS = {
  SUNDAY: "Sunday",
  MONDAY: "Monday",
  TUESDAY: "Tuesday",
  WEDNESDAY: "Wednesday",
  THURSDAY: "Thursday",
  FRIDAY: "Friday",
  SATURDAY: "Saturday",
};

const WEEKDAY_NAMES = [
  "SUNDAY",
  "MONDAY",
  "TUESDAY",
  "WEDNESDAY",
  "THURSDAY",
  "FRIDAY",
  "SATURDAY",
];

function windowKey(window) {
  return `${window.day_of_week}-${window.start_time}-${window.end_time}`;
}

function weekdayFromDate(value) {
  const [year, month, day] = value.split("-").map(Number);
  if (!year || !month || !day) {
    return null;
  }
  return WEEKDAY_NAMES[new Date(year, month - 1, day).getDay()];
}

// prefill is a rejected request; use its details where they fit this volunteer.
function initialForm(volunteer, windows, prefill) {
  const matchingWindow = prefill
    ? windows.find(
        (window) =>
          window.day_of_week === weekdayFromDate(prefill.date) &&
          window.start_time === prefill.start_time,
      )
    : null;
  const firstWindow = matchingWindow || windows[0];
  return {
    category:
      prefill && volunteer.categories.includes(prefill.category)
        ? prefill.category
        : volunteer.categories[0] || "",
    date: prefill?.date || "",
    windowKey: firstWindow ? windowKey(firstWindow) : "",
    duration: prefill ? String(prefill.duration) : "1",
    description: prefill?.description || "",
  };
}

export default function RequestPage({
  volunteer,
  prefill,
  onLoggedOut,
  onShowSearch,
  onShowRequests,
}) {
  const windows = volunteer.availability || [];
  const hasWindows = windows.length > 0;
  const [client, setClient] = useState(null);
  const [form, setForm] = useState(() => initialForm(volunteer, windows, prefill));
  const [locationText, setLocationText] = useState("");
  const [place, setPlace] = useState(null);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [created, setCreated] = useState(null);

  const handlePlaceSelected = useCallback((selected) => setPlace(selected), []);
  const handlePlaceCleared = useCallback(() => setPlace(null), []);

  useEffect(() => {
    let cancelled = false;
    getCurrentUser()
      .then((profile) => {
        if (cancelled) return;
        // Default task location: the rejected request's place when searching
        // again, otherwise the client's profile address. The client can change it.
        const start = prefill?.google_place_id
          ? {
              address: prefill.location,
              google_place_id: prefill.google_place_id,
              latitude: prefill.latitude,
              longitude: prefill.longitude,
            }
          : profile.google_place_id && profile.latitude != null && profile.longitude != null
            ? {
                address: profile.address,
                google_place_id: profile.google_place_id,
                latitude: profile.latitude,
                longitude: profile.longitude,
              }
            : null;
        setLocationText(start ? start.address : "");
        setPlace(start);
        setClient(profile);
      })
      .catch((err) => {
        if (cancelled) return;
        if (err.status === 401) {
          setStoredToken(null);
          onLoggedOut(err.message);
          return;
        }
        setError(err.message);
      });
    return () => {
      cancelled = true;
    };
    // prefill is fixed for the life of this page.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [onLoggedOut]);

  function updateField(event) {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    const duration = Number(form.duration);
    if (!Number.isInteger(duration) || duration < 1) {
      setError("Duration must be a whole number of hours, at least 1.");
      return;
    }
    const selected = windows.find((window) => windowKey(window) === form.windowKey);
    if (!selected) {
      setError("Choose one of the volunteer’s saved availability windows.");
      return;
    }
    if (weekdayFromDate(form.date) !== selected.day_of_week) {
      setError("The date must fall on the selected window’s weekday.");
      return;
    }
    if (!place) {
      setError("Choose the task location from the suggestions.");
      return;
    }
    setSubmitting(true);
    try {
      const request = await createVolunteerRequest({
        volunteer_id: volunteer.id,
        category: form.category,
        date: form.date,
        start_time: selected.start_time,
        duration,
        description: form.description,
        location: place.address,
        google_place_id: place.google_place_id,
        latitude: place.latitude,
        longitude: place.longitude,
      });
      setCreated(request);
    } catch (err) {
      if (err.status === 401) {
        setStoredToken(null);
        onLoggedOut(err.message);
        return;
      }
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  if (created) {
    return (
      <section className="card">
        <h1>Request sent</h1>
        <p className="lede">Request {created.id} is {created.status}.</p>
        <dl className="profile">
          <dt>Request id</dt>
          <dd>{created.id}</dd>
          <dt>Status</dt>
          <dd>{created.status}</dd>
          <dt>Volunteer</dt>
          <dd>{volunteer.name}</dd>
          <dt>Category</dt>
          <dd>{created.category}</dd>
          <dt>Date</dt>
          <dd>{created.date}</dd>
          <dt>Start time</dt>
          <dd>{created.start_time}</dd>
          <dt>Duration</dt>
          <dd>
            {created.duration} {created.duration === 1 ? "hour" : "hours"}
          </dd>
          <dt>Location</dt>
          <dd>{created.location}</dd>
          <dt>Description</dt>
          <dd>{created.description}</dd>
        </dl>
        <div className="button-row">
          <button type="button" onClick={onShowSearch}>
            Back to search
          </button>
          <button type="button" onClick={onShowRequests}>
            My requests
          </button>
        </div>
      </section>
    );
  }

  return (
    <section className="card">
      <h1>Request {volunteer.name}</h1>
      <p className="lede">
        {volunteer.categories.length
          ? volunteer.categories.join(", ")
          : "This volunteer has no saved categories."}
      </p>
      {hasWindows ? null : (
        <p className="lede">This volunteer has no saved availability.</p>
      )}
      {client || error ? null : <p className="lede">Loading your address...</p>}
      <form onSubmit={handleSubmit}>
        {client ? (
          <AddressAutocomplete
            id="request-location"
            label="Task location"
            value={locationText}
            onChange={setLocationText}
            onPlaceSelected={handlePlaceSelected}
            onPlaceCleared={handlePlaceCleared}
          />
        ) : null}
        <label>
          Category
          <select
            name="category"
            value={form.category}
            onChange={updateField}
            required
          >
            {volunteer.categories.length === 0 ? (
              <option value="">No categories available</option>
            ) : (
              volunteer.categories.map((category) => (
                <option key={category} value={category}>
                  {category}
                </option>
              ))
            )}
          </select>
        </label>
        <label>
          Availability
          <select
            name="windowKey"
            value={form.windowKey}
            onChange={updateField}
            required
            disabled={!hasWindows}
          >
            {hasWindows ? (
              windows.map((window) => (
                <option key={windowKey(window)} value={windowKey(window)}>
                  {DAY_LABELS[window.day_of_week] || window.day_of_week}{" "}
                  {window.start_time}–{window.end_time}
                </option>
              ))
            ) : (
              <option value="">No availability listed</option>
            )}
          </select>
        </label>
        <label>
          Date
          <input
            name="date"
            type="date"
            value={form.date}
            onChange={updateField}
            required
          />
        </label>
        <label>
          Duration (hours)
          <input
            name="duration"
            type="number"
            min="1"
            step="1"
            value={form.duration}
            onChange={updateField}
            required
          />
        </label>
        <label>
          Description
          <textarea
            name="description"
            value={form.description}
            onChange={updateField}
            rows={4}
            required
          />
        </label>
        {error ? <p className="error">{error}</p> : null}
        <div className="button-row">
          <button type="submit" disabled={submitting || !client || !hasWindows}>
            {submitting ? "Sending..." : "Send request"}
          </button>
          <button type="button" className="secondary" onClick={onShowSearch}>
            Back to search
          </button>
        </div>
      </form>
    </section>
  );
}
