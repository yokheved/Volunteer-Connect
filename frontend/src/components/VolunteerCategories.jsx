import { useEffect, useState } from "react";
import { setStoredToken } from "../services/authService";
import {
  ALLOWED_CATEGORIES,
  getMyCategories,
  updateMyCategories,
} from "../services/volunteerService";

export default function VolunteerCategories({ onLoggedOut }) {
  const [selected, setSelected] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  useEffect(() => {
    let cancelled = false;
    getMyCategories()
      .then((data) => {
        if (cancelled) return;
        setSelected(data.categories || []);
        setLoading(false);
      })
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
    return () => {
      cancelled = true;
    };
  }, [onLoggedOut]);

  function toggle(category) {
    setSelected((current) =>
      current.includes(category)
        ? current.filter((item) => item !== category)
        : [...current, category],
    );
  }

  async function handleSave(event) {
    event.preventDefault();
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

  return (
    <section className="card">
      <h2>Volunteering categories</h2>
      <p className="lede">Select the activities you want to help with.</p>
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
        <button type="submit" disabled={saving}>
          {saving ? "Saving..." : "Save categories"}
        </button>
      </form>
    </section>
  );
}
