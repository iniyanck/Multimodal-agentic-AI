"""
LLMInterface class for handling LLM calls and response parsing.
"""
import json
import io
import datetime
from PIL import Image

class LLMInterface:
    llm_call_count = 0
    llm_call_timestamps = []

    def __init__(self, llm_client, logger):
        self.llm_client = llm_client
        self.logger = logger
        self.last_screenshot_pil = None

    def call_llm(self, prompt: str, image_data: bytes | None = None) -> str:
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
            # --- LLM call diagnostics ---
            LLMInterface.llm_call_count += 1
            now = datetime.datetime.now()
            LLMInterface.llm_call_timestamps.append(now)
            self.logger.info(f"LLM CALL #{LLMInterface.llm_call_count} at {now.strftime('%Y-%m-%d %H:%M:%S')}")
            if len(LLMInterface.llm_call_timestamps) > 1:
                recent = LLMInterface.llm_call_timestamps[-5:]
                self.logger.info(f"Last 5 LLM call times: {[t.strftime('%H:%M:%S') for t in recent]}")
            # --- END diagnostics ---
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
            error_str = str(e)
            if any(keyword in error_str.lower() for keyword in ["quota", "rate limit", "429", "exceeded", "too many requests"]):
                self.logger.error(f"LLM quota/rate limit error: {e}", exc_info=True)
                return json.dumps({"action": "unknown", "error": f"LLM quota/rate limit error: {e}"})
            else:
                self.logger.error(f"Error calling LLM API: {e}", exc_info=True)
                return json.dumps({"action": "unknown", "error": f"LLM API error: {e}"})

    def parse_llm_response(self, response: str) -> dict:
        try:
            start_idx = response.find('{')
            end_idx = response.rfind('}')
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                json_string = response[start_idx : end_idx + 1]
                parsed_data = json.loads(json_string)
                # Fallback: If 'command' is present but 'action' is missing, infer 'action': 'execute_shell_command'
                if (
                    "action" not in parsed_data and
                    "plan" not in parsed_data and
                    "status" not in parsed_data and
                    "command" in parsed_data
                ):
                    self.logger.warning("LLM response missing 'action' but has 'command'. Inferring action as 'execute_shell_command'.")
                    parsed_data["action"] = "execute_shell_command"
                if "action" not in parsed_data and "plan" not in parsed_data and "status" not in parsed_data:
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
