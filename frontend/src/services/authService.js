import { apiRequest, TOKEN_KEY } from "./api";

export function getStoredToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function setStoredToken(token) {
  if (token) {
    localStorage.setItem(TOKEN_KEY, token);
    return;
  }
  localStorage.removeItem(TOKEN_KEY);
}

export function registerUser(payload) {
  return apiRequest("/api/auth/register", { method: "POST", body: payload });
}

export function loginUser(payload) {
  return apiRequest("/api/auth/login", { method: "POST", body: payload }).then(
    (data) => {
      setStoredToken(data.access_token);
      return data;
    },
  );
}

export async function logoutUser() {
  try {
    await apiRequest("/api/auth/logout", { method: "POST" });
  } finally {
    setStoredToken(null);
  }
}

export function getCurrentUser() {
  return apiRequest("/api/users/me");
}

export function updateCurrentUser(payload) {
  return apiRequest("/api/users/me", { method: "PUT", body: payload });
}
