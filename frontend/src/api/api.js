import axios from "axios";

const api = axios.create({
  baseURL: "/api",
  headers: { "Content-Type": "application/json" },
});

export const fetchHCPs = () => api.get("/hcps");

export const fetchInteractions = (hcpId) =>
  api.get("/interactions", { params: hcpId ? { hcp_id: hcpId } : {} });

export const createInteraction = (payload) => api.post("/interactions", payload);

export const updateInteraction = (id, payload) => api.put(`/interactions/${id}`, payload);

export const sendChatMessage = (payload) => api.post("/chat", payload);

export default api;
