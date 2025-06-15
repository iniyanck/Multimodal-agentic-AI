import React from "react";
import { Card, CardContent, Typography, Box, TextField, Button } from "@mui/material";

export default function TaskInput({ task, setTask, submitTask, loading }) {
  return (
    <Card sx={{ mb: 3 }}>
      <CardContent>
        <Typography variant="h6">Submit Task</Typography>
        <Box display="flex" gap={2} mt={1}>
          <TextField
            label="Task"
            value={task}
            onChange={e => setTask(e.target.value)}
            fullWidth
            disabled={loading}
          />
          <Button variant="contained" onClick={submitTask} disabled={loading || !task}>
            Send
          </Button>
        </Box>
        <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
          Enter a new task for the agent (not feedback or corrections).
        </Typography>
      </CardContent>
    </Card>
  );
}
