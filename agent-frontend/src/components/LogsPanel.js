import React from "react";
import PropTypes from 'prop-types';
import { Card, CardContent, Typography, Box, Collapse, IconButton, Button } from "@mui/material";
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import DownloadIcon from '@mui/icons-material/Download';

export default function LogsPanel({ logs, logsOpen, setLogsOpen, downloadLogs, clearLogs }) {
  return (
    <Card sx={{ mb: 3 }}>
      <CardContent>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Typography variant="h6">Logs</Typography>
          <Box>
            <IconButton onClick={downloadLogs} size="small" title="Download logs">
              <DownloadIcon />
            </IconButton>
            <IconButton onClick={() => setLogsOpen(o => !o)} size="small" title={logsOpen ? "Hide logs" : "Show logs"}>
              {logsOpen ? <ExpandLessIcon /> : <ExpandMoreIcon />}
            </IconButton>
          </Box>
        </Box>
        <Collapse in={logsOpen}>
          <Box sx={{ maxHeight: 200, overflow: "auto", background: "#222", color: "#fff", p: 1, borderRadius: 1, mt: 1 }}>
            {logs.map((line, i) => <div key={i}>{line}</div>)}
          </Box>
          <Box display="flex" justifyContent="flex-end" mt={1}>
            <Button variant="outlined" color="secondary" size="small" onClick={clearLogs}>
              Clear Logs
            </Button>
          </Box>
        </Collapse>
      </CardContent>
    </Card>
  );
}

LogsPanel.propTypes = {
  logs: PropTypes.array.isRequired,
  logsOpen: PropTypes.bool.isRequired,
  setLogsOpen: PropTypes.func.isRequired,
  downloadLogs: PropTypes.func.isRequired,
  clearLogs: PropTypes.func.isRequired,
};
