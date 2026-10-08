import { useCallback, useEffect, useState } from "react";
import AddressAutocomplete from "../components/AddressAutocomplete";
import {
  getCurrentUser,
  logoutUser,
  setStoredToken,
  updateCurrentUser,
} from "../services/authService";

function isTokenError(message) {
  return !/current password/i.test(message || "");
}

export default function ProfilePage({ onLoggedOut }) {
  const [user, setUser] = useState(null);
  const [form, setForm] = useState({
    name: "",
    phone: "",
    address: "",
    google_place_id: "",
    latitude: null,
    longitude: null,
    isClient: false,
    isVolunteer: false,
    current_password: "",
    new_password: "",
    confirm_password: "",
    about_me: "",
    monthly_hours_goal: "",
  });
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    let cancelled = false;
    getCurrentUser()
      .then((profile) => {
        if (cancelled) return;
        setUser(profile);
        setForm((current) => ({
          ...current,
          name: profile.name || "",
          phone: profile.phone || "",
          address: profile.address || "",
          google_place_id: profile.google_place_id || "",
          latitude: profile.latitude,
          longitude: profile.longitude,
          isClient: profile.roles.includes("CLIENT"),
          isVolunteer: profile.roles.includes("VOLUNTEER"),
          about_me: profile.about_me || "",
          monthly_hours_goal:
            profile.monthly_hours_goal == null
              ? ""
              : String(profile.monthly_hours_goal),
        }));
      })
      .catch((err) => {
        if (cancelled) return;
        if (err.status === 401 && isTokenError(err.message)) {
          setStoredToken(null);
          onLoggedOut(err.message);
          return;
        }
        setError(err.message);
      });
    return () => {
      cancelled = true;
    };
  }, [onLoggedOut]);

  function updateField(event) {
    const { name, value, type, checked } = event.target;
    setForm((current) => ({
      ...current,
      [name]: type === "checkbox" ? checked : value,
    }));
  }

  const handlePlaceSelected = useCallback((place) => {
    setForm((current) => ({ ...current, ...place }));
  }, []);

  const handlePlaceCleared = useCallback(() => {
    setForm((current) => ({
      ...current,
      google_place_id: "",
      latitude: null,
      longitude: null,
    }));
  }, []);

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setNotice("");

    const roles = [];
    if (form.isClient) roles.push("CLIENT");
    if (form.isVolunteer) roles.push("VOLUNTEER");
    if (roles.length === 0) {
      setError("Select at least one role.");
      return;
    }
    if (!form.google_place_id) {
      setError("Select an address from the Google suggestions.");
      return;
    }
    if (form.new_password || form.confirm_password) {
      if (form.new_password !== form.confirm_password) {
        setError("New password and confirmation must match.");
        return;
      }
    }

    const payload = {
      current_password: form.current_password,
      name: form.name,
      phone: form.phone,
      roles,
      address: form.address,
      google_place_id: form.google_place_id,
      latitude: form.latitude,
      longitude: form.longitude,
    };
    if (form.new_password || form.confirm_password) {
      payload.new_password = form.new_password;
      payload.confirm_password = form.confirm_password;
    }
    if (form.isVolunteer) {
      payload.about_me = form.about_me;
      payload.monthly_hours_goal =
        form.monthly_hours_goal === "" ? null : Number(form.monthly_hours_goal);
    }

    setSubmitting(true);
    try {
      const profile = await updateCurrentUser(payload);
      setUser(profile);
      setForm((current) => ({
        ...current,
        current_password: "",
        new_password: "",
        confirm_password: "",
        google_place_id: profile.google_place_id || "",
        latitude: profile.latitude,
        longitude: profile.longitude,
        address: profile.address || "",
      }));
      setNotice("Profile saved.");
    } catch (err) {
      if (err.status === 401 && isTokenError(err.message)) {
        setStoredToken(null);
        onLoggedOut(err.message);
        return;
      }
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  async function handleLogout() {
    try {
      await logoutUser();
      onLoggedOut();
    } catch (err) {
      onLoggedOut(err.message);
    }
  }

  if (!user && !error) {
    return (
      <section className="card">
        <p>Loading profile...</p>
      </section>
    );
  }

  return (
    <section className="card">
      <h1>Your profile</h1>
      <p className="lede">Enter your current password to save any changes.</p>
      {user ? (
        <form onSubmit={handleSubmit}>
          <label>
            Email
            <input value={user.email} readOnly />
          </label>
          <label>
            Name
            <input name="name" value={form.name} onChange={updateField} required />
          </label>
          <label>
            Phone
            <input name="phone" value={form.phone} onChange={updateField} required />
          </label>
          <AddressAutocomplete
            id="profile-address"
            value={form.address}
            onChange={(address) => setForm((current) => ({ ...current, address }))}
            onPlaceSelected={handlePlaceSelected}
            onPlaceCleared={handlePlaceCleared}
          />
          <fieldset>
            <legend>Roles</legend>
            <label className="checkbox">
              <input
                name="isClient"
                type="checkbox"
                checked={form.isClient}
                onChange={updateField}
              />
              Client
            </label>
            <label className="checkbox">
              <input
                name="isVolunteer"
                type="checkbox"
                checked={form.isVolunteer}
                onChange={updateField}
              />
              Volunteer
            </label>
          </fieldset>
          {form.isVolunteer ? (
            <>
              <label>
                About me
                <textarea
                  name="about_me"
                  value={form.about_me}
                  onChange={updateField}
                  rows={4}
                />
              </label>
              <label>
                Monthly hours goal
                <input
                  name="monthly_hours_goal"
                  type="number"
                  min="1"
                  value={form.monthly_hours_goal}
                  onChange={updateField}
                />
              </label>
            </>
          ) : null}
          <label>
            Current password
            <input
              name="current_password"
              type="password"
              value={form.current_password}
              onChange={updateField}
              required
            />
          </label>
          <label>
            New password
            <input
              name="new_password"
              type="password"
              value={form.new_password}
              onChange={updateField}
              minLength={8}
            />
          </label>
          <label>
            Confirm new password
            <input
              name="confirm_password"
              type="password"
              value={form.confirm_password}
              onChange={updateField}
              minLength={8}
            />
          </label>
          {notice ? <p className="notice">{notice}</p> : null}
          {error ? <p className="error">{error}</p> : null}
          <button type="submit" disabled={submitting}>
            {submitting ? "Saving..." : "Save profile"}
          </button>
        </form>
      ) : null}
      {error && !user ? <p className="error">{error}</p> : null}
      <button type="button" className="secondary" onClick={handleLogout}>
        Log out
      </button>
    </section>
  );
}
