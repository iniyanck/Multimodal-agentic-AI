"""
ActionPrompt class for generating action execution prompts for LLM.
"""
import json

class ActionPrompt:
    def __init__(self, base_instruction=None):
        self.base_instruction = base_instruction or (
            "You are an AI agent designed to interact with a computer system. "
            "Your goal is to accurately understand and execute user tasks."
        )

    def get_action_execution_prompt(self, current_task_description: str, current_plan_step: dict, last_action_feedback: str, last_read_content: str, last_directory_list: str, last_retrieved_knowledge: str, history: list, failed_steps_summary=None, successful_steps_summary=None) -> str:
        history_str = "\n".join([
            f"- {entry['action']['action']} (Result: {entry.get('feedback', 'No feedback')})"
            for entry in history[-5:]
        ])
        failed_str = "\n".join([
            f"Step: {k}, Failures: {v}" for k, v in (failed_steps_summary or {}).items()
        ])
        success_str = "\n".join(successful_steps_summary or [])
        return f"""
        ***IMPORTANT: Your response MUST be a single JSON object that ALWAYS includes an 'action' key (e.g., 'action': 'execute_shell_command'). If you do not include the 'action' key, the agent will fail and your output will be ignored.***
        
        WARNING: If you omit the 'action' key, your response will be discarded and the task will fail. DO NOT OMIT 'action'.
        
        {self.base_instruction}

        ***Before using the 'task_complete' action, you should consider capturing the screen (using 'capture_screen') and using visual cues to confirm that the task is truly complete.***

        You are currently executing a step in your overall plan. Your goal is to provide the exact parameters for the tool specified in the current plan step.

        Overall Task: "{current_task_description}"

        Current Plan Step:
        Action: {current_plan_step.get('action')}
        Description: {current_plan_step.get('description', 'No description provided.')}
        Previous Parameters (if any from plan): {json.dumps({k: v for k, v in current_plan_step.items() if k not in ['action', 'description']})}

        Last Action Feedback: {last_action_feedback}
        Last Read Content: {last_read_content if last_read_content else 'None'}
        Last Directory List: {last_directory_list if last_directory_list else 'None'}
        Last Retrieved Knowledge: {last_retrieved_knowledge if last_retrieved_knowledge else 'None'}

        Recent Action History:
        {history_str if history_str else 'No recent history.'}
        Failed Steps Summary:
        {failed_str if failed_str else 'None'}
        Successful Steps Summary:
        {success_str if success_str else 'None'}

        Example of a VALID response:
        {{
            "action": "execute_shell_command",
            "command": "notepad",
            "background": true
        }}
        
        Example of an INVALID response (do NOT do this):
        {{
            "command": "notepad",
            "background": true
        }}
        
        Provide ONLY the JSON response. Do not include any other text.
        """
