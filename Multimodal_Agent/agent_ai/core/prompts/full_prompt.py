"""
FullPrompt class for generating general reasoning prompts for the agent.
"""

class FullPrompt:
    def __init__(self, base_instruction=None):
        self.base_instruction = base_instruction or (
            "You are an AI agent designed to interact with a computer system. "
            "Your goal is to accurately understand and execute user tasks."
        )

    def get_full_prompt(self, **kwargs):
        return f"""
        {self.base_instruction}

        Here is the current state and task:
        Current Task: {kwargs.get('current_task_description')}
        Last Action Feedback: {kwargs.get('last_action_feedback')}
        Last Read Content: {kwargs.get('last_read_content', 'None')}
        Last Directory List: {kwargs.get('last_directory_list', 'None')}
        Last Retrieved Knowledge: {kwargs.get('last_retrieved_knowledge', 'None')}

        Based on the above, decide the next best action in JSON format.
        Available actions are: read_file, write_file, execute_shell_command, list_directory, capture_screen, move_mouse, click, type_text, press_key, hotkey, store_knowledge, retrieve_knowledge, wait, task_complete.

        Your response MUST be a single JSON object with an "action" key and appropriate parameters.
        """
