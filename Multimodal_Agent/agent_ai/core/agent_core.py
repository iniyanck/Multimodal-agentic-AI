# agent_ai/core/agent_core.py

from ..perception.file_io import FileIO
from ..perception.screen_capture import ScreenCapture
from ..action.system_interaction import SystemInteraction
from ..action.feedback_handler import FeedbackHandler
from ..memory.knowledge_base import KnowledgeBase
from ..core.global_prompt import GlobalPrompt
import time
import json
import io
import base64
from PIL import Image # Import PIL for image handling
from ..utils.logger import Logger

# You'll need an LLM client library (e.g., openai, google-generativeai)
# For demonstration, we'll use a placeholder for LLM interaction.

class AgentCore:
    def __init__(self, llm_client=None): # Pass your LLM client here
        self.file_io = FileIO()
        self.screen_capture = ScreenCapture()
        self.system_interaction = SystemInteraction()
        self.feedback_handler = FeedbackHandler()
        self.knowledge_base = KnowledgeBase()
        self.global_prompt_manager = GlobalPrompt()
        self.llm_client = llm_client # Your LLM client instance (e.g., GoogleGenerativeAI, OpenAI)
        self.agent_state = self.knowledge_base.load_agent_state() or {"status": "idle", "current_task": "None", "history": []}
        self.logger = Logger() # Initialize your logger
        # Initialize last_screenshot_pil to None or a default if no screenshot is taken yet
        self.last_screenshot_pil = None

    def _call_llm(self, prompt: str, image_data: bytes | None = None) -> str:
        """
        Placeholder for calling your Large Language Model.
        This is where you'd integrate with OpenAI, Google Gemini, etc.
        If using a multimodal LLM, pass image_data.
        """
        if self.llm_client is None:
            self.logger.error("LLM client is not configured. Cannot make API call.")
            return json.dumps({"action": "unknown", "error": "LLM not configured"})

        try:
            contents = [prompt]
            if image_data:
                try:
                    # Convert bytes image_data to PIL Image
                    pil_image = Image.open(io.BytesIO(image_data))
                    contents.append(pil_image)
                    self.last_screenshot_pil = pil_image # Store for potential future use or debugging
                except Exception as img_e:
                    self.logger.error(f"Error converting image data to PIL Image: {img_e}")
                    # Decide if you want to proceed without the image or raise an error
                    # For now, we'll log and continue without the image

            self.logger.info(f"Sending prompt to LLM (first 500 chars): {prompt[:500]}...")
            if image_data:
                self.logger.info("Image data included in LLM call.")

            response = self.llm_client.generate_content(
                contents=contents,
                generation_config={"temperature": 0.7} # Adjust temperature as needed
            )

            if not hasattr(response, 'text') or not response.text:
                self.logger.error("LLM returned empty or malformed response object.")
                return json.dumps({"action": "unknown", "error": "LLM returned empty response"})

            self.logger.info(f"Received LLM response (first 200 chars): {response.text[:200]}...")
            return response.text

        except Exception as e:
            self.logger.error(f"Error calling LLM API: {e}", exc_info=True)
            return json.dumps({"action": "unknown", "error": f"LLM API error: {e}"})

    def _parse_llm_response(self, response: str) -> dict:
        """
        Parses the LLM's response assuming it contains a JSON string.
        It tries to extract the JSON block even if there's surrounding text.
        Example: {"action": "read_file", "file": "example.txt"}
        """
        try:
            # Attempt to find the JSON part by looking for the first '{' and last '}'
            start_idx = response.find('{')
            end_idx = response.rfind('}')

            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                json_string = response[start_idx : end_idx + 1]
                parsed_data = json.loads(json_string)

                if "action" not in parsed_data:
                    self.logger.error(f"Parsed JSON missing 'action' key: {parsed_data}")
                    return {"action": "unknown", "error": "Parsed JSON missing 'action' key"}

                return parsed_data
            else:
                self.logger.error(f"LLM response does not contain valid JSON structure: {response}")
                return {"action": "unknown", "error": "LLM response not in JSON format"}

        except json.JSONDecodeError as e:
            self.logger.error(f"JSON decoding error in LLM response '{response}': {e}", exc_info=True)
            return {"action": "unknown", "error": f"JSON decode error: {e}"}
        except Exception as e:
            self.logger.error(f"Unexpected error parsing LLM response '{response}': {e}", exc_info=True)
            return {"action": "unknown", "error": f"Unexpected parsing error: {e}"}

    def _execute_action(self, parsed_action: dict) -> str:
        """Executes the action decided by the LLM."""
        action_type = parsed_action.get("action")
        feedback = "Action executed successfully."

        # Add a record to history for debugging and future context
        action_entry = {"timestamp": time.time(), "action": parsed_action}
        self.agent_state["history"].append(action_entry)

        try:
            if action_type == "read_file":
                filename = parsed_action.get("file")
                content = self.file_io.read_file(filename)
                self.agent_state["last_read_content"] = content
                feedback = f"Read content of {filename}: {content[:100]}..." if content else f"File read failed for {filename}."
            elif action_type == "write_file":
                filename = parsed_action.get("file")
                content = parsed_action.get("content")
                if self.file_io.write_file(filename, content):
                    feedback = f"Wrote to {filename}."
                else:
                    feedback = f"Failed to write to {filename}."
            elif action_type == "execute_shell_command":
                command = parsed_action.get("command")
                if command:
                    return_code, stdout, stderr = self.system_interaction.execute_shell_command(command)
                    if return_code == 0:
                        feedback = f"Command '{command}' executed successfully. Output: {stdout.strip()}"
                    else:
                        feedback = f"Command '{command}' failed (Exit Code: {return_code}). Error: {stderr.strip()}"
                else:
                    feedback = "execute_shell_command action missing 'command' parameter."
                    self.logger.warning(feedback)
            elif action_type == "list_directory":
                path = parsed_action.get("path", ".")
                contents = self.file_io.list_directory(path)
                self.agent_state["last_directory_list"] = contents
                feedback = f"Directory contents of {path}: {contents}" if contents is not None else "Directory listing failed."
            elif action_type == "capture_screen":
                filename = parsed_action.get("file")
                screenshot_bytes = self.screen_capture.capture_screen_bytes(filename)
                if screenshot_bytes:
                    # Encode bytes to base64 string before storing in JSON-serializable state
                    self.agent_state["last_screenshot_bytes"] = base64.b64encode(screenshot_bytes).decode('utf-8')
                    feedback = f"Captured screen to {filename}."
                else:
                    feedback = "Screen capture failed."
            elif action_type == "move_mouse":
                x = int(parsed_action.get("x", 0))
                y = int(parsed_action.get("y", 0))
                self.system_interaction.move_mouse(x, y)
                feedback = f"Moved mouse to ({x},{y})."
            elif action_type == "click":
                x = int(parsed_action.get("x", -1)) # -1 indicates current position
                y = int(parsed_action.get("y", -1))
                button = parsed_action.get("button", "left")
                if x != -1 and y != -1:
                    self.system_interaction.click(x, y, button)
                else:
                    self.system_interaction.click(button=button)
                feedback = f"Clicked at ({x},{y}) with {button} button."
            elif action_type == "type_text":
                text = parsed_action.get("text")
                self.system_interaction.type_text(text)
                feedback = f"Typed text: '{text}'."
            elif action_type == "press_key":
                key = parsed_action.get("key")
                self.system_interaction.press_key(key)
                feedback = f"Pressed key: '{key}'."
            elif action_type == "hotkey":
                keys = parsed_action.get("keys", "").split('+') # e.g., "ctrl+c"
                self.system_interaction.hotkey(*keys)
                feedback = f"Pressed hotkey: {keys}."
            elif action_type == "store_knowledge":
                key = parsed_action.get("key")
                value = parsed_action.get("value")
                if self.knowledge_base.store_knowledge(key, value):
                    feedback = f"Knowledge '{key}' stored."
                else:
                    feedback = f"Failed to store knowledge '{key}'."
            elif action_type == "retrieve_knowledge":
                key = parsed_action.get("key")
                value = self.knowledge_base.retrieve_knowledge(key)
                # If retrieved knowledge is a base64 encoded image, you might want to decode it here
                # or handle it based on the key/context. For now, we store as is.
                self.agent_state["last_retrieved_knowledge"] = value
                feedback = f"Retrieved knowledge for '{key}': {value}" if value else f"No knowledge for '{key}'."
            elif action_type == "ask_user":
                question = parsed_action.get("question")
                print(f"\nAGENT ASKS: {question}")
                user_response = input("Your response: ")
                self.feedback_handler.receive_feedback(user_response)
                feedback = f"User asked: {question}. User responded: {user_response}"
            elif action_type == "wait":
                duration = int(parsed_action.get("duration", 1))
                print(f"Agent waiting for {duration} seconds...")
                self.logger.info(f"Agent waiting for {duration} seconds...")
                time.sleep(duration)
                feedback = f"Agent waited for {duration} seconds."
            elif action_type == "task_complete":
                self.logger.info("Task reported as complete by LLM.")
                feedback = "Task completed successfully."
                self.agent_state["status"] = "completed"
            else: # Removed the duplicate 'capture_screen' block here
                feedback = f"Unknown action: {action_type}. Please refine the LLM's output."
                self.logger.error(feedback)
        except Exception as e:
            feedback = f"Error executing action {action_type}: {e}"
            print(f"Error during action execution: {e}")
            self.logger.error(f"Error during action execution: {e}", exc_info=True)

        self.agent_state["last_action_feedback"] = feedback
        self.knowledge_base.store_agent_state(self.agent_state) # Save state after each action
        return feedback

    def run_agent(self, initial_task: str):
        """The main agentic loop."""
        self.agent_state["current_task"] = initial_task
        print(f"\n--- Starting Agent ---")
        print(f"Initial Task: {initial_task}")

        MAX_PARSE_RETRIES = 3
        parse_failures = 0

        while True:
            # 1. Perception/Observation
            # Capture screen for visual context (optional, based on need)
            screenshot_path = "current_screen.png"
            screen_image_bytes = self.screen_capture.capture_screen_bytes(screenshot_path) # Capture as bytes

            # Gather feedback
            latest_feedback = self.feedback_handler.get_latest_feedback()
            if latest_feedback:
                print(f"\nReceived user feedback: {latest_feedback}")
                self.agent_state = self.feedback_handler.process_feedback(self.agent_state, latest_feedback)

            # Construct LLM Prompt
            full_llm_prompt = self.global_prompt_manager.get_full_prompt(
                current_task_description=self.agent_state["current_task"],
                last_action_feedback=self.agent_state.get('last_action_feedback', 'None'),
                last_read_content=self.agent_state.get('last_read_content'),
                last_directory_list=self.agent_state.get('last_directory_list'),
                last_retrieved_knowledge=self.agent_state.get('last_retrieved_knowledge')
            )

            # 2. Reasoning (LLM Call)
            print("\n--- Agent Thinking ---")
            llm_response_text = self._call_llm(full_llm_prompt, image_data=screen_image_bytes)
            parsed_action = self._parse_llm_response(llm_response_text)

            if parsed_action.get("action") == "unknown":
                parse_failures += 1
                self.logger.warning(f"LLM output parsing failed ({parse_failures}/{MAX_PARSE_RETRIES}): {parsed_action.get('error')}. Raw LLM: {llm_response_text}")
                if parse_failures >= MAX_PARSE_RETRIES:
                    self.logger.error("Too many LLM output parsing failures. Agent cannot proceed. Exiting.")
                    print("\n--- AGENT HALTED: Unable to parse LLM instructions. ---")
                    print("Please check agent.log for details on LLM output and parsing errors.")
                    break # Exit the loop
                else:
                    self.logger.info("Retrying LLM call with enhanced context about parsing failure.")
                    self.agent_state["last_action_feedback"] = f"Previous LLM response parsing failed: {parsed_action.get('error', 'Unknown error')}. Please ensure your response is ONLY a single, valid JSON object with an 'action' key."
                    continue # Skip action execution, re-prompt LLM

            parse_failures = 0 # Reset counter on successful parse

            # 3. Action
            print(f"\n--- Agent Acting: {parsed_action['action']} ---")
            action_result_feedback = self._execute_action(parsed_action)
            print(f"Action Result: {action_result_feedback}")

            if self.agent_state["status"] == "completed":
                print("\n--- Agent finished its task. ---")
                break

            # Small delay to prevent rapid-fire actions and allow observation
            time.sleep(1)

# Example Usage (requires an LLM client setup, e.g., using Google Gemini)
if __name__ == "__main__":
    # Placeholder for your actual LLM client setup
    # from google.generativeai import GenerativeModel # pip install google-generativeai
    # gemini_llm_client = GenerativeModel('gemini-pro') # For text only
    # For multimodal: gemini_llm_client = GenerativeModel('gemini-pro-vision')

    agent = AgentCore(llm_client=None) # Pass your actual LLM client here
    # Example task: "Find the price of 'Python for Dummies' on Amazon."
    agent.run_agent("List the files in the current directory, then create a new file named 'ai_notes.txt' with content 'My first AI note.'")