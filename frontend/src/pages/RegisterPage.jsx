import { useCallback, useState } from "react";
import AddressAutocomplete from "../components/AddressAutocomplete";
import PasswordField from "../components/PasswordField";
import { registerUser } from "../services/authService";
import { joinDisplayName } from "../utils/personName";

export default function RegisterPage({ onRegistered, onShowLogin }) {
  const [form, setForm] = useState({
    firstName: "",
    lastName: "",
    email: "",
    password: "",
    confirm_password: "",
    phone: "",
    address: "",
    google_place_id: "",
    latitude: null,
    longitude: null,
    isClient: true,
    isVolunteer: false,
  });
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

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

    const roles = [];
    if (form.isClient) roles.push("CLIENT");
    if (form.isVolunteer) roles.push("VOLUNTEER");
    if (roles.length === 0) {
      setError("Select at least one role.");
      return;
    }
    if (form.password !== form.confirm_password) {
      setError("Password and confirmation must match.");
      return;
    }
    if (!form.firstName.trim() || !form.lastName.trim()) {
      setError("Enter a first name and a last name.");
      return;
    }
    if (!form.google_place_id) {
      setError("Select an address from the Google suggestions.");
      return;
    }

    setSubmitting(true);
    try {
      await registerUser({
        name: joinDisplayName(form.firstName, form.lastName),
        email: form.email,
        password: form.password,
        confirm_password: form.confirm_password,
        phone: form.phone,
        address: form.address,
        google_place_id: form.google_place_id,
        latitude: form.latitude,
        longitude: form.longitude,
        roles,
      });
      onRegistered();
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="card">
      <h1>Create an account</h1>
      <p className="lede">Register as a client, a volunteer, or both.</p>
      <form onSubmit={handleSubmit}>
        <label>
          First name
          <input
            name="firstName"
            value={form.firstName}
            onChange={updateField}
            autoComplete="given-name"
            required
          />
        </label>
        <label>
          Last name
          <input
            name="lastName"
            value={form.lastName}
            onChange={updateField}
            autoComplete="family-name"
            required
          />
        </label>
        <label>
          Email
          <input
            name="email"
            type="email"
            value={form.email}
            onChange={updateField}
            required
          />
        </label>
        <PasswordField
          label="Password"
          name="password"
          value={form.password}
          onChange={updateField}
          minLength={8}
          autoComplete="new-password"
          required
        />
        <PasswordField
          label="Confirm password"
          name="confirm_password"
          value={form.confirm_password}
          onChange={updateField}
          minLength={8}
          autoComplete="new-password"
          required
        />
        <label>
          Phone
          <input name="phone" value={form.phone} onChange={updateField} required />
        </label>
        <AddressAutocomplete
          id="register-address"
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
        {error ? <p className="error">{error}</p> : null}
        <button type="submit" disabled={submitting}>
          {submitting ? "Registering..." : "Register"}
        </button>
      </form>
      <p className="switch">
        Already have an account?{" "}
        <button type="button" className="link" onClick={onShowLogin}>
          Log in
        </button>
      </p>
    </section>
  );
}
