import { useEffect, useState } from "react";
import { getCurrentUser, logoutUser, setStoredToken } from "../services/authService";

export default function ProfilePage({ onLoggedOut }) {
  const [user, setUser] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    getCurrentUser()
      .then((profile) => {
        if (!cancelled) setUser(profile);
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
  }, [onLoggedOut]);

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
      <h1>Current user</h1>
      {user ? (
        <dl className="profile">
          <dt>Name</dt>
          <dd>{user.name}</dd>
          <dt>Email</dt>
          <dd>{user.email}</dd>
          <dt>Roles</dt>
          <dd>{user.roles.join(", ")}</dd>
          <dt>Phone</dt>
          <dd>{user.phone}</dd>
          <dt>Address</dt>
          <dd>{user.address}</dd>
        </dl>
      ) : null}
      {error ? <p className="error">{error}</p> : null}
      <button type="button" onClick={handleLogout}>
        Log out
      </button>
    </section>
  );
}
