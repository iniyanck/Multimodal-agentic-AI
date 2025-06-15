# agent_ai/core/global_prompt.py (Conceptual changes)
import json

class GlobalPrompt:
    def __init__(self):
        self.base_instruction = "You are an AI agent designed to interact with a computer system. Your goal is to accurately understand and execute user tasks."

    def get_planning_prompt(self, task_description: str, current_context: str, tools_description: str, history: list) -> str:
        """
        Generates a prompt for the LLM to create a plan.
        """
        history_str = "\n".join([f"- {entry['action']['action']} (Result: {entry.get('feedback', 'No feedback')})" for entry in history[-5:]]) # Last 5 entries
        return f"""
        {self.base_instruction}

        You are currently in the planning phase. Your objective is to break down the main task into a sequence of smaller, manageable steps. For each step, you should decide which tool to use and provide a brief description of the step.

        Here is the main task you need to accomplish:
        Task: "{task_description}"

        Current System Context/Observations:
        {current_context}

        Available Tools and their usage:
        {tools_description}

        Recent Action History (for context and learning from past attempts):
        {history_str if history_str else "No recent history."}

        Based on the task and available tools, provide a plan as a JSON array of objects. Each object in the array should represent a step in your plan and *must* have an "action" key (the name of the tool to use) and a "description" key. You can also include other parameters for the action if you know them (e.g., "file" for "read_file"). The "action" key must directly map to one of the available tools.

        Example Plan Structure:
        {{
            "plan": [
                {{"action": "list_directory", "description": "First, I need to see what files are in the current directory."}},
                {{"action": "read_file", "file": "important_doc.txt", "description": "Then, I'll read the important document to gather information."}},
                {{"action": "type_text", "text": "Hello World!", "description": "Finally, I'll type 'Hello World!' into an open application."}},
                {{"action": "task_complete", "description": "The task is finished."}}
            ]
        }}
        Provide ONLY the JSON response. Do not include any other text.
        """

    def get_action_execution_prompt(self, current_task_description: str, current_plan_step: dict, last_action_feedback: str, last_read_content: str, last_directory_list: str, last_retrieved_knowledge: str, history: list) -> str:
        """
        Generates a prompt for the LLM to decide on specific parameters for the current action.
        """
        history_str = "\n".join([f"- {entry['action']['action']} (Result: {entry.get('feedback', 'No feedback')})" for entry in history[-5:]]) # Last 5 entries
        return f"""
        {self.base_instruction}

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
        {history_str if history_str else "No recent history."}

        Based on the current plan step, the overall task, and the provided feedback/observations, decide the exact parameters for the action '{current_plan_step.get('action')}' and provide them as a JSON object. Ensure the JSON object contains an "action" key with the value '{current_plan_step.get('action')}' and all necessary parameters for that action.

        Example for 'write_file' action:
        {{
            "action": "write_file",
            "file": "my_new_file.txt",
            "content": "This is the content I want to write."
        }}
        Example for 'list_directory' action:
        {{
            "action": "list_directory",
            "path": "."
        }}
        Example for 'task_complete' action:
        {{
            "action": "task_complete"
        }}
        Provide ONLY the JSON response. Do not include any other text.
        """
    
    def get_reflection_prompt(self, current_task_description, current_plan_step, action_executed, action_result, current_context, history):
        # Placeholder for reflection prompt generation logic
        # This should construct a prompt that asks the LLM to assess the success
        # of the action, and if the plan step can be considered complete.
        # It should consider the action_result (including any errors),
        # the overall task, and the current plan step.
        prompt = f"Reflecting on the last action: {action_executed.get('action')}.  Action result: {action_result}.  Current task: {current_task_description}.  Current plan step: {current_plan_step}.  Based on the action result, was the action successful and is this plan step complete?  Explain your reasoning.  Output ONLY a JSON object with 'status' ('success' or 'failure'), 'thought' explaining your reasoning, and optionally a 'message' if there are issues.  Example: {{\"status\": \"success\", \"thought\": \"The action completed successfully and achieved the desired state.\"}}"
        return prompt

    def get_full_prompt(self, **kwargs):
        # This method might become less central if planning and action execution have separate prompts.
        # However, it could still be used for a general "reasoning" prompt if the agent needs to
        # decide between planning or executing. For now, it's simplified.
        return f"""
        {self.base_instruction}

        Here is the current state and task:
        Current Task: {kwargs.get('current_task_description')}
        Last Action Feedback: {kwargs.get('last_action_feedback')}
        Last Read Content: {kwargs.get('last_read_content', 'None')}
        Last Directory List: {kwargs.get('last_directory_list', 'None')}
        Last Retrieved Knowledge: {kwargs.get('last_retrieved_knowledge', 'None')}

        Based on the above, decide the next best action in JSON format.
        Available actions are: read_file, write_file, execute_shell_command, list_directory, capture_screen, move_mouse, click, type_text, press_key, hotkey, store_knowledge, retrieve_knowledge, ask_user, wait, task_complete.

        Your response MUST be a single JSON object with an "action" key and appropriate parameters.
        """

    def get_current_context(self, agent_state: dict) -> str:
        """Helper to summarize current relevant context for the LLM."""
        context = []
        if agent_state.get('last_action_feedback'):
            context.append(f"Last action feedback: {agent_state['last_action_feedback']}")
        if agent_state.get('last_read_content'):
            context.append(f"Last file content read: {agent_state['last_read_content'][:200]}...")
        if agent_state.get('last_directory_list'):
            context.append(f"Last directory listing: {agent_state['last_directory_list']}")
        if agent_state.get('last_retrieved_knowledge'):
            context.append(f"Last retrieved knowledge: {agent_state['last_retrieved_knowledge']}")
        # You could also add information about the current screenshot, if parsed.
        return "\n".join(context) if context else "No specific observations yet."