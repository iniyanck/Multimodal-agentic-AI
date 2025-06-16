"""
ActionExecutor class for executing actions decided by the LLM.
"""
import time
import os
import base64
from ..utils.file_search import find_video_files_by_keyword_recursive
from ..utils.window_utils import list_open_windows, is_window_open, list_processes, is_process_running

class ActionExecutor:
    # Define allowed actions
    ALLOWED_ACTIONS = {
        "read_file",
        "write_file",
        "execute_shell_command",
        "focus_window",
        "list_directory",
        "capture_screen",
        "move_mouse",
        "wait",
        "task_complete",
        "type_text",
        "press_key",
        "hotkey",
        "click",
        "ask_user",
        "web_search"  # <-- Add web_search
    }

    def __init__(self, file_io, screen_capture, system_interaction, logger, agent_state):
        self.file_io = file_io
        self.screen_capture = screen_capture
        self.system_interaction = system_interaction
        self.logger = logger
        self.agent_state = agent_state
        try:
            from ..action.web_search import web_search as web_search_tool
            self.web_search_tool = web_search_tool
        except ImportError:
            self.web_search_tool = None

    def execute_action(self, parsed_action: dict) -> dict:
        action_type = parsed_action.get("action", "").strip().lower()
        if action_type not in self.ALLOWED_ACTIONS:
            self.logger.warning(f"Action '{action_type}' is not in the allowed set: {self.ALLOWED_ACTIONS}")
            return {
                "status": "failure",
                "message": f"Action '{action_type}' is not allowed. Allowed actions: {sorted(self.ALLOWED_ACTIONS)}",
                "details": {}
            }
        self.logger.info(f"Executing action type: {action_type}")
        feedback = {"status": "success", "message": "Action executed successfully.", "details": {}}
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
                if command and ("play" in self.agent_state["current_task"].lower() or "video" in self.agent_state["current_task"].lower()):
                    import re
                    user_keywords = re.findall(r"[\w-]+", self.agent_state["current_task"])
                    video_dir = os.path.expanduser(parsed_action.get("cwd", os.path.expanduser("~")))
                    if "videos" in video_dir.lower() or os.path.exists(os.path.join(os.path.expanduser("~"), "Videos")):
                        video_dir = os.path.join(os.path.expanduser("~"), "Videos")
                    for keyword in user_keywords:
                        matches = find_video_files_by_keyword_recursive(video_dir, keyword)
                        if matches:
                            command = f'start "" "{os.path.join(video_dir, matches[0])}"'
                            feedback["details"]["matched_file"] = matches[0]
                            break
                background = parsed_action.get("background", False)
                if command:
                    return_code, stdout, stderr = self.system_interaction.execute_shell_command(command, background=background)
                    feedback["details"]["command"] = command
                    feedback["details"]["background"] = background
                    feedback["details"]["return_code"] = return_code
                    feedback["details"]["stdout"] = stdout.strip() if isinstance(stdout, str) else stdout
                    feedback["details"]["stderr"] = stderr.strip() if isinstance(stderr, str) else stderr
                    # Add generic process/window info
                    feedback["details"]["open_windows"] = list_open_windows()
                    feedback["details"]["processes"] = list_processes()
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
                    feedback["details"]["open_windows"] = list_open_windows()
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
            elif action_type == "wait":
                duration = parsed_action.get("duration", 1)
                try:
                    duration = float(duration)
                except Exception:
                    duration = 1
                self.logger.info(f"Waiting for {duration} seconds as requested by LLM.")
                time.sleep(duration)
                feedback["message"] = f"Waited for {duration} seconds."
                feedback["details"]["duration"] = duration
            elif action_type == "task_complete":
                self.agent_state["status"] = "completed"
                feedback["message"] = "Task marked as complete."
            elif action_type == "type_text":
                text = parsed_action.get("text", "")
                interval = float(parsed_action.get("interval", 0.05))
                self.system_interaction.type_text(text, interval=interval)
                feedback["details"]["text_typed_preview"] = text[:50] + "..."
                feedback["details"]["open_windows"] = list_open_windows()
            elif action_type == "press_key":
                key = parsed_action.get("key", "")
                self.system_interaction.press_key(key)
                feedback["details"]["key"] = key
            elif action_type == "hotkey":
                keys = parsed_action.get("keys", "").split('+')
                self.system_interaction.hotkey(*keys)
                feedback["details"]["keys"] = keys
            elif action_type == "click":
                x = parsed_action.get("x")
                y = parsed_action.get("y")
                button = parsed_action.get("button", "left")
                if x is not None and y is not None:
                    self.system_interaction.click(int(x), int(y), button)
                else:
                    self.system_interaction.click(button=button)
                feedback["details"]["coordinates"] = {"x": x, "y": y}
                feedback["details"]["button"] = button
            elif action_type == "ask_user":
                question = parsed_action.get("question", "")
                self.logger.info(f"Agent asks user: {question}")
                self.agent_state["pending_user_question"] = question
                feedback["details"]["question"] = question
                feedback["message"] = f"User input requested: {question}"
                feedback["status"] = "pending_user_input"
            elif action_type == "web_search":
                query = parsed_action.get("query")
                num_results = int(parsed_action.get("num_results", 3))
                if self.web_search_tool and query:
                    result = self.web_search_tool(query, num_results)
                    feedback["details"]["query"] = query
                    feedback["details"]["num_results"] = num_results
                    feedback["details"]["result"] = result[:500] + ("..." if len(result) > 500 else "")
                    feedback["message"] = f"Web search completed for query: {query}"
                else:
                    feedback["status"] = "failure"
                    feedback["message"] = "web_search action missing 'query' parameter or tool not available."
            else:
                self.logger.warning(f"Unknown action type encountered: {action_type}")
                feedback["status"] = "failure"
                feedback["message"] = f"Unknown action type: {action_type}"
        except Exception as e:
            feedback["status"] = "failure"
            feedback["message"] = f"Exception during action execution: {e}"
            self.logger.error(feedback["message"], exc_info=True)
        return feedback
