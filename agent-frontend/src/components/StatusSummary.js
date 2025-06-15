import React from "react";
import { Stack, Box, Chip, Typography } from "@mui/material";

export default function StatusSummary({ status }) {
  if (!status || typeof status !== "object") return null;
  return (
    <Stack spacing={1}>
      <Box>
        <Chip label={`Status: ${status.status || "-"}`} color="primary" clickable={false} />
        {status.current_task && (
          <Chip label={`Task: ${status.current_task}`} sx={{ ml: 1 }} clickable={false} />
        )}
      </Box>
      {status.current_plan && status.current_plan.length > 0 && (
        <Box>
          <Typography variant="subtitle2" sx={{ mt: 1 }}>Current Plan:</Typography>
          <ol style={{ margin: 0, paddingLeft: 20 }}>
            {status.current_plan.map((step, idx) => (
              <li key={idx} style={{ fontWeight: idx === status.plan_step ? "bold" : "normal" }}>
                {step.description || step.action || JSON.stringify(step)}
                {idx === status.plan_step && <Chip label="In Progress" size="small" color="secondary" sx={{ ml: 1 }} clickable={false} />}
              </li>
            ))}
          </ol>
        </Box>
      )}
      {status.history && status.history.length > 0 && (
        <Box>
          <Typography variant="subtitle2" sx={{ mt: 1 }}>Recent Actions:</Typography>
          <ul style={{ margin: 0, paddingLeft: 20 }}>
            {status.history.slice(-3).reverse().map((h, i) => (
              <li key={i}>{h.action?.action || JSON.stringify(h.action)}</li>
            ))}
          </ul>
        </Box>
      )}
    </Stack>
  );
}
