import axios from "axios";

const baseURL = (
  (typeof import.meta !== "undefined" && import.meta.env?.VITE_API_BASE_URL) ||
  "http://localhost:8080/api"
).replace(/\/+$/, "");

/**
 * Shared HTTP client for FireFusion API (Screen 1 misinfo + other features).
 */
export const apiClient = axios.create({
  baseURL,
  timeout: 30_000,
  headers: {
    Accept: "application/json",
    "Content-Type": "application/json",
  },
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const message =
      error.response?.data?.message ||
      error.response?.data?.detail ||
      error.message ||
      "Request failed";
    const wrapped = new Error(message);
    wrapped.cause = error;
    wrapped.status = error.response?.status;
    return Promise.reject(wrapped);
  }
);
