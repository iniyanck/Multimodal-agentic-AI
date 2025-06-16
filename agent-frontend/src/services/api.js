// API service for backend communication
import axios from 'axios';

const API_BASE = "http://127.0.0.1:8000";

export const fetchStatus = () => axios.get(`${API_BASE}/status`).then(res => res.data);
export const fetchLogs = () => axios.get(`${API_BASE}/logs`).then(res => res.data);
export const fetchUserInput = () => axios.get(`${API_BASE}/user_input`).then(res => res.data);
export const fetchScreenshotUrl = () => `${API_BASE}/screenshot?${Date.now()}`;
export const submitTask = (task) => axios.post(`${API_BASE}/task`, { task });
export const submitUserInput = (userInput) => axios.post(`${API_BASE}/user_input`, { user_input: userInput });
export const killAgent = () => axios.post(`${API_BASE}/kill`);
export const clearLogs = () => axios.post(`${API_BASE}/clear_logs`);
