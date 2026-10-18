import { apiRequest } from "./api";

export function createVolunteerRequest(payload) {
  return apiRequest("/api/requests", { method: "POST", body: payload });
}

export function searchVolunteers(filters) {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    const trimmed = typeof value === "string" ? value.trim() : value;
    if (trimmed) {
      params.set(key, trimmed);
    }
  });
  const query = params.toString();
  return apiRequest(`/api/volunteers${query ? `?${query}` : ""}`);
}
