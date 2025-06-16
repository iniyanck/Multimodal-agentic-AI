"""
AgentCore class: main orchestrator for agent perception, memory, planning, and action.
"""
from ..perception.file_io import FileIO
from ..perception.screen_capture import ScreenCapture
from ..action.system_interaction import SystemInteraction
from ..action.feedback_handler import FeedbackHandler
from ..memory.knowledge_base import KnowledgeBase
from ..core.global_prompt import GlobalPrompt
from ..utils.platform_utils import is_windows, is_mac, is_linux, get_platform_name
from ..utils.path_utils import resolve_special_folder
from ..utils.file_search import find_video_files_by_keyword, find_video_files_by_keyword_recursive
from .llm_interface import LLMInterface
from .action_executor import ActionExecutor
import time
import json
import io
import base64
from PIL import Image
from ..utils.logger import Logger
from ..action.web_search import web_search
import os
import datetime

class AgentCore:
    """Main orchestrator for agent perception, memory, planning, and action."""
    llm_call_count = 0
    llm_call_timestamps = []

    def __init__(self, llm_client=None):
        self.file_io = FileIO()
        self.screen_capture = ScreenCapture()
        self.system_interaction = SystemInteraction()
        self.feedback_handler = FeedbackHandler()
        self.knowledge_base = KnowledgeBase()
        self.global_prompt_manager = GlobalPrompt()
        self.llm_client = llm_client
        self.agent_state = self.knowledge_base.load_agent_state() or {
            "status": "idle",
            "current_task": "None",
            "history": [],
            "current_plan": [],
            "plan_step": 0
        }
        self.logger = Logger()
        self.last_screenshot_pil = None
        self.stop_flag = False  # Add stop flag
        self.interactive = True  # Add interactive flag
        self.failed_steps = {}
        self.successful_steps = set()
        self.llm_call_count = 0
        self.llm_call_timestamps = []

        self.llm_interface = LLMInterface(self.llm_client, self.logger)
        self.action_executor = ActionExecutor(self.file_io, self.screen_capture, self.system_interaction, self.logger, self.agent_state)

    def call_llm(self, prompt: str, image_data: bytes | None = None) -> str:
        """Calls the Large Language Model (LLM) with a prompt and optional image data."""
        return self.llm_interface.call_llm(prompt, image_data)

    def parse_llm_response(self, response: str) -> dict:
        """Parses the LLM's response, extracting a JSON object for action or plan."""
        return self.llm_interface.parse_llm_response(response)

    def execute_action(self, parsed_action: dict) -> dict:
        """Executes the action decided by the LLM and returns structured feedback."""
        return self.action_executor.execute_action(parsed_action)

    def _get_available_tools_description(self) -> str:
        """Generates a string describing the available tools for the LLM, with platform notes and usage examples."""
        platform_note = f"(Current platform: {get_platform_name()})"
        tools_description = f"""
Available Tools and their usage {platform_note} (output ONLY a JSON object with 'action' and parameters):

- read_file(file: str): Reads the content of a specified file.
  Example: {{"action": "read_file", "file": "README.md"}}
- write_file(file: str, content: str): Writes content to a specified file.
  Example: {{"action": "write_file", "file": "output.txt", "content": "Hello!"}}
- execute_shell_command(command: str, background: bool = False): Executes a shell command. If launching a GUI app, set background=true. Example: {{"action": "execute_shell_command", "command": "notepad", "background": true}}
- focus_window(title_substring: str): Focuses a window whose title contains the given substring. (Windows only)
  Example: {{"action": "focus_window", "title_substring": "Notepad"}}
- list_directory(path: str = "."): Lists the contents of a directory.
  Example: {{"action": "list_directory", "path": "."}}
- capture_screen(file: str): Captures the current screen and saves it. Use this to get visual context.
  Example: {{"action": "capture_screen", "file": "screen.png"}}
- move_mouse(x: int, y: int): Moves the mouse to absolute screen coordinates.
  Example: {{"action": "move_mouse", "x": 100, "y": 200}}
- click(x: int = -1, y: int = -1, button: str = "left"): Clicks at a specified position or current position.
  Example: {{"action": "click", "x": 100, "y": 200, "button": "left"}}
- type_text(text: str): Types the given text.
  Example: {{"action": "type_text", "text": "Hello world!"}}
- press_key(key: str): Presses a single keyboard key.
  Example: {{"action": "press_key", "key": "enter"}}
- hotkey(keys: str): Presses a combination of keys (e.g., "ctrl+c").
  Example: {{"action": "hotkey", "keys": "ctrl+c"}}
- store_knowledge(key: str, value: str): Stores information in the agent's knowledge base.
  Example: {{"action": "store_knowledge", "key": "last_app", "value": "notepad"}}
- retrieve_knowledge(key: str): Retrieves information from the agent's knowledge base.
  Example: {{"action": "retrieve_knowledge", "key": "last_app"}}
- ask_user(question: str): Asks the user a question and waits for a response.
  Example: {{"action": "ask_user", "question": "What should I do next?"}}
- wait(duration: int): Pauses agent execution for a specified number of seconds.
  Example: {{"action": "wait", "duration": 3}}
- decompose_subtask(subtask_description: str): If a step is too complex, break it down into a new plan and execute recursively.
  Example: {{"action": "decompose_subtask", "subtask_description": "Draw a circle in Paint"}}
- task_complete: Indicates that the current overall task is finished.
  Example: {{"action": "task_complete"}}
- resolve_special_folder(folder_name: str): Resolves the absolute path of a special folder (like 'videos', 'documents', 'desktop', etc.) in a platform-agnostic way. Use this to get the correct path for any user folder.
  Example: {{"action": "resolve_special_folder", "folder_name": "videos"}}
- web_search(query: str, num_results: int = 3): Performs a web search and returns a summary of the top results.
  Example: {{"action": "web_search", "query": "latest AI news", "num_results": 2}}
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
        llm_response = self.call_llm(planning_prompt)
        parsed_response = self.parse_llm_response(llm_response)

        if "plan" in parsed_response and isinstance(parsed_response["plan"], list):
            self.logger.info(f"Generated plan: {parsed_response['plan']}")
            return parsed_response["plan"]
        else:
            self.logger.error(f"LLM failed to generate a valid plan: {parsed_response.get('error', llm_response)}")
            self.logger.error(f"Raw LLM response: {llm_response}")
            self.logger.error(f"Planning prompt was: {planning_prompt}")
            self.agent_state["status"] = "idle"  # Set to idle so user can retry
            return [] # Return empty plan if invalid

    def _execute_subplan(self, subtask_description: str, parent_context: str = "") -> bool:
        """Recursively plan and execute a subtask. Returns True if successful."""
        print(f"\n--- Decomposing subtask: {subtask_description} ---")
        subplan = self._plan_task(subtask_description, parent_context)
        if not subplan:
            self.logger.error(f"Failed to generate subplan for subtask: {subtask_description}")
            return False
        for step in subplan:
            print(f"\n[Subtask] Executing: {step.get('description', step.get('action'))}")
            parsed_action = step
            if parsed_action.get('action') == 'decompose_subtask':
                # Recursively decompose further
                nested_desc = parsed_action.get('subtask_description', 'No description provided')
                if not self._execute_subplan(nested_desc, parent_context):
                    return False
            else:
                feedback = self.execute_action(parsed_action)
                if feedback.get('status') != 'success':
                    print(f"[Subtask] Step failed: {feedback.get('message')}")
                    return False
        print(f"--- Subtask '{subtask_description}' completed ---")
        return True

    def run_agent(self, initial_task: str):
        """The main agentic loop with planning and execution, now with recursive subtask decomposition and step/iteration limits."""
        self.agent_state["current_task"] = initial_task
        self.agent_state["status"] = "planning" # Initial status
        print(f"\n--- Starting Agent ---")
        print(f"Initial Task: {initial_task}")
        # --- Always capture a screenshot at the start of every task ---
        screenshot_path = os.path.join(os.path.dirname(__file__), '..', 'logs', 'screens', 'current_screen_step.png')
        self.screen_capture.capture_screen_bytes(screenshot_path)

        MAX_TOTAL_STEPS = 50
        total_steps = 0
        MAX_PLANNING_CYCLES = 3  # New: maximum times to re-plan for the same task
        planning_cycles = 0

        MAX_PARSE_RETRIES = 3
        parse_failures = 0

        MAX_ACTION_EXECUTION_RETRIES = 2 # Max retries for a single action within a plan step
        action_execution_retries = 0

        MAX_STEP_FAILURES = 3  # New: max failures per plan step

        while True:
            if self.stop_flag:
                print("\n--- Agent stopped by kill/reset ---")
                self.agent_state["status"] = "aborted"
                break

            if total_steps >= MAX_TOTAL_STEPS:
                print("\n--- Maximum step limit reached. Stopping agent to prevent runaway execution. ---")
                self.logger.warning("Maximum step limit reached. Stopping agent.")
                break

            if self.agent_state["status"] == "planning":
                if self.stop_flag:
                    self.agent_state["status"] = "aborted"
                    break
                if planning_cycles >= MAX_PLANNING_CYCLES:
                    print("\n--- Maximum planning cycles reached. Aborting task to prevent infinite loop. ---")
                    self.logger.error("Maximum planning cycles reached. Aborting task.")
                    self.agent_state["status"] = "aborted"
                    break
                planning_cycles += 1
                print("\n--- Agent Planning ---")
                current_context = self.global_prompt_manager.get_current_context(self.agent_state)
                self.agent_state["current_plan"] = self._plan_task(self.agent_state["current_task"], current_context)
                self.agent_state["plan_step"] = 0
                action_execution_retries = 0 # Reset retries for new plan
                total_steps += 1

                if not self.agent_state["current_plan"]:
                    self.logger.error("Failed to generate a plan. Halting agent.")
                    print("\n--- AGENT HALTED: Unable to generate a plan. ---")
                    break
                else:
                    self.agent_state["status"] = "executing_plan"
                    print(f"Agent has a plan with {len(self.agent_state['current_plan'])} steps.")

            elif self.agent_state["status"] == "executing_plan":
                if self.stop_flag:
                    self.agent_state["status"] = "aborted"
                    break
                if self.agent_state["plan_step"] >= len(self.agent_state["current_plan"]):
                    print("\n--- All steps in the current plan executed. Agent considering next steps or task completion. ---")
                    self.agent_state["status"] = "planning"
                    continue
                current_step = self.agent_state["current_plan"][self.agent_state["plan_step"]]
                step_signature = json.dumps(current_step, sort_keys=True)

                # Removed user confirmation for risky actions; proceed automatically

                # 1. Perception/Observation for this step
                screenshot_path = os.path.join(os.path.dirname(__file__), '..', 'logs', 'screens', 'current_screen_step.png')
                screen_image_bytes = self.screen_capture.capture_screen_bytes(screenshot_path)

                if self.stop_flag:
                    self.agent_state["status"] = "aborted"
                    break

                # Gather user feedback
                latest_feedback = self.feedback_handler.get_latest_feedback()
                if latest_feedback:
                    print(f"\nReceived user feedback: {latest_feedback}")
                    self.agent_state = self.feedback_handler.process_feedback(self.agent_state, latest_feedback)

                # Construct LLM Prompt for action execution (now it's more about refining the current step)
                last_action_feedback_str = json.dumps(self.agent_state.get('last_action_feedback', {"status": "none", "message": "No previous action feedback."}))

                llm_response_text = self.call_llm(
                    self.global_prompt_manager.get_action_execution_prompt(
                        current_task_description=self.agent_state["current_task"],
                        current_plan_step=current_step,
                        last_action_feedback=last_action_feedback_str,
                        last_read_content=self.agent_state.get('last_read_content'),
                        last_directory_list=self.agent_state.get('last_directory_list'),
                        last_retrieved_knowledge=self.agent_state.get('last_retrieved_knowledge'),
                        history=self.agent_state["history"][-5:],
                        failed_steps_summary=self.failed_steps,
                        successful_steps_summary=list(self.successful_steps)
                    ),
                    image_data=screen_image_bytes
                )
                parsed_action = self.parse_llm_response(llm_response_text)

                if self.stop_flag:
                    self.agent_state["status"] = "aborted"
                    break

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
                action_result_feedback = self.execute_action(parsed_action) # This now returns a dict
                print(f"Action Result: {action_result_feedback['status'].upper()} - {action_result_feedback['message']}")

                if self.stop_flag:
                    self.agent_state["status"] = "aborted"
                    break

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
                reflection_llm_response = self.call_llm(reflection_prompt, image_data=screen_image_bytes) # Pass screenshot again for reflection
                reflection_parsed = self.parse_llm_response(reflection_llm_response)

                if self.stop_flag:
                    self.agent_state["status"] = "aborted"
                    break

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
                self.self_evaluate_task()  # Automated self-evaluation after task completion
                # self.agent_state["status"] = "idle"  # Remove this line
                break

            # Small delay to prevent rapid-fire actions and allow observation
            time.sleep(1)

            if self.stop_flag:
                self.agent_state["status"] = "aborted"
                break

    def self_evaluate_task(self):
        """Prompts the LLM to critique the agent's overall performance after task completion."""
        evaluation_prompt = self.global_prompt_manager.get_self_evaluation_prompt(
            current_task=self.agent_state["current_task"],
            history=self.agent_state["history"],
            final_state=self.agent_state
        )
        self.logger.info("Agent performing self-evaluation of completed task.")
        llm_response = self.call_llm(evaluation_prompt)
        try:
            evaluation = json.loads(llm_response)
        except Exception:
            evaluation = {"raw_response": llm_response}
        self.logger.info(f"Self-evaluation: {evaluation}")
        # Store in knowledge base for future reference
        self.knowledge_base.store_knowledge(
            key=f"self_evaluation_{int(time.time())}",
            value=json.dumps(evaluation)
        )
        print(f"\n--- Agent Self-Evaluation ---\n{evaluation}\n")

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