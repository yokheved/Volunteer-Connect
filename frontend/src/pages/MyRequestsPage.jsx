import { useCallback, useEffect, useState } from "react";
import { getCurrentUser, setStoredToken } from "../services/authService";
import {
  REQUEST_STATUSES,
  approveRequest,
  listMyRequests,
  rejectRequest,
} from "../services/requestService";

function formatDate(isoDate) {
  const [year, month, day] = isoDate.split("-");
  return `${day}/${month}/${year}`;
}

function statusLabel(status) {
  return status.charAt(0) + status.slice(1).toLowerCase();
}

// Same rule as the server: a request's time has passed once it has started.
function hasStarted(request) {
  const [year, month, day] = request.date.split("-").map(Number);
  const [hours, minutes] = request.start_time.split(":").map(Number);
  return new Date(year, month - 1, day, hours, minutes) <= new Date();
}

function RequestCard({ request, otherName, children }) {
  return (
    <article className="search-result">
      <h2>{otherName}</h2>
      <p>
        {request.category} · {formatDate(request.date)} {request.start_time} ·{" "}
        {request.duration}h
      </p>
      <p>{request.location}</p>
      <p>{request.description}</p>
      <div className="request-footer">
        <span className={`status status-${request.status.toLowerCase()}`}>
          {statusLabel(request.status)}
        </span>
        {children}
      </div>
    </article>
  );
}

export default function MyRequestsPage({ onLoggedOut, onShowProfile, onSearchAgain }) {
  const [roles, setRoles] = useState(null);
  const [requests, setRequests] = useState(null);
  const [statusFilter, setStatusFilter] = useState("");
  const [error, setError] = useState("");
  const [busyId, setBusyId] = useState(null);

  const handleError = useCallback(
    (err) => {
      if (err.status === 401) {
        setStoredToken(null);
        onLoggedOut(err.message);
        return;
      }
      setError(err.message);
    },
    [onLoggedOut],
  );

  const load = useCallback(async () => {
    try {
      // The server closes requests whose time has passed before it answers.
      setRequests(await listMyRequests(statusFilter));
    } catch (err) {
      handleError(err);
    }
  }, [statusFilter, handleError]);

  useEffect(() => {
    getCurrentUser()
      .then((user) => setRoles(user.roles))
      .catch(handleError);
  }, [handleError]);

  useEffect(() => {
    load();
  }, [load]);

  async function decide(action, requestId) {
    setError("");
    setBusyId(requestId);
    try {
      await action(requestId);
    } catch (err) {
      handleError(err);
      if (err.status === 401) return;
    } finally {
      setBusyId(null);
    }
    // Reload even after a 409, so the row shows the status the server has now.
    await load();
  }

  if (!roles || !requests) {
    return (
      <section className="card">
        <h1>My requests</h1>
        {error ? <p className="error">{error}</p> : <p className="lede">Loading...</p>}
      </section>
    );
  }

  const received = requests.filter((request) => request.my_role === "VOLUNTEER");
  const sent = requests.filter((request) => request.my_role === "CLIENT");

  return (
    <section className="card">
      <h1>My requests</h1>
      <form onSubmit={(event) => event.preventDefault()}>
        <label>
          Status
          <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
            <option value="">All</option>
            {REQUEST_STATUSES.map((status) => (
              <option key={status} value={status}>
                {statusLabel(status)}
              </option>
            ))}
          </select>
        </label>
      </form>
      {error ? <p className="error">{error}</p> : null}

      {roles.includes("VOLUNTEER") ? (
        <div className="search-results">
          <h2>Requests sent to me</h2>
          {received.length === 0 ? (
            <p className="lede">No requests.</p>
          ) : (
            received.map((request) => (
              <RequestCard key={request.id} request={request} otherName={request.client_name}>
                {request.status === "PENDING" ? (
                  <div className="button-row">
                    <button
                      type="button"
                      disabled={busyId === request.id}
                      onClick={() => decide(approveRequest, request.id)}
                    >
                      Approve
                    </button>
                    <button
                      type="button"
                      className="danger"
                      disabled={busyId === request.id}
                      onClick={() => decide(rejectRequest, request.id)}
                    >
                      Reject
                    </button>
                  </div>
                ) : null}
              </RequestCard>
            ))
          )}
        </div>
      ) : null}

      {roles.includes("CLIENT") ? (
        <div className="search-results">
          <h2>Requests I sent</h2>
          {sent.length === 0 ? (
            <p className="lede">No requests.</p>
          ) : (
            sent.map((request) => (
              <RequestCard
                key={request.id}
                request={request}
                otherName={`To: ${request.volunteer_name}`}
              >
                {request.status === "REJECTED" && !hasStarted(request) ? (
                  <div className="button-row">
                    <button type="button" onClick={() => onSearchAgain(request)}>
                      Search again
                    </button>
                  </div>
                ) : null}
              </RequestCard>
            ))
          )}
        </div>
      ) : null}

      <div className="button-row">
        <button type="button" className="secondary" onClick={onShowProfile}>
          Back to profile
        </button>
      </div>
    </section>
  );
}
