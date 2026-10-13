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
