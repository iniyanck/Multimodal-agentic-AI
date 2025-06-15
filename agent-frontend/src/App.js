import React, { useState, useEffect } from "react";
import axios from "axios";
import { Container, Box, Button } from "@mui/material";
import StatusSummary from "./components/StatusSummary";
import TaskInput from "./components/TaskInput";
import UserInput from "./components/UserInput";
import ScreenshotPanel from "./components/ScreenshotPanel";
import LogsPanel from "./components/LogsPanel";

const API_BASE = "http://127.0.0.1:8000";

function App() {
  const [task, setTask] = useState("");
  const [userInput, setUserInput] = useState("");
  const [status, setStatus] = useState({});
  const [logs, setLogs] = useState([]);
  const [screenshotUrl, setScreenshotUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [logsOpen, setLogsOpen] = useState(false);
  const [fresh, setFresh] = useState(true); // new state

  // Only poll agent state if not fresh
  useEffect(() => {
    if (!fresh) {
      const fetchStatus = () => {
        axios.get(`${API_BASE}/status`).then(res => setStatus(res.data));
        axios.get(`${API_BASE}/logs`).then(res => setLogs(res.data.logs || []));
        axios.get(`${API_BASE}/user_input`).then(res => setUserInput(res.data.user_input || ""));
        setScreenshotUrl(`${API_BASE}/screenshot?${Date.now()}`); // bust cache
      };
      fetchStatus();
      const interval = setInterval(fetchStatus, 3000);
      return () => clearInterval(interval);
    }
  }, [fresh]);

  // On first load or after kill, clear all UI state except feedback/user input
  useEffect(() => {
    setTask("");
    setStatus({});
    setLogs([]);
    setScreenshotUrl("");
    setLogsOpen(false);
    setFresh(true);
  }, []);

  const submitTask = async () => {
    setLoading(true);
    try {
      await axios.post(`${API_BASE}/task`, { task });
      setTask("");
      setFresh(false); // Start polling after first task
    } catch (e) {
      alert(e.response?.data?.error || "Failed to submit task");
    }
    setLoading(false);
  };

  const submitUserInput = async () => {
    setLoading(true);
    try {
      await axios.post(`${API_BASE}/user_input`, { user_input: userInput });
    } catch (e) {
      alert("Failed to send direction/feedback");
    }
    setLoading(false);
  };

  const resetAgent = async () => {
    setLoading(true);
    try {
      await axios.post(`${API_BASE}/reset`);
      setTask("");
      setUserInput("");
      setStatus({});
      setLogs([]);
      setScreenshotUrl("");
      setLogsOpen(false);
      setFresh(true);
    } catch (e) {
      alert("Failed to reset agent");
    }
    setLoading(false);
  };

  const killSwitch = async () => {
    setLoading(true);
    try {
      await axios.post(`${API_BASE}/kill`);
      setTask("");
      setStatus({});
      setLogs([]);
      setScreenshotUrl("");
      setLogsOpen(false);
      setUserInput("");
      setFresh(true);
      window.location.reload();
    } catch (e) {
      alert("Failed to kill/reset agent");
    }
    setLoading(false);
  };

  const downloadLogs = () => {
    const element = document.createElement("a");
    const file = new Blob([logs.join("\n")], { type: 'text/plain' });
    element.href = URL.createObjectURL(file);
    element.download = "agent_logs.txt";
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  return (
    <Container maxWidth="md" sx={{ mt: 4, mb: 4, background: '#f7f9fb', borderRadius: 3, boxShadow: 2, p: { xs: 1, sm: 3 } }}>
      <h1 style={{ textAlign: "center", fontWeight: 700, letterSpacing: 1, marginBottom: 24, color: '#1a237e' }}>Multimodal Agent Dashboard</h1>
      <Box display="flex" justifyContent="center" mb={2} gap={2}>
        <Button variant="contained" color="error" onClick={killSwitch} disabled={loading}>
          Kill Switch (Full Reset)
        </Button>
        {(!fresh && (status.status === "completed" || status.status === "idle" || status.status === "aborted")) && (
          <Button variant="contained" color="secondary" onClick={resetAgent} disabled={loading}>
            Reset Agent
          </Button>
        )}
      </Box>
      <TaskInput task={task} setTask={setTask} submitTask={submitTask} loading={loading || (!fresh && !(status.status === "idle" || status.status === "completed" || status.status === "aborted"))}
      />
      <Box display="flex" flexDirection={{ xs: 'column', md: 'row' }} gap={3} mb={3}>
        <Box flex={1} minWidth={0}>
          {!fresh && <StatusSummary status={status} />}
        </Box>
        <Box flex={1} minWidth={0}>
          <UserInput userInput={userInput} setUserInput={setUserInput} submitUserInput={submitUserInput} loading={loading} />
        </Box>
      </Box>
      <ScreenshotPanel screenshotUrl={screenshotUrl} />
      <LogsPanel logs={logs} logsOpen={logsOpen} setLogsOpen={setLogsOpen} downloadLogs={downloadLogs} />
    </Container>
  );
}

export default App;