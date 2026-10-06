import { useState } from "react";
import { registerUser } from "../services/authService";

export default function RegisterPage({ onRegistered, onShowLogin }) {
  const [form, setForm] = useState({
    name: "",
    email: "",
    password: "",
    phone: "",
    address: "",
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

    setSubmitting(true);
    try {
      await registerUser({
        name: form.name,
        email: form.email,
        password: form.password,
        phone: form.phone,
        address: form.address,
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
          Name
          <input name="name" value={form.name} onChange={updateField} required />
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
        <label>
          Password
          <input
            name="password"
            type="password"
            value={form.password}
            onChange={updateField}
            minLength={8}
            required
          />
        </label>
        <label>
          Phone
          <input name="phone" value={form.phone} onChange={updateField} required />
        </label>
        <label>
          Address
          <input
            name="address"
            value={form.address}
            onChange={updateField}
            required
          />
        </label>
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
