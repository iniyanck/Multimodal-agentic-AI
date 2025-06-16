import React, { useState, useEffect } from "react";
import { Container, Box, Button } from "@mui/material";
import StatusSummary from "./components/StatusSummary";
import TaskInput from "./components/TaskInput";
import UserInput from "./components/UserInput";
import ScreenshotPanel from "./components/ScreenshotPanel";
import LogsPanel from "./components/LogsPanel";
import AskUserModal from "./components/AskUserModal";
import useAgentPolling from "./hooks/useAgentPolling";
import { submitTask as apiSubmitTask, submitUserInput as apiSubmitUserInput, killAgent, clearLogs as apiClearLogs } from "./services/api";
import axios from "axios";

function App() {
  const [task, setTask] = useState("");
  const [userInput, setUserInput] = useState("");
  const [status, setStatus] = useState({});
  const [logs, setLogs] = useState([]);
  const [screenshotUrl, setScreenshotUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [logsOpen, setLogsOpen] = useState(false);
  const [fresh, setFresh] = useState(true);
  const [planningStuck, setPlanningStuck] = useState(false);
  const [editingUserInput, setEditingUserInput] = useState(false);
  const [killing, setKilling] = useState(false);
  const [quotaError, setQuotaError] = useState(false);
  const [pendingQuestion, setPendingQuestion] = useState(null);
  const [pendingAnswer, setPendingAnswer] = useState("");

  useAgentPolling({ fresh, quotaError, editingUserInput, setStatus, setLogs, setUserInput, setScreenshotUrl, setPlanningStuck });

  // Poll for pending question
  useEffect(() => {
    const poll = async () => {
      try {
        const res = await axios.get("http://127.0.0.1:8000/pending_question");
        setPendingQuestion(res.data.question);
      } catch {}
    };
    poll();
    const interval = setInterval(poll, 2000);
    return () => clearInterval(interval);
  }, []);

  const submitTask = async () => {
    setLoading(true);
    try {
      await apiSubmitTask(task);
      setTask("");
      setFresh(false);
    } catch (e) {
      alert(e.response?.data?.error || "Failed to submit task");
    }
    setLoading(false);
  };

  const submitUserInput = async () => {
    setLoading(true);
    try {
      await apiSubmitUserInput(userInput);
      setEditingUserInput(false);
    } catch (e) {
      alert("Failed to send direction/feedback");
    }
    setLoading(false);
  };

  const resetAgent = async () => {
    setLoading(true);
    try {
      await killAgent();
      setTask("");
      setUserInput("");
      setStatus({});
      setLogs([]);
      setScreenshotUrl("");
      setLogsOpen(false);
      setFresh(true);
      setQuotaError(false);
    } catch (e) {
      alert("Failed to reset agent");
    }
    setLoading(false);
  };

  const killSwitch = async () => {
    setKilling(true);
    setLoading(true);
    try {
      await killAgent();
      setTask("");
      setStatus({});
      setLogs([]);
      setScreenshotUrl("");
      setLogsOpen(false);
      setUserInput("");
      setFresh(true);
      setKilling(false);
      window.location.reload();
    } catch (e) {
      alert("Failed to kill/reset agent");
      setKilling(false);
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

  const clearLogs = async () => {
    setLoading(true);
    try {
      await apiClearLogs();
      setLogs([]);
    } catch (e) {
      alert("Failed to clear logs");
    }
    setLoading(false);
  };

  const submitPendingAnswer = async () => {
    await axios.post("http://127.0.0.1:8000/pending_answer", { answer: pendingAnswer });
    setPendingQuestion(null);
    setPendingAnswer("");
  };

  return (
    <>
      <AskUserModal
        open={!!pendingQuestion}
        question={pendingQuestion}
        answer={pendingAnswer}
        setAnswer={setPendingAnswer}
        onSubmit={submitPendingAnswer}
      />
      <Container maxWidth="md" sx={{ mt: 4, mb: 4, background: '#f7f9fb', borderRadius: 3, boxShadow: 2, p: { xs: 1, sm: 3 } }}>
        <h1 style={{ textAlign: "center", fontWeight: 700, letterSpacing: 1, marginBottom: 24, color: '#1a237e' }}>Multimodal Agent Dashboard</h1>
        {quotaError ? (
          <Box display="flex" flexDirection="column" alignItems="center" mb={2}>
            <Box color="error.main" fontWeight={600} mb={1}>
              LLM quota or rate limit exceeded. Please reset or try again later.
            </Box>
            <Button variant="contained" color="secondary" onClick={resetAgent} disabled={loading || killing} sx={{ mr: 1 }}>
              Reset Agent
            </Button>
            <Button variant="contained" color="error" onClick={killSwitch} disabled={loading || killing}>
              {killing ? "Killing agent..." : "Kill Switch (Full Reset)"}
            </Button>
          </Box>
        ) : planningStuck ? (
          <Box display="flex" flexDirection="column" alignItems="center" mb={2}>
            <Box color="error.main" fontWeight={600} mb={1}>
              Agent appears stuck in planning. This may be due to an LLM or parsing error.
            </Box>
            <Button variant="contained" color="secondary" onClick={resetAgent} disabled={loading || killing} sx={{ mr: 1 }}>
              Reset Agent
            </Button>
            <Button variant="contained" color="error" onClick={killSwitch} disabled={loading || killing}>
              {killing ? "Killing agent..." : "Kill Switch (Full Reset)"}
            </Button>
          </Box>
        ) : (
          <Box display="flex" justifyContent="center" mb={2} gap={2}>
            {/* Only show kill switch if not planningStuck */}
            {!planningStuck && (
              <Button variant="contained" color="error" onClick={killSwitch} disabled={loading || killing}>
                {killing ? "Killing agent..." : "Kill Switch (Full Reset)"}
              </Button>
            )}
            {(!fresh && (status.status === "completed" || status.status === "idle" || status.status === "aborted")) && (
              <Button variant="contained" color="secondary" onClick={resetAgent} disabled={loading || killing}>
                Reset Agent
              </Button>
            )}
          </Box>
        )}
        <TaskInput task={task} setTask={setTask} submitTask={submitTask} loading={loading || killing || quotaError || (!fresh && !(status.status === "idle" || status.status === "completed" || status.status === "aborted"))}
        />
        <Box display="flex" flexDirection={{ xs: 'column', md: 'row' }} gap={3} mb={3}>
          <Box flex={1} minWidth={0}>
            {!fresh && <StatusSummary status={status} />}
          </Box>
          <Box flex={1} minWidth={0}>
            <UserInput
              userInput={userInput}
              setUserInput={setUserInput}
              submitUserInput={submitUserInput}
              loading={loading || killing || quotaError}
              onFocus={() => setEditingUserInput(true)}
              onBlur={() => setEditingUserInput(false)}
              pendingQuestion={pendingQuestion}
            />
          </Box>
        </Box>
        <ScreenshotPanel screenshotUrl={screenshotUrl} />
        <LogsPanel logs={logs} logsOpen={logsOpen} setLogsOpen={setLogsOpen} downloadLogs={downloadLogs} clearLogs={clearLogs} />
      </Container>
    </>
  );
}

export default App;