import { apiRequest } from "./api";

export const REQUEST_STATUSES = ["PENDING", "APPROVED", "REJECTED", "COMPLETED"];

export function listMyRequests(status) {
  const query = status ? `?status=${encodeURIComponent(status)}` : "";
  return apiRequest(`/api/requests${query}`);
}

export function approveRequest(requestId) {
  return apiRequest(`/api/requests/${requestId}/approve`, { method: "POST" });
}

export function rejectRequest(requestId) {
  return apiRequest(`/api/requests/${requestId}/reject`, { method: "POST" });
}
