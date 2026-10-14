import { useEffect, useState } from "react";
import { setStoredToken } from "../services/authService";
import {
  DAYS_OF_WEEK,
  getMyAvailability,
  updateMyAvailability,
} from "../services/volunteerService";

const DAY_LABELS = {
  SUNDAY: "Sunday",
  MONDAY: "Monday",
  TUESDAY: "Tuesday",
  WEDNESDAY: "Wednesday",
  THURSDAY: "Thursday",
  FRIDAY: "Friday",
  SATURDAY: "Saturday",
};

let addedWindowSeq = 0;

function newWindow() {
  addedWindowSeq += 1;
  const key =
    typeof crypto !== "undefined" && typeof crypto.randomUUID === "function"
      ? crypto.randomUUID()
      : `added-${addedWindowSeq}`;
  return {
    key,
    day_of_week: "SUNDAY",
    start_time: "09:00",
    end_time: "13:00",
  };
}

function withKeys(windows) {
  return (windows || []).map((window, index) => ({
    key: `${window.day_of_week}-${window.start_time}-${index}`,
    day_of_week: window.day_of_week,
    start_time: window.start_time,
    end_time: window.end_time,
  }));
}

function withoutKeys(windows) {
  return windows.map(({ day_of_week, start_time, end_time }) => ({
    day_of_week,
    start_time: start_time.slice(0, 5),
    end_time: end_time.slice(0, 5),
  }));
}

export default function VolunteerAvailability({ onLoggedOut, canLoad = true }) {
  const [windows, setWindows] = useState([]);
  const [loading, setLoading] = useState(canLoad);
  const [loaded, setLoaded] = useState(!canLoad);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  useEffect(() => {
    let cancelled = false;
    if (!canLoad) {
      return () => {
        cancelled = true;
      };
    }
    getMyAvailability()
      .then((data) => {
        if (cancelled) return;
        setWindows(withKeys(data.availability));
        setLoaded(true);
        setLoading(false);
      })
      .catch((err) => {
        if (cancelled) return;
        if (err.status === 401) {
          setStoredToken(null);
          onLoggedOut(err.message);
          return;
        }
        setLoaded(false);
        setError(err.message);
        setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [onLoggedOut, canLoad]);

  function loadAvailability() {
    setLoading(true);
    setError("");
    setNotice("");
    getMyAvailability()
      .then((data) => {
        setWindows(withKeys(data.availability));
        setLoaded(true);
        setLoading(false);
      })
      .catch((err) => {
        if (err.status === 401) {
          setStoredToken(null);
          onLoggedOut(err.message);
          return;
        }
        setLoaded(false);
        setError(err.message);
        setLoading(false);
      });
  }

  function updateWindow(key, field, value) {
    setWindows((current) =>
      current.map((window) =>
        window.key === key ? { ...window, [field]: value } : window,
      ),
    );
  }

  function addWindow() {
    setWindows((current) => [...current, newWindow()]);
  }

  function removeWindow(key) {
    setWindows((current) => current.filter((window) => window.key !== key));
  }

  async function handleSave(event) {
    event.preventDefault();
    if (!loaded || loading || !canLoad) {
      if (!canLoad) {
        setError("Save your profile with the Volunteer role before saving availability.");
      }
      return;
    }
    setError("");
    setNotice("");
    setSaving(true);
    try {
      const data = await updateMyAvailability(withoutKeys(windows));
      setWindows(withKeys(data.availability));
      setNotice("Availability saved.");
    } catch (err) {
      if (err.status === 401) {
        setStoredToken(null);
        onLoggedOut(err.message);
        return;
      }
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <section className="card">
        <h2>Availability</h2>
        <p>Loading availability...</p>
      </section>
    );
  }

  if (!loaded) {
    return (
      <section className="card">
        <h2>Availability</h2>
        {error ? <p className="error">{error}</p> : (
          <p className="error">Availability could not be loaded.</p>
        )}
        <button type="button" className="secondary" onClick={loadAvailability}>
          Try again
        </button>
      </section>
    );
  }

  return (
    <section className="card">
      <h2>Availability</h2>
      <p className="lede">Set the recurring times you can volunteer.</p>
      {!canLoad ? (
        <p className="lede">Save your profile to keep this availability.</p>
      ) : null}
      {notice ? <p className="notice">{notice}</p> : null}
      <form onSubmit={handleSave}>
        {windows.length === 0 ? (
          <p className="lede">No availability windows yet.</p>
        ) : (
          windows.map((window) => (
            <div className="availability-row" key={window.key}>
              <label>
                Day
                <select
                  value={window.day_of_week}
                  onChange={(event) =>
                    updateWindow(window.key, "day_of_week", event.target.value)
                  }
                >
                  {DAYS_OF_WEEK.map((day) => (
                    <option key={day} value={day}>
                      {DAY_LABELS[day]}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Start
                <input
                  type="time"
                  value={window.start_time}
                  onChange={(event) =>
                    updateWindow(window.key, "start_time", event.target.value)
                  }
                  required
                />
              </label>
              <label>
                End
                <input
                  type="time"
                  value={window.end_time}
                  onChange={(event) =>
                    updateWindow(window.key, "end_time", event.target.value)
                  }
                  required
                />
              </label>
              <button
                type="button"
                className="secondary"
                onClick={() => removeWindow(window.key)}
              >
                Remove
              </button>
            </div>
          ))
        )}
        {error ? <p className="error">{error}</p> : null}
        <div className="button-row">
          <button type="button" className="secondary" onClick={addWindow}>
            Add window
          </button>
          <button type="submit" disabled={saving || !canLoad || loading || !loaded}>
            {saving ? "Saving..." : "Save availability"}
          </button>
        </div>
      </form>
    </section>
  );
}
