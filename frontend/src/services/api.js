import axios from "axios";

const baseURL = import.meta.env.VITE_API_BASE_URL || "";

const api = axios.create({
  baseURL: baseURL ? `${baseURL}/api` : "/api",
  timeout: 30000, // 30-second timeout
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor to attach JWT token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("smartdesk_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to handle authentication expiration
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Clear token if invalid or expired
      localStorage.removeItem("smartdesk_token");
      localStorage.removeItem("smartdesk_user");
      if (window.location.pathname !== "/login") {
        window.dispatchEvent(new Event("smartdesk_auth_expired"));
      }
    }
    return Promise.reject(error);
  }
);

export const authApi = {
  login: (email, password) => api.post("/login", { email, password }),
  getMe: () => api.get("/me"),
};

export const ticketApi = {
  list: (params) => api.get("/tickets", { params }),
  get: (id) => api.get(`/tickets/${id}`),
  create: (data) => api.post("/tickets", data),
  update: (id, data) => api.patch(`/tickets/${id}`, data),
  delete: (id) => api.delete(`/tickets/${id}`),
};

export const dashboardApi = {
  getStats: () => api.get("/dashboard/stats"),
};

export const aiApi = {
  analyze: (data) => api.post("/ai/analyze", data),
  chat: (message, history = []) => api.post("/ai/chat", { message, history }),
};

export const knowledgeApi = {
  list: (category) => api.get("/knowledge/articles", { params: { category } }),
  upload: (formData) =>
    api.post("/knowledge/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    }),
};

export const healthApi = {
  check: () => api.get("/health"),
};

export default api;
