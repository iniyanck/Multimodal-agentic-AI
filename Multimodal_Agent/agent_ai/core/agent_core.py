# agent_ai/core/agent_core.py

from ..perception.file_io import FileIO
from ..perception.screen_capture import ScreenCapture
from ..action.system_interaction import SystemInteraction
from ..action.feedback_handler import FeedbackHandler
from ..memory.knowledge_base import KnowledgeBase
from ..core.global_prompt import GlobalPrompt
from ..utils.platform_utils import is_windows, is_mac, is_linux, get_platform_name
import time
import json
import io
import base64
from PIL import Image # Import PIL for image handling
from ..utils.logger import Logger

class AgentCore:
    def __init__(self, llm_client=None):
        """Initializes the core agent with all subsystems and state."""
        self.file_io = FileIO()
        self.screen_capture = ScreenCapture()
        self.system_interaction = SystemInteraction()
        self.feedback_handler = FeedbackHandler()
        self.knowledge_base = KnowledgeBase()
        self.global_prompt_manager = GlobalPrompt()
        self.llm_client = llm_client
        self.agent_state = self.knowledge_base.load_agent_state() or {"status": "idle", "current_task": "None", "history": [], "current_plan": [], "plan_step": 0}
        self.logger = Logger()
        self.last_screenshot_pil = None

    def _call_llm(self, prompt: str, image_data: bytes | None = None) -> str:
        """Calls the Large Language Model (LLM) with a prompt and optional image data."""
        if self.llm_client is None:
            self.logger.error("LLM client is not configured. Cannot make API call.")
            return json.dumps({"action": "unknown", "error": "LLM not configured"})

        try:
            contents = [prompt]
            if image_data:
                try:
                    pil_image = Image.open(io.BytesIO(image_data))
                    contents.append(pil_image)
                    self.last_screenshot_pil = pil_image
                except Exception as img_e:
                    self.logger.error(f"Error converting image data to PIL Image: {img_e}")

            self.logger.info(f"Sending prompt to LLM (first 500 chars): {prompt[:500]}...")
            if image_data:
                self.logger.info("Image data included in LLM call.")

            response = self.llm_client.generate_content(
                contents=contents,
                generation_config={"temperature": 0.7}
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
        """Parses the LLM's response, extracting a JSON object for action or plan."""
        try:
            # Find the first occurrence of '{' and the last occurrence of '}'
            start_idx = response.find('{')
            end_idx = response.rfind('}')

            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                json_string = response[start_idx : end_idx + 1]
                parsed_data = json.loads(json_string)

                if "action" not in parsed_data and "plan" not in parsed_data and "status" not in parsed_data: # Modified for planning and reflection
                    self.logger.error(f"Parsed JSON missing 'action', 'plan', or 'status' key: {parsed_data}")
                    return {"action": "unknown", "error": "Parsed JSON missing required key ('action', 'plan', or 'status')"}

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

    def _get_available_tools_description(self) -> str:
        """Generates a string describing the available tools for the LLM, with platform notes."""
        platform_note = f"(Current platform: {get_platform_name()})"
        tools_description = f"""
Available Tools and their usage {platform_note} (output ONLY a JSON object with 'action' and parameters):
- read_file(file: str): Reads the content of a specified file.
- write_file(file: str, content: str): Writes content to a specified file.
- execute_shell_command(command: str, background: bool = False): Executes a shell command. If background=True, runs non-blocking and returns immediately. (Platform-aware)
- focus_window(title_substring: str): Focuses a window whose title contains the given substring. (Windows only)
- list_directory(path: str = "."): Lists the contents of a directory.
- capture_screen(file: str): Captures the current screen and saves it. Use this to get visual context.
- move_mouse(x: int, y: int): Moves the mouse to absolute screen coordinates.
- click(x: int = -1, y: int = -1, button: str = "left"): Clicks at a specified position or current position.
- type_text(text: str): Types the given text.
- press_key(key: str): Presses a single keyboard key.
- hotkey(keys: str): Presses a combination of keys (e.g., "ctrl+c").
- store_knowledge(key: str, value: str): Stores information in the agent's knowledge base.
- retrieve_knowledge(key: str): Retrieves information from the agent's knowledge base.
- ask_user(question: str): Asks the user a question and waits for a response.
- wait(duration: int): Pauses agent execution for a specified number of seconds.
- task_complete: Indicates that the current overall task is finished.
"""
        return tools_description

    def _plan_task(self, task_description: str, current_context: str) -> list[dict]:
        """Uses the LLM to generate a plan (a sequence of actions) to achieve the task."""
        planning_prompt = self.global_prompt_manager.get_planning_prompt(
            task_description=task_description,
            current_context=current_context,
            tools_description=self._get_available_tools_description(),
            history=self.agent_state["history"] # Provide history for better planning
        )
        self.logger.info("Agent is generating a plan...")
        llm_response = self._call_llm(planning_prompt)
        parsed_response = self._parse_llm_response(llm_response)

        if "plan" in parsed_response and isinstance(parsed_response["plan"], list):
            self.logger.info(f"Generated plan: {parsed_response['plan']}")
            return parsed_response["plan"]
        else:
            self.logger.error(f"LLM failed to generate a valid plan: {parsed_response.get('error', llm_response)}")
            return [] # Return empty plan if invalid

    def _execute_action(self, parsed_action: dict) -> dict:
        """Executes the action decided by the LLM and returns structured feedback."""
        action_type = parsed_action.get("action")
        feedback = {"status": "success", "message": "Action executed successfully.", "details": {}}

        # Add a record to history for debugging and future context
        action_entry = {"timestamp": time.time(), "action": parsed_action}
        self.agent_state["history"].append(action_entry)

        try:
            if action_type == "read_file":
                filename = parsed_action.get("file")
                content = self.file_io.read_file(filename)
                self.agent_state["last_read_content"] = content
                feedback["details"]["filename"] = filename
                feedback["details"]["content_preview"] = content[:200] + "..." if content else "No content"
                if not content:
                    feedback["status"] = "failure"
                    feedback["message"] = f"File read failed or file is empty for {filename}."
            elif action_type == "write_file":
                filename = parsed_action.get("file")
                content = parsed_action.get("content")
                if self.file_io.write_file(filename, content):
                    feedback["details"]["filename"] = filename
                    feedback["details"]["content_written_preview"] = content[:100] + "..."
                else:
                    feedback["status"] = "failure"
                    feedback["message"] = f"Failed to write to {filename}."
            elif action_type == "execute_shell_command":
                command = parsed_action.get("command")
                background = parsed_action.get("background", False)
                if command:
                    return_code, stdout, stderr = self.system_interaction.execute_shell_command(command, background=background)
                    feedback["details"]["command"] = command
                    feedback["details"]["background"] = background
                    feedback["details"]["return_code"] = return_code
                    feedback["details"]["stdout"] = stdout.strip() if isinstance(stdout, str) else stdout
                    feedback["details"]["stderr"] = stderr.strip() if isinstance(stderr, str) else stderr
                    if return_code == 0:
                        feedback["message"] = f"Command '{command}' executed successfully." if not background else f"Command '{command}' started in background."
                    else:
                        feedback["status"] = "failure"
                        feedback["message"] = f"Command '{command}' failed (Exit Code: {return_code})."
                else:
                    feedback["status"] = "failure"
                    feedback["message"] = "execute_shell_command action missing 'command' parameter."
                    self.logger.warning(feedback["message"])
            elif action_type == "focus_window":
                title_substring = parsed_action.get("title_substring")
                if title_substring:
                    success = self.system_interaction.focus_window(title_substring)
                    feedback["details"]["title_substring"] = title_substring
                    feedback["details"]["focused"] = success
                    if success:
                        feedback["message"] = f"Focused window with title containing '{title_substring}'."
                    else:
                        feedback["status"] = "failure"
                        feedback["message"] = f"Could not find or focus window with title containing '{title_substring}'."
                else:
                    feedback["status"] = "failure"
                    feedback["message"] = "focus_window action missing 'title_substring' parameter."
                    self.logger.warning(feedback["message"])
            elif action_type == "list_directory":
                path = parsed_action.get("path", ".")
                contents = self.file_io.list_directory(path)
                self.agent_state["last_directory_list"] = contents
                feedback["details"]["path"] = path
                feedback["details"]["contents"] = contents
                if contents is None:
                    feedback["status"] = "failure"
                    feedback["message"] = "Directory listing failed."
            elif action_type == "capture_screen":
                filename = parsed_action.get("file")
                screenshot_bytes = self.screen_capture.capture_screen_bytes(filename)
                if screenshot_bytes:
                    self.agent_state["last_screenshot_bytes"] = base64.b64encode(screenshot_bytes).decode('utf-8')
                    feedback["details"]["filename"] = filename
                else:
                    feedback["status"] = "failure"
                    feedback["message"] = "Screen capture failed."
            elif action_type == "move_mouse":
                x = int(parsed_action.get("x", 0))
                y = int(parsed_action.get("y", 0))
                self.system_interaction.move_mouse(x, y)
                feedback["details"]["coordinates"] = {"x": x, "y": y}
            elif action_type == "click":
                x = int(parsed_action.get("x", -1))
                y = int(parsed_action.get("y", -1))
                button = parsed_action.get("button", "left")
                if x != -1 and y != -1:
                    self.system_interaction.click(x, y, button)
                else:
                    self.system_interaction.click(button=button)
                feedback["details"]["coordinates"] = {"x": x, "y": y}
                feedback["details"]["button"] = button
            elif action_type == "type_text":
                text = parsed_action.get("text")
                self.system_interaction.type_text(text)
                feedback["details"]["text_typed_preview"] = text[:50] + "..."
            elif action_type == "press_key":
                key = parsed_action.get("key")
                self.system_interaction.press_key(key)
                feedback["details"]["key"] = key
            elif action_type == "hotkey":
                keys = parsed_action.get("keys", "").split('+')
                self.system_interaction.hotkey(*keys)
                feedback["details"]["keys"] = keys
            elif action_type == "store_knowledge":
                key = parsed_action.get("key")
                value = parsed_action.get("value")
                if self.knowledge_base.store_knowledge(key, value):
                    feedback["details"]["key"] = key
                else:
                    feedback["status"] = "failure"
                    feedback["message"] = f"Failed to store knowledge '{key}'."
            elif action_type == "retrieve_knowledge":
                key = parsed_action.get("key")
                value = self.knowledge_base.retrieve_knowledge(key)
                self.agent_state["last_retrieved_knowledge"] = value
                feedback["details"]["key"] = key
                feedback["details"]["value"] = value
                if not value:
                    feedback["message"] = f"No knowledge for '{key}'." # Not necessarily a failure
            elif action_type == "ask_user":
                question = parsed_action.get("question")
                print(f"\nAGENT ASKS: {question}")
                user_response = input("Your response: ")
                self.feedback_handler.receive_feedback(user_response)
                feedback["details"]["question"] = question
                feedback["details"]["user_response"] = user_response
                feedback["message"] = f"User responded to question."
            elif action_type == "wait":
                duration = int(parsed_action.get("duration", 1))
                print(f"Agent waiting for {duration} seconds...")
                self.logger.info(f"Agent waiting for {duration} seconds...")
                time.sleep(duration)
                feedback["details"]["duration"] = duration
            elif action_type == "task_complete":
                self.logger.info("Task reported as complete by LLM.")
                feedback["message"] = "Task completed successfully."
                self.agent_state["status"] = "completed"
            else:
                feedback["status"] = "failure"
                feedback["message"] = f"Unknown action: {action_type}. Please refine the LLM's output."
                self.logger.error(feedback["message"])
        except Exception as e:
            feedback["status"] = "failure"
            feedback["message"] = f"Error executing action {action_type}: {e}"
            feedback["details"]["exception"] = str(e)
            print(f"Error during action execution: {e}")
            self.logger.error(f"Error during action execution: {e}", exc_info=True)

        self.agent_state["last_action_feedback"] = feedback # Store structured feedback
        self.knowledge_base.store_agent_state(self.agent_state)
        return feedback

    def run_agent(self, initial_task: str):
        """The main agentic loop with planning and execution."""
        self.agent_state["current_task"] = initial_task
        self.agent_state["status"] = "planning" # Initial status
        print(f"\n--- Starting Agent ---")
        print(f"Initial Task: {initial_task}")

        MAX_PARSE_RETRIES = 3
        parse_failures = 0

        MAX_ACTION_EXECUTION_RETRIES = 2 # Max retries for a single action within a plan step
        action_execution_retries = 0

        while True:
            if self.agent_state["status"] == "planning":
                print("\n--- Agent Planning ---")
                current_context = self.global_prompt_manager.get_current_context(self.agent_state)
                self.agent_state["current_plan"] = self._plan_task(self.agent_state["current_task"], current_context)
                self.agent_state["plan_step"] = 0
                action_execution_retries = 0 # Reset retries for new plan

                if not self.agent_state["current_plan"]:
                    self.logger.error("Failed to generate a plan. Halting agent.")
                    print("\n--- AGENT HALTED: Unable to generate a plan. ---")
                    break
                else:
                    self.agent_state["status"] = "executing_plan"
                    print(f"Agent has a plan with {len(self.agent_state['current_plan'])} steps.")

            elif self.agent_state["status"] == "executing_plan":
                if self.agent_state["plan_step"] >= len(self.agent_state["current_plan"]):
                    print("\n--- All steps in the current plan executed. Agent considering next steps or task completion. ---")
                    # If all steps completed, transition to planning to allow LLM to decide if task is truly complete
                    self.agent_state["status"] = "planning"
                    continue # Go back to the top of the loop for planning

                current_step = self.agent_state["current_plan"][self.agent_state["plan_step"]]
                print(f"\n--- Executing Plan Step {self.agent_state['plan_step'] + 1}/{len(self.agent_state['current_plan'])}: {current_step.get('description', current_step.get('action'))} ---")

                # 1. Perception/Observation for this step
                screenshot_path = "current_screen_step.png"
                screen_image_bytes = self.screen_capture.capture_screen_bytes(screenshot_path)

                # Gather user feedback
                latest_feedback = self.feedback_handler.get_latest_feedback()
                if latest_feedback:
                    print(f"\nReceived user feedback: {latest_feedback}")
                    self.agent_state = self.feedback_handler.process_feedback(self.agent_state, latest_feedback)
                    # If user feedback significantly changes context, might want to re-plan
                    # self.agent_state["status"] = "planning"
                    # continue

                # Construct LLM Prompt for action execution (now it's more about refining the current step)
                # Pass structured feedback to LLM
                last_action_feedback_str = json.dumps(self.agent_state.get('last_action_feedback', {"status": "none", "message": "No previous action feedback."}))

                action_prompt = self.global_prompt_manager.get_action_execution_prompt(
                    current_task_description=self.agent_state["current_task"],
                    current_plan_step=current_step,
                    last_action_feedback=last_action_feedback_str, # Pass structured feedback
                    last_read_content=self.agent_state.get('last_read_content'),
                    last_directory_list=self.agent_state.get('last_directory_list'),
                    last_retrieved_knowledge=self.agent_state.get('last_retrieved_knowledge'),
                    history=self.agent_state["history"]
                )

                # 2. Reasoning (LLM Call to get specific action parameters)
                llm_response_text = self._call_llm(action_prompt, image_data=screen_image_bytes)
                parsed_action = self._parse_llm_response(llm_response_text)

                if parsed_action.get("action") == "unknown":
                    parse_failures += 1
                    self.logger.warning(f"LLM output parsing failed ({parse_failures}/{MAX_PARSE_RETRIES}) for step {self.agent_state['plan_step']}: {parsed_action.get('error')}. Raw LLM: {llm_response_text}")
                    if parse_failures >= MAX_PARSE_RETRIES:
                        self.logger.error("Too many LLM output parsing failures for a plan step. Going back to planning.")
                        self.agent_state["status"] = "planning" # Go back to planning if current step cannot be parsed
                        parse_failures = 0 # Reset counter
                        action_execution_retries = 0 # Reset retries for new plan
                        continue
                    else:
                        # Provide explicit feedback to LLM about parsing failure for the next retry on this step
                        self.agent_state["last_action_feedback"] = {
                            "status": "failure",
                            "message": f"LLM response parsing failed. Expected ONLY a single JSON object for action parameters. Error: {parsed_action.get('error', 'Unknown error')}. Please output a valid JSON object matching the action schema for: {current_step.get('action')}."
                        }
                        continue # Skip action execution, re-prompt LLM for this step with feedback

                parse_failures = 0 # Reset counter on successful parse

                # 3. Action Execution
                print(f"\n--- Agent Acting (from plan): {parsed_action['action']} ---")
                action_result_feedback = self._execute_action(parsed_action) # This now returns a dict
                print(f"Action Result: {action_result_feedback['status'].upper()} - {action_result_feedback['message']}")

                # 4. Reflection and Confirmation (New Step)
                # After executing an action, prompt the LLM to reflect on its success
                reflection_prompt = self.global_prompt_manager.get_reflection_prompt(
                    current_task_description=self.agent_state["current_task"],
                    current_plan_step=current_step,
                    action_executed=parsed_action,
                    action_result=action_result_feedback, # Pass structured result
                    current_context=self.global_prompt_manager.get_current_context(self.agent_state), # Fresh context
                    history=self.agent_state["history"]
                )
                print("\n--- Agent Reflecting on Action Outcome ---")
                reflection_llm_response = self._call_llm(reflection_prompt, image_data=screen_image_bytes) # Pass screenshot again for reflection
                reflection_parsed = self._parse_llm_response(reflection_llm_response)

                action_successful_in_reflection = reflection_parsed.get("status") == "success"
                reflection_thought = reflection_parsed.get("thought", "No specific reflection thought provided.")

                print(f"Agent's Reflection: {reflection_thought}")

                if action_successful_in_reflection:
                    self.logger.info(f"LLM confirmed action success for plan step {self.agent_state['plan_step']}. Moving to next step.")
                    self.agent_state["plan_step"] += 1 # Move to next step if successful
                    action_execution_retries = 0 # Reset retries
                    self.agent_state["last_action_feedback"] = action_result_feedback # Update feedback for next prompt
                else:
                    action_execution_retries += 1
                    self.logger.warning(f"LLM indicated action failure or requested re-evaluation for step {self.agent_state['plan_step']}. Retries: {action_execution_retries}/{MAX_ACTION_EXECUTION_RETRIES}. LLM reason: {reflection_parsed.get('message', 'No message')}")
                    if action_execution_retries >= MAX_ACTION_EXECUTION_RETRIES:
                        self.logger.error(f"Too many action execution retries for plan step {self.agent_state['plan_step']}. Going back to planning to adjust strategy.")
                        self.agent_state["status"] = "planning" # Go back to planning if action repeatedly fails or LLM can't confirm
                        action_execution_retries = 0 # Reset retries
                        # Provide explicit feedback for re-planning
                        self.agent_state["last_action_feedback"] = {
                            "status": "failure",
                            "message": f"Action '{parsed_action.get('action')}' for plan step '{current_step.get('description', 'N/A')}' repeatedly failed or could not be confirmed. LLM said: {reflection_parsed.get('message', 'No specific reason.')}. Please adjust the plan."
                        }
                    else:
                        # If retrying, LLM needs to know the action failed and its reflection
                        self.agent_state["last_action_feedback"] = {
                            "status": "failure",
                            "message": f"Previous action '{parsed_action.get('action')}' failed (LLM reflection). Retrying step. LLM reason: {reflection_parsed.get('message', 'No specific reason.')}",
                            "details": action_result_feedback['details']
                        }
                        # Do not increment plan_step, remain on current step for retry

            if self.agent_state["status"] == "completed":
                print("\n--- Agent finished its task. ---")
                break

            # Small delay to prevent rapid-fire actions and allow observation
            time.sleep(1)

# Example Usage (requires an LLM client setup, e.g., using Google Gemini)
if __name__ == "__main__":
    # Placeholder for your actual LLM client setup
    # from google.generativeai import GenerativeModel # pip install google-generativeai
    # gemini_llm_client = GenerativeModel('gemini-pro-vision') # For multimodal

    class MockLLMClient: # Mock LLM client for demonstration
        def generate_content(self, contents, generation_config):
            prompt = contents[0]
            if "PLANNING_PROMPT" in prompt:
                print("Mock LLM: Planning phase...")
                # Example plan for the initial task
                return type('obj', (object,), {'text' : json.dumps({"plan": [
                    {"action": "list_directory", "description": "See what files are in the current directory."},
                    {"action": "write_file", "file": "ai_notes.txt", "content": "My first AI note.", "description": "Create the new file with content."},
                    {"action": "read_file", "file": "ai_notes.txt", "description": "Verify the file content."},
                    {"action": "task_complete", "description": "Task is done."}
                ]})})
            elif "ACTION_EXECUTION_PROMPT" in prompt:
                print("Mock LLM: Action execution phase...")
                if "list_directory" in prompt:
                    return type('obj', (object,), {'text' : json.dumps({"action": "list_directory", "path": "."})})
                elif "write_file" in prompt:
                    return type('obj', (object,), {'text' : json.dumps({"action": "write_file", "file": "ai_notes.txt", "content": "My first AI note."})})
                elif "read_file" in prompt:
                    return type('obj', (object,), {'text' : json.dumps({"action": "read_file", "file": "ai_notes.txt"})})
                elif "task_complete" in prompt:
                    return type('obj', (object,), {'text' : json.dumps({"action": "task_complete"})})
                else:
                    return type('obj', (object,), {'text' : json.dumps({"action": "unknown", "error": "Mock LLM didn't understand action."})})
            elif "REFLECTION_PROMPT" in prompt:
                print("Mock LLM: Reflection phase...")
                # Simulate success for all actions in this mock
                if '"status": "failure"' in prompt: # If previous action was reported as failure
                     # Simulate reflection recommending re-attempt or re-plan if needed
                    return type('obj', (object,), {'text' : json.dumps({
                        "status": "failure",
                        "thought": "The previous action failed. I will try to adjust my approach or re-attempt it.",
                        "message": "Action verification failed or adjustment needed."
                    })})
                else:
                    return type('obj', (object,), {'text' : json.dumps({
                        "status": "success",
                        "thought": "The action seems to have completed successfully. Moving to the next step.",
                        "message": "Action verified as successful."
                    })})
            else:
                return type('obj', (object,), {'text' : json.dumps({"action": "unknown", "error": "Mock LLM didn't understand prompt type."})})


    agent = AgentCore(llm_client=MockLLMClient()) # Pass your actual LLM client here
    # Example task adjusted to reflect the mock LLM's capabilities
    agent.run_agent("List the files in the current directory, then create a new file named 'ai_notes.txt' with content 'My first AI note.'. Finally, verify the file content and indicate task completion.")