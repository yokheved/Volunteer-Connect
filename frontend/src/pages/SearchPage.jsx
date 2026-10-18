import { useState } from "react";
import { setStoredToken } from "../services/authService";
import { searchVolunteers } from "../services/clientService";
import { ALLOWED_CATEGORIES } from "../services/volunteerService";

const DAY_LABELS = {
  SUNDAY: "Sunday",
  MONDAY: "Monday",
  TUESDAY: "Tuesday",
  WEDNESDAY: "Wednesday",
  THURSDAY: "Thursday",
  FRIDAY: "Friday",
  SATURDAY: "Saturday",
};

export default function SearchPage({ onLoggedOut, onShowProfile }) {
  const [filters, setFilters] = useState({
    category: "",
    date: "",
    start_time: "",
    location: "",
  });
  const [volunteers, setVolunteers] = useState(null);
  const [error, setError] = useState("");
  const [searching, setSearching] = useState(false);

  function updateField(event) {
    const { name, value } = event.target;
    setFilters((current) => ({ ...current, [name]: value }));
  }

  async function handleSearch(event) {
    event.preventDefault();
    setError("");
    setVolunteers(null);
    setSearching(true);
    try {
      const data = await searchVolunteers({
        category: filters.category,
        date: filters.date,
        start_time: filters.start_time ? filters.start_time.slice(0, 5) : "",
        location: filters.location,
      });
      setVolunteers(data.volunteers || []);
    } catch (err) {
      if (err.status === 401) {
        setStoredToken(null);
        onLoggedOut(err.message);
        return;
      }
      setVolunteers(null);
      setError(err.message);
    } finally {
      setSearching(false);
    }
  }

  return (
    <section className="card">
      <h1>Search volunteers</h1>
      <p className="lede">Filter by category, time, and location.</p>
      <form onSubmit={handleSearch}>
        <label>
          Category
          <select name="category" value={filters.category} onChange={updateField}>
            <option value="">Any category</option>
            {ALLOWED_CATEGORIES.map((category) => (
              <option key={category} value={category}>
                {category}
              </option>
            ))}
          </select>
        </label>
        <label>
          Date
          <input
            name="date"
            type="date"
            value={filters.date}
            onChange={updateField}
          />
        </label>
        <label>
          Start time
          <input
            name="start_time"
            type="time"
            value={filters.start_time}
            onChange={updateField}
          />
        </label>
        <label>
          Location
          <input
            name="location"
            type="text"
            value={filters.location}
            onChange={updateField}
            placeholder="Address text"
          />
        </label>
        {error ? <p className="error">{error}</p> : null}
        <div className="button-row">
          <button type="submit" disabled={searching}>
            {searching ? "Searching..." : "Search"}
          </button>
          <button type="button" className="secondary" onClick={onShowProfile}>
            Back to profile
          </button>
        </div>
      </form>
      {volunteers ? (
        <div className="search-results">
          {volunteers.length === 0 ? (
            <p className="lede">No volunteers match these filters.</p>
          ) : (
            volunteers.map((volunteer) => (
              <article className="search-result" key={volunteer.id}>
                <h2>{volunteer.name}</h2>
                <p>{volunteer.address}</p>
                {volunteer.about_me ? <p>{volunteer.about_me}</p> : null}
                <p>
                  {volunteer.categories.length
                    ? volunteer.categories.join(", ")
                    : "No categories"}
                </p>
                <ul className="availability-list">
                  {volunteer.availability.length === 0 ? (
                    <li>No availability listed</li>
                  ) : (
                    volunteer.availability.map((window) => (
                      <li
                        key={`${window.day_of_week}-${window.start_time}-${window.end_time}`}
                      >
                        {DAY_LABELS[window.day_of_week] || window.day_of_week}{" "}
                        {window.start_time}–{window.end_time}
                      </li>
                    ))
                  )}
                </ul>
              </article>
            ))
          )}
        </div>
      ) : null}
    </section>
  );
}
