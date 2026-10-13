import { useCallback, useEffect, useState } from "react";
import AddressAutocomplete from "../components/AddressAutocomplete";
import PasswordField from "../components/PasswordField";
import VolunteerCategories from "../components/VolunteerCategories";
import {
  getCurrentUser,
  loginUser,
  logoutUser,
  setStoredToken,
  updateCurrentUser,
} from "../services/authService";

function isTokenError(message) {
  return !/current password/i.test(message || "");
}

function profileToForm(profile) {
  return {
    name: profile.name || "",
    phone: profile.phone || "",
    address: profile.address || "",
    google_place_id: profile.google_place_id || "",
    latitude: profile.latitude,
    longitude: profile.longitude,
    isClient: profile.roles.includes("CLIENT"),
    isVolunteer: profile.roles.includes("VOLUNTEER"),
    current_password: "",
    new_password: "",
    confirm_password: "",
    about_me: profile.about_me || "",
    monthly_hours_goal:
      profile.monthly_hours_goal == null ? "" : String(profile.monthly_hours_goal),
  };
}

function roleLabels(roles) {
  const labels = [];
  if (roles.includes("CLIENT")) labels.push("Client");
  if (roles.includes("VOLUNTEER")) labels.push("Volunteer");
  return labels.join(", ");
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
  const [mode, setMode] = useState("view");
  const [changingPassword, setChangingPassword] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    let cancelled = false;
    getCurrentUser()
      .then((profile) => {
        if (cancelled) return;
        setUser(profile);
        setForm(profileToForm(profile));
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
    // #region agent log
    if (name === "isVolunteer") {
      fetch("http://127.0.0.1:7435/ingest/9b4fa94a-b436-42f4-8a45-dbb7a509d7d4", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Debug-Session-Id": "09a427",
        },
        body: JSON.stringify({
          sessionId: "09a427",
          runId: "pre-fix",
          hypothesisId: "H1",
          location: "ProfilePage.jsx:updateField",
          message: "Volunteer role checkbox changed",
          data: {
            checked,
            mode,
            savedRoles: user?.roles || [],
            formIsVolunteerBefore: form.isVolunteer,
          },
          timestamp: Date.now(),
        }),
      }).catch(() => {});
    }
    // #endregion
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

  function showDetails(profile) {
    // #region agent log
    fetch("http://127.0.0.1:7435/ingest/9b4fa94a-b436-42f4-8a45-dbb7a509d7d4", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Debug-Session-Id": "09a427",
      },
      body: JSON.stringify({
        sessionId: "09a427",
        runId: "pre-fix",
        hypothesisId: "H2",
        location: "ProfilePage.jsx:showDetails",
        message: "Profile saved into local user state",
        data: {
          returnedRoles: profile?.roles || [],
          stillShowsCategories: !!(profile?.roles || []).includes("VOLUNTEER"),
        },
        timestamp: Date.now(),
      }),
    }).catch(() => {});
    // #endregion
    setUser(profile);
    setForm(profileToForm(profile));
    setMode("view");
    setChangingPassword(false);
  }

  function startEdit() {
    setError("");
    setNotice("");
    setForm((current) => ({ ...current, current_password: "" }));
    setMode("unlock");
  }

  function cancelEdit() {
    if (user) setForm(profileToForm(user));
    setMode("view");
    setChangingPassword(false);
    setError("");
  }

  function stopPasswordChange() {
    setChangingPassword(false);
    setForm((current) => ({
      ...current,
      new_password: "",
      confirm_password: "",
    }));
  }

  async function unlockEdit(event) {
    event.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await loginUser({ email: user.email, password: form.current_password });
      setMode("edit");
    } catch (err) {
      setError(err.status === 401 ? "Current password is incorrect." : err.message);
    } finally {
      setSubmitting(false);
    }
  }

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
    if (changingPassword) {
      if (!form.new_password || !form.confirm_password) {
        setError("Enter and confirm the new password.");
        return;
      }
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
    if (changingPassword) {
      payload.new_password = form.new_password;
      payload.confirm_password = form.confirm_password;
    }
    if (form.isVolunteer) {
      payload.about_me = form.about_me;
      payload.monthly_hours_goal =
        form.monthly_hours_goal === "" ? null : Number(form.monthly_hours_goal);
    }
    // #region agent log
    fetch("http://127.0.0.1:7435/ingest/9b4fa94a-b436-42f4-8a45-dbb7a509d7d4", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Debug-Session-Id": "09a427",
      },
      body: JSON.stringify({
        sessionId: "09a427",
        runId: "pre-fix",
        hypothesisId: "H5",
        location: "ProfilePage.jsx:handleSubmit",
        message: "Profile save payload roles",
        data: {
          formIsVolunteer: form.isVolunteer,
          formIsClient: form.isClient,
          roles,
        },
        timestamp: Date.now(),
      }),
    }).catch(() => {});
    // #endregion

    setSubmitting(true);
    try {
      const profile = await updateCurrentUser(payload);
      showDetails(profile);
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

  const savedVolunteer = !!(user?.roles || []).includes("VOLUNTEER");
  const showCategories = form.isVolunteer;

  // #region agent log
  fetch("http://127.0.0.1:7435/ingest/9b4fa94a-b436-42f4-8a45-dbb7a509d7d4", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Debug-Session-Id": "09a427",
    },
    body: JSON.stringify({
      sessionId: "09a427",
      runId: "post-fix",
      hypothesisId: "H1",
      location: "ProfilePage.jsx:render",
      message: "Whether categories card is shown",
      data: {
        mode,
        formIsVolunteer: form.isVolunteer,
        savedRoles: user?.roles || [],
        savedVolunteer,
        showCategories,
      },
      timestamp: Date.now(),
    }),
  }).catch(() => {});
  // #endregion

  return (
    <>
    <section className="card">
      <h1>Your profile</h1>
      {mode === "view" ? (
        <p className="lede">These are your account details.</p>
      ) : null}
      {mode === "unlock" ? (
        <p className="lede">Enter your current password to edit your profile.</p>
      ) : null}
      {notice ? <p className="notice">{notice}</p> : null}
      {user && mode === "view" ? (
        <>
          <dl className="profile">
            <dt>Email</dt>
            <dd>{user.email}</dd>
            <dt>Name</dt>
            <dd>{user.name}</dd>
            <dt>Phone</dt>
            <dd>{user.phone}</dd>
            <dt>Address</dt>
            <dd>{user.address}</dd>
            <dt>Roles</dt>
            <dd>{roleLabels(user.roles)}</dd>
            {user.roles.includes("VOLUNTEER") ? (
              <>
                <dt>About me</dt>
                <dd>{user.about_me || "—"}</dd>
                <dt>Monthly hours goal</dt>
                <dd>{user.monthly_hours_goal ?? "—"}</dd>
              </>
            ) : null}
          </dl>
          <div className="button-row">
            <button type="button" onClick={startEdit}>
              Edit profile
            </button>
            <button type="button" className="secondary" onClick={handleLogout}>
              Log out
            </button>
          </div>
        </>
      ) : null}
      {user && mode === "unlock" ? (
        <form onSubmit={unlockEdit}>
          <PasswordField
            label="Current password"
            name="current_password"
            value={form.current_password}
            onChange={updateField}
            autoComplete="current-password"
            required
          />
          {error ? <p className="error">{error}</p> : null}
          <div className="button-row">
            <button type="submit" disabled={submitting}>
              {submitting ? "Checking..." : "Continue"}
            </button>
            <button type="button" className="secondary" onClick={cancelEdit}>
              Cancel
            </button>
          </div>
        </form>
      ) : null}
      {user && mode === "edit" ? (
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
          {changingPassword ? (
            <>
              <PasswordField
                label="New password"
                name="new_password"
                value={form.new_password}
                onChange={updateField}
                minLength={8}
                autoComplete="new-password"
                required
              />
              <PasswordField
                label="Confirm new password"
                name="confirm_password"
                value={form.confirm_password}
                onChange={updateField}
                minLength={8}
                autoComplete="new-password"
                required
              />
              <button type="button" className="link" onClick={stopPasswordChange}>
                Keep current password
              </button>
            </>
          ) : (
            <button type="button" className="secondary" onClick={() => setChangingPassword(true)}>
              Change password
            </button>
          )}
          {error ? <p className="error">{error}</p> : null}
          <div className="button-row">
            <button type="submit" disabled={submitting}>
              {submitting ? "Saving..." : "Save profile"}
            </button>
            <button type="button" className="secondary" onClick={cancelEdit}>
              Cancel
            </button>
          </div>
        </form>
      ) : null}
      {error && !user ? <p className="error">{error}</p> : null}
      {user && mode !== "view" ? (
        <button type="button" className="secondary" onClick={handleLogout}>
          Log out
        </button>
      ) : null}
    </section>
    {showCategories ? (
      <VolunteerCategories
        onLoggedOut={onLoggedOut}
        canLoad={savedVolunteer}
      />
    ) : null}
    </>
  );
}
