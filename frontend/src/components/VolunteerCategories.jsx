import { useEffect, useState } from "react";
import { setStoredToken } from "../services/authService";
import {
  ALLOWED_CATEGORIES,
  getMyCategories,
  updateMyCategories,
} from "../services/volunteerService";

export default function VolunteerCategories({ onLoggedOut, canLoad = true }) {
  const [selected, setSelected] = useState([]);
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
    getMyCategories()
      .then((data) => {
        if (cancelled) return;
        setSelected(data.categories || []);
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

  function loadCategories() {
    setLoading(true);
    setError("");
    setNotice("");
    getMyCategories()
      .then((data) => {
        setSelected(data.categories || []);
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

  function toggle(category) {
    setSelected((current) =>
      current.includes(category)
        ? current.filter((item) => item !== category)
        : [...current, category],
    );
  }

  async function handleSave(event) {
    event.preventDefault();
    if (!loaded || loading || !canLoad) {
      if (!canLoad) {
        setError("Save your profile with the Volunteer role before saving categories.");
      }
      return;
    }
    setError("");
    setNotice("");
    setSaving(true);
    try {
      const data = await updateMyCategories(selected);
      setSelected(data.categories);
      setNotice("Categories saved.");
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
        <h2>Volunteering categories</h2>
        <p>Loading categories...</p>
      </section>
    );
  }

  if (!loaded) {
    return (
      <section className="card">
        <h2>Volunteering categories</h2>
        {error ? <p className="error">{error}</p> : (
          <p className="error">Categories could not be loaded.</p>
        )}
        <button type="button" className="secondary" onClick={loadCategories}>
          Try again
        </button>
      </section>
    );
  }

  return (
    <section className="card">
      <h2>Volunteering categories</h2>
      <p className="lede">Select the activities you want to help with.</p>
      {!canLoad ? (
        <p className="lede">Save your profile to keep these categories.</p>
      ) : null}
      {notice ? <p className="notice">{notice}</p> : null}
      <form onSubmit={handleSave}>
        <fieldset>
          <legend>Categories</legend>
          {ALLOWED_CATEGORIES.map((category) => (
            <label className="checkbox" key={category}>
              <input
                type="checkbox"
                checked={selected.includes(category)}
                onChange={() => toggle(category)}
              />
              {category}
            </label>
          ))}
        </fieldset>
        {error ? <p className="error">{error}</p> : null}
        <button type="submit" disabled={saving || !canLoad || loading || !loaded}>
          {saving ? "Saving..." : "Save categories"}
        </button>
      </form>
    </section>
  );
}
