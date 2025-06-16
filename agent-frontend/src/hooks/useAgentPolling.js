// Custom hook for polling agent status and logs
import { useEffect } from 'react';
import { fetchStatus, fetchLogs, fetchUserInput, fetchScreenshotUrl } from '../services/api';

export default function useAgentPolling({ fresh, quotaError, editingUserInput, setStatus, setLogs, setUserInput, setScreenshotUrl, setPlanningStuck }) {
  useEffect(() => {
    let planningTimer;
    let interval;
    if (!fresh && !quotaError) {
      const poll = async () => {
        const status = await fetchStatus();
        setStatus(status);
        if (status.status === "quota_exceeded") {
          setPlanningStuck(false);
          return;
        }
        if (status.status === "planning") {
          if (!planningTimer) {
            planningTimer = setTimeout(() => setPlanningStuck(true), 30000);
          }
        } else {
          setPlanningStuck(false);
          if (planningTimer) clearTimeout(planningTimer);
        }
        const logs = await fetchLogs();
        setLogs(logs.logs || []);
        const userInput = await fetchUserInput();
        if (!editingUserInput) setUserInput(userInput.user_input || "");
        setScreenshotUrl(fetchScreenshotUrl());
      };
      poll();
      interval = setInterval(poll, 3000);
      return () => {
        clearInterval(interval);
        if (planningTimer) clearTimeout(planningTimer);
      };
    }
    return () => {
      if (planningTimer) clearTimeout(planningTimer);
      if (interval) clearInterval(interval);
    };
  }, [fresh, quotaError]);
}
