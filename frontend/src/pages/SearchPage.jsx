import { useCallback, useState } from "react";
import AddressAutocomplete from "../components/AddressAutocomplete";
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

const RADIUS_OPTIONS = [5, 10, 25, 50];

export default function SearchPage({
  prefill,
  onLoggedOut,
  onShowProfile,
  onRequestVolunteer,
}) {
  // prefill is a rejected request whose details start the search.
  const [filters, setFilters] = useState({
    category: prefill?.category || "",
    date: prefill?.date || "",
    start_time: prefill?.start_time || "",
    locationText: prefill?.location || "",
    radius_km: "10",
  });
  const [place, setPlace] = useState(() =>
    prefill
      ? {
          address: prefill.location,
          google_place_id: prefill.google_place_id,
          latitude: prefill.latitude,
          longitude: prefill.longitude,
        }
      : null,
  );
  const [volunteers, setVolunteers] = useState(null);
  const [error, setError] = useState("");
  const [searching, setSearching] = useState(false);

  function updateField(event) {
    const { name, value } = event.target;
    setFilters((current) => ({ ...current, [name]: value }));
  }

  const handleLocationText = useCallback((locationText) => {
    setFilters((current) => ({ ...current, locationText }));
  }, []);
  const handlePlaceSelected = useCallback((selected) => setPlace(selected), []);
  const handlePlaceCleared = useCallback(() => setPlace(null), []);

  async function handleSearch(event) {
    event.preventDefault();
    setError("");
    if (filters.locationText.trim() && !place) {
      setError("Choose a location from the suggestions, or clear the field.");
      return;
    }
    setVolunteers(null);
    setSearching(true);
    try {
      const data = await searchVolunteers({
        category: filters.category,
        date: filters.date,
        start_time: filters.start_time ? filters.start_time.slice(0, 5) : "",
        latitude: place ? String(place.latitude) : "",
        longitude: place ? String(place.longitude) : "",
        radius_km: place ? filters.radius_km : "",
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
      <p className="lede">
        {prefill
          ? "Filled in from your rejected request. Edit the filters and search again."
          : "Filter by category, time, and location."}
      </p>
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
        <AddressAutocomplete
          id="search-location"
          label="Location"
          value={filters.locationText}
          onChange={handleLocationText}
          onPlaceSelected={handlePlaceSelected}
          onPlaceCleared={handlePlaceCleared}
        />
        <label>
          Distance
          <select
            name="radius_km"
            value={filters.radius_km}
            onChange={updateField}
            disabled={!place}
          >
            {RADIUS_OPTIONS.map((km) => (
              <option key={km} value={String(km)}>
                Within {km} km
              </option>
            ))}
          </select>
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
                <div className="button-row">
                  <button
                    type="button"
                    onClick={() => onRequestVolunteer(volunteer)}
                  >
                    Request
                  </button>
                </div>
              </article>
            ))
          )}
        </div>
      ) : null}
    </section>
  );
}
