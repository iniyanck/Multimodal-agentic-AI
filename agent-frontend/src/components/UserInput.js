import React from "react";
import PropTypes from 'prop-types';
import { Card, CardContent, Typography, Box, TextField, Button, Alert } from "@mui/material";

export default function UserInput({ userInput, setUserInput, submitUserInput, loading, onFocus, onBlur, pendingQuestion }) {
  return (
    <Card sx={{ mb: 3 }}>
      <CardContent>
        <Typography variant="h6">Direct the Agent (Real-Time Direction/Feedback)</Typography>
        {pendingQuestion && (
          <Alert severity="info" sx={{ mb: 2 }}>
            <strong>Agent asks:</strong> {pendingQuestion}
          </Alert>
        )}
        <Box display="flex" gap={2} mt={1}>
          <TextField
            label="Direction or Feedback (real-time)"
            value={userInput}
            onChange={e => setUserInput(e.target.value)}
            fullWidth
            disabled={loading}
            multiline
            minRows={2}
            onFocus={onFocus}
            onBlur={onBlur}
          />
          <Button variant="outlined" onClick={submitUserInput} disabled={loading}>
            Send
          </Button>
        </Box>
        <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
          This is live: you can direct, correct, or guide the agent at any time. The current value is always shown.
        </Typography>
      </CardContent>
    </Card>
  );
}

UserInput.propTypes = {
  userInput: PropTypes.string.isRequired,
  setUserInput: PropTypes.func.isRequired,
  submitUserInput: PropTypes.func.isRequired,
  loading: PropTypes.bool.isRequired,
  onFocus: PropTypes.func,
  onBlur: PropTypes.func,
  pendingQuestion: PropTypes.string
};
