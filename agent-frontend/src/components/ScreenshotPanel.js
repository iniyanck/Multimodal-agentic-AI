import React, { useState } from "react";
import { Card, CardContent, Typography, Box } from "@mui/material";

export default function ScreenshotPanel({ screenshotUrl }) {
  const [imgError, setImgError] = useState(false);
  return (
    <Card sx={{ mb: 3 }}>
      <CardContent>
        <Typography variant="h6">Screenshot</Typography>
        <Box>
          {!imgError ? (
            <img
              src={screenshotUrl}
              alt="Latest Screenshot"
              style={{ maxWidth: "100%", border: "1px solid #ccc", borderRadius: 4, marginTop: 8 }}
              onError={() => setImgError(true)}
            />
          ) : (
            <Typography color="text.secondary" sx={{ mt: 2 }}>
              No screenshot available.
            </Typography>
          )}
        </Box>
      </CardContent>
    </Card>
  );
}
