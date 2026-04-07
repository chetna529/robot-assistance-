const API_BASE =
  import.meta.env.VITE_API_BASE_URL?.trim() || "http://127.0.0.1:8000";

async function request(method, path, body) {
  const url = `${API_BASE}${path}`;
  const response = await fetch(url, {
    method,
    headers: {
      "Content-Type": "application/json",
    },
    body: body ? JSON.stringify(body) : undefined,
  });

  let data = null;
  try {
    data = await response.json();
  } catch {
    data = null;
  }

  if (!response.ok) {
    const message = data?.detail || `Request failed with status ${response.status}`;
    throw new Error(message);
  }

  return data;
}

export const api = {
  get: (path) => request("GET", path),
  post: (path, body) => request("POST", path, body),
  put: (path, body) => request("PUT", path, body),
  patch: (path, body) => request("PATCH", path, body),
  delete: (path) => request("DELETE", path),
};

export const endpoints = {
  summary: (city, units = "metric") => `/api/executive-summary?city=${encodeURIComponent(city)}&units=${encodeURIComponent(units)}`,
  weather: (city, units = "metric") => `/api/info/weather?city=${encodeURIComponent(city)}&units=${encodeURIComponent(units)}`,
  meetings: "/api/meetings",
  reminders: "/api/reminders",
  notifications: "/api/notifications",
};
