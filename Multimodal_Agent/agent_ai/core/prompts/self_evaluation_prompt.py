"""
SelfEvaluationPrompt class for generating self-evaluation prompts for LLM.
"""
import json

class SelfEvaluationPrompt:
    def __init__(self, base_instruction=None):
        self.base_instruction = base_instruction or (
            "You are an AI agent designed to interact with a computer system. "
            "Your goal is to accurately understand and execute user tasks."
        )

    def get_self_evaluation_prompt(self, current_task: str, history: list, final_state: dict) -> str:
        history_str = "\n".join([
            f"- {entry['action']['action']} (Result: {entry['action'].get('status', 'unknown')})" for entry in history[-10:]
        ])
        return f"""
        {self.base_instruction}

        The task has been completed. Please provide a critical self-evaluation of your performance on the following task:
        Task: \"{current_task}\"

        Recent Action History (last 10 steps):
        {history_str if history_str else 'No recent history.'}

        Final Agent State:
        {json.dumps(final_state, indent=2)}

        Please answer the following:
        - Did you accomplish the task successfully? Why or why not?
        - What went well, and what could be improved?
        - Were there any mistakes, inefficiencies, or unnecessary steps?
        - What would you do differently next time?
        - Give yourself a score from 1 (poor) to 10 (excellent) for this episode.

        Output ONLY a JSON object with keys: 'success' (true/false), 'score' (1-10), 'strengths', 'weaknesses', 'improvements', and 'summary'.
        Example:
        {{
            "success": true,
            "score": 8,
            "strengths": "Clear planning and correct execution.",
            "weaknesses": "One unnecessary directory listing step.",
            "improvements": "Be more concise in planning.",
            "summary": "The agent completed the task with minor inefficiencies."
        }}
        """
