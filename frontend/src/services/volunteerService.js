import { apiRequest } from "./api";

export const ALLOWED_CATEGORIES = [
  "Elderly Assistance",
  "Transportation",
  "Shopping",
  "Tutoring",
  "Technical Help",
  "Childcare Support",
  "Cooking",
  "Cleaning",
];

export function getMyCategories() {
  return apiRequest("/api/volunteers/me/categories");
}

export function updateMyCategories(categories) {
  return apiRequest("/api/volunteers/me/categories", {
    method: "PUT",
    body: { categories },
  });
}

export const DAYS_OF_WEEK = [
  "SUNDAY",
  "MONDAY",
  "TUESDAY",
  "WEDNESDAY",
  "THURSDAY",
  "FRIDAY",
  "SATURDAY",
];

export function getMyAvailability() {
  return apiRequest("/api/volunteers/me/availability");
}

export function updateMyAvailability(availability) {
  return apiRequest("/api/volunteers/me/availability", {
    method: "PUT",
    body: { availability },
  });
}
