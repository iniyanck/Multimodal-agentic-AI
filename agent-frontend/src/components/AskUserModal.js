import React from 'react';
import PropTypes from 'prop-types';
import { Modal, Box, Typography, TextField, Button } from '@mui/material';

export default function AskUserModal({ open, question, answer, setAnswer, onSubmit }) {
  return (
    <Modal open={open}>
      <Box sx={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', bgcolor: 'background.paper', p: 4, borderRadius: 2, boxShadow: 24, minWidth: 320 }}>
        <Typography variant="h6" mb={2}>Agent Needs Your Input</Typography>
        <Typography mb={2}>{question}</Typography>
        <TextField
          label="Your Answer"
          value={answer}
          onChange={e => setAnswer(e.target.value)}
          fullWidth
          multiline
          minRows={2}
          sx={{ mb: 2 }}
        />
        <Button variant="contained" onClick={onSubmit} disabled={!answer.trim()}>
          Submit
        </Button>
      </Box>
    </Modal>
  );
}

AskUserModal.propTypes = {
  open: PropTypes.bool.isRequired,
  question: PropTypes.string,
  answer: PropTypes.string.isRequired,
  setAnswer: PropTypes.func.isRequired,
  onSubmit: PropTypes.func.isRequired,
};
