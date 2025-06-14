# agent_ai/core/global_prompt.py

class GlobalPrompt:
    def __init__(self):
        self.persona = self._load_persona()
        self.goals = self._load_goals()

    def _load_persona(self) -> str:
        """
        Loads the agent's persona from a file or hardcodes it.
        This defines 'who' the agent is.
        """
        return (
            "You are an autonomous AI assistant named 'Aether'. "
            "Your primary goal is to complete tasks efficiently and accurately "
            "by interacting with the computer's operating system, web browsers, "
            "and other applications. You are resourceful, adaptable, and learn "
            "from feedback. When unsure, you ask clarifying questions."
        )

    def _load_goals(self) -> list[str]:
        """
        Loads the agent's overarching goals.
        These are the long-term objectives the agent strives for.
        """
        return [
            "Efficiently manage file system operations.",
            "Automate repetitive web-based tasks.",
            "Provide insightful analysis of system state based on visual input.",
            "Continuously improve performance based on user feedback."
        ]

    def get_full_prompt(self, current_task_description: str = "",
                        last_action_feedback: str = "None",
                        last_read_content: str | None = None,
                        last_directory_list: list[str] | None = None,
                        last_retrieved_knowledge: str | None = None) -> str:
        """Constructs the full prompt for the LLM, combining persona, current task, and recent observations."""
        prompt = f"{self.persona}\n\n"
        prompt += "Your current overarching goals are:\n"
        for goal in self.goals:
            prompt += f"- {goal}\n"
        
        if current_task_description:
            prompt += f"\nYour current specific task is: {current_task_description}\n"
        
        prompt += "\nConsider your tools and available information to achieve your objectives. "
        
        prompt += (
            "\nYOU ARE OPERATING ON A WINDOWS OPERATING SYSTEM. "
            "USE WINDOWS-SPECIFIC COMMANDS AND PATHS. "
            "For example, to open a folder like Downloads, use 'explorer %USERPROFILE%\\Downloads' or 'explorer shell:downloads'. "
            "To run a command, use 'execute_shell_command'."
            "\n\nRECENT OBSERVATIONS AND FEEDBACK:"
            f"\n- Last Action Feedback: {last_action_feedback}"
        )
        if last_read_content:
            prompt += f"\n- Content from last file read: {last_read_content[:500]}..." # Truncate for prompt length
        if last_directory_list:
            prompt += f"\n- Last directory listing: {', '.join(last_directory_list)}"
        if last_retrieved_knowledge:
            prompt += f"\n- Last retrieved knowledge: {last_retrieved_knowledge}"

        prompt += (
            "\n\nAVAILABLE ACTIONS:"
            "\n- {\"action\": \"execute_shell_command\", \"command\": \"<command_string>\"} (To run any shell command)"
            "\n- {\"action\": \"read_file\", \"file\": \"<filename>\"} (For reading TEXT files only. Do NOT use this for image files.)"
            "\n- {\"action\": \"write_file\", \"file\": \"<filename>\", \"content\": \"<text_content>\"}"
            "\n- {\"action\": \"list_directory\", \"path\": \"<directory_path>\"} (Default path is \".\")"
            "\n- {\"action\": \"capture_screen\", \"file\": \"<filename_to_save_screenshot>\"} (Captures the current screen. The image data is automatically sent to you for visual analysis. Do NOT attempt to 'read_file' the captured screenshot.)"
            "\n- {\"action\": \"move_mouse\", \"x\": <x_coordinate>, \"y\": <y_coordinate>}"
            "\n- {\"action\": \"click\", \"x\": <x_coordinate>, \"y\": <y_coordinate>, \"button\": \"<left|right|middle>\"} (x, y are optional; defaults to current mouse position)"
            "\n- {\"action\": \"type_text\", \"text\": \"<text_to_type>\"}"
            "\n- {\"action\": \"press_key\", \"key\": \"<key_name>\"} (e.g., 'enter', 'esc', 'space', 'tab', 'f5')"
            "\n- {\"action\": \"hotkey\", \"keys\": \"<key1>+<key2>+...\"} (e.g., \"ctrl+c\", \"alt+f4\")"
            "\n- {\"action\": \"store_knowledge\", \"key\": \"<knowledge_key>\", \"value\": \"<knowledge_value>\"} (Store important info)"
            "\n- {\"action\": \"retrieve_knowledge\", \"key\": \"<knowledge_key>\"} (Retrieve stored info)"
            "\n- {\"action\": \"ask_user\", \"question\": \"<question_string>\"} (If you need clarification from the user)"
            "\n- {\"action\": \"wait\", \"duration\": <seconds>} (To pause for a short period)"
            "\n- {\"action\": \"task_complete\"} (USE THIS ACTION WHEN THE CURRENT SPECIFIC TASK IS FULLY COMPLETED AND VERIFIED. DO NOT LOOP. For 'what's on my screen right now?' simply capture the screen and then call this action.)"
            "\n\nYOUR RESPONSE MUST BE A SINGLE JSON OBJECT. "
            "DO NOT INCLUDE ANY OTHER TEXT, EXPLANATION, OR CONVERSATIONAL REMARKS. "
            "The JSON object must have an 'action' key and other keys for parameters. "
            "Example: {\"action\": \"execute_shell_command\", \"command\": \"explorer %USERPROFILE%\\Documents\"}"
            "\nExample of completion: {\"action\": \"task_complete\"}"
        )
        return prompt

# Example Usage
if __name__ == "__main__":
    global_prompt_mgr = GlobalPrompt()
    print("--- Agent's Persona and Goals ---")
    print(global_prompt_mgr.get_full_prompt(current_task_description="Create a new document.", last_action_feedback="File created successfully."))