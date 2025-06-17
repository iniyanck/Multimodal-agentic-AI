"""
PlanningPrompt class for generating planning prompts for LLM.
"""

try:
    from ..action_executor import ActionExecutor
    allowed_actions = sorted(ActionExecutor.ALLOWED_ACTIONS)
except ImportError:
    # Fallback: define allowed actions inline if import fails
    allowed_actions = [
        "read_file", "write_file", "execute_shell_command", "focus_window", "list_directory", "capture_screen", "move_mouse", "wait", "task_complete", "type_text", "press_key", "hotkey", "click", "ask_user"
    ]

class PlanningPrompt:
    def __init__(self):
        self.base_instruction = (
            "You are an AI agent designed to interact with a computer system. "
            "Your goal is to accurately understand and execute user tasks."
        )

    def get_planning_prompt(self, task_description: str, current_context: str, tools_description: str, history: list) -> str:
        allowed_actions_str = ', '.join(f'"{a}"' for a in allowed_actions)
        history_str = "\n".join([
            f"- {entry['action']['action']} (Result: {entry.get('feedback', 'No feedback')})"
            for entry in history[-5:]
        ])
        return f"""
        {self.base_instruction}

        You are currently in the planning phase. Your objective is to break down the main task into a sequence of smaller, manageable steps. For each step, you should decide which tool to use and provide a brief description of the step.

        Here is the main task you need to accomplish:
        Task: "{task_description}"

        Current System Context/Observations:
        {current_context}

        Available Tools and their usage:
        {tools_description}

        ***IMPORTANT: You may ONLY use the following actions/tools in your plan: {allowed_actions_str}. Do NOT use any other action or tool not listed here. Prefer executing shell commands over other actions. If you think about it, most tasks can be completed with the shell alone.***

        Recent Action History (for context and learning from past attempts):
        {history_str if history_str else "No recent history."}

        Based on the task and available tools, provide a plan as a JSON array of objects. Each object in the array should represent a step in your plan and *must* have an "action" key (the name of the tool to use) and a "description" key. You can also include other parameters for the action if you know them (e.g., "file" for "read_file"). The "action" key must directly map to one of the available tools.

        You should use yor ingenuity and common sense to effectively complete the task

        ***When planning to complete a task, consider using visual cues by capturing the screen (using the 'capture_screen' action) and analyzing the result to confirm that the task is truly complete before using 'task_complete'.***

        Example Plan Structure:
        {{
            "plan": [
                {{"action": "list_directory", "description": "First, I need to see what files are in the current directory."}},
                {{"action": "read_file", "file": "important_doc.txt", "description": "Then, I'll read the important document to gather information."}},
                {{"action": "type_text", "text": "Hello World!", "description": "Finally, I'll type 'Hello World!' into an open application."}},
                {{"action": "capture_screen", "description": "Capture the screen to visually confirm the result before finishing."}},
                {{"action": "task_complete", "description": "The task is finished after visually confirming completion."}}
            ]
        }}
        Provide ONLY the JSON response. Do not include any other text.
        """
