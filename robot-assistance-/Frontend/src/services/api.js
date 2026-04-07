const API_BASE = import.meta.env.VITE_API_BASE_URL?.trim() || "";

async function request(method, path, body) {
  const url = `${API_BASE}${path}`;
  const response = await fetch(url, {
    method,
    headers: { "Content-Type": "application/json" },
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
    const error = new Error(message);
    error.status = response.status;
    error.data = data;
    throw error;
  }

  return data;
}

function query(params) {
  const search = new URLSearchParams();

  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === null || value === "") return;
    search.set(key, String(value));
  });

  const serialized = search.toString();
  return serialized ? `?${serialized}` : "";
}

export const api = {
  get: (path) => request("GET", path),
  post: (path, body) => request("POST", path, body),
  put: (path, body) => request("PUT", path, body),
  patch: (path, body) => request("PATCH", path, body),
  delete: (path) => request("DELETE", path),
};

export const backendApi = {
  health: () => api.get("/api/health"),
  info: () => api.get("/api/info"),
  weatherStatus: () => api.get("/api/weather/status"),
  weatherCurrent: ({ city, units = "metric" }) =>
    api.get(`/api/weather/current${query({ city, units })}`),
  googleAuthStatus: () => api.get("/api/auth/google/status"),
  googleAuthUrl: () => api.get("/api/auth/google/url"),
  executiveSummary: ({ city, units = "metric" }) =>
    api.get(`/api/executive-summary${query({ city, units })}`),

  users: {
    list: (activeOnly = false) => api.get(`/api/users${query({ active_only: activeOnly || undefined })}`),
    create: (payload) => api.post("/api/users", payload),
    update: (userId, payload) => api.put(`/api/users/${userId}`, payload),
    deactivate: (userId) => api.delete(`/api/users/${userId}`),
  },

  meetings: {
    list: () => api.get("/api/meetings"),
    listToday: () => api.get("/api/meetings/today"),
    get: (meetingId) => api.get(`/api/meetings/${meetingId}`),
    create: (payload) => api.post("/api/meetings", payload),
    update: (meetingId, payload) => api.put(`/api/meetings/${meetingId}`, payload),
    updateAvailability: (meetingId, availability) =>
      api.patch(`/api/meetings/${meetingId}/availability`, { availability }),
    updateAlerts: (meetingId, alertMinutes) =>
      api.patch(`/api/meetings/${meetingId}/alerts`, { alert_minutes: alertMinutes }),
    remove: (meetingId) => api.delete(`/api/meetings/${meetingId}`),
  },

  reminders: {
    list: () => api.get("/api/reminders"),
    listByMeeting: (meetingId) => api.get(`/api/meetings/${meetingId}/reminders`),
    create: (payload) => api.post("/api/reminders", payload),
    update: (reminderId, payload) => api.put(`/api/reminders/${reminderId}`, payload),
    remove: (reminderId) => api.delete(`/api/reminders/${reminderId}`),
  },

  notifications: {
    list: () => api.get("/api/notifications"),
    listByMeeting: (meetingId) => api.get(`/api/meetings/${meetingId}/notifications`),
    create: (payload) => api.post("/api/notifications", payload),
    update: (notificationId, payload) => api.put(`/api/notifications/${notificationId}`, payload),
    remove: (notificationId) => api.delete(`/api/notifications/${notificationId}`),
  },
};
