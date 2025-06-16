import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import threading
from agent_ai.core.agent_core import AgentCore
import google.generativeai as genai
import logging

app = FastAPI()

# CORS middleware for frontend-backend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load API key from environment or .env
api_key = os.environ.get("GOOGLE_API_KEY")
if not api_key:
    raise RuntimeError("GOOGLE_API_KEY environment variable not set.")

genai.configure(api_key=api_key)
llm_client = genai.GenerativeModel('gemini-2.0-flash')
agent = AgentCore(llm_client=llm_client)
agent.interactive = False

# Models for request/response
class TaskRequest(BaseModel):
    task: str

class FeedbackRequest(BaseModel):
    feedback: str

class UserInputRequest(BaseModel):
    user_input: str

agent_thread = None
agent_lock = threading.Lock()

@app.post("/task")
def submit_task(req: TaskRequest):
    global agent_thread
    with agent_lock:
        logging.info(f"/task called with: {req.task}, current agent status: {agent.agent_state.get('status')}")
        if agent.agent_state.get("status") not in ["idle", "completed", "aborted"]:
            logging.warning("Task submission rejected: agent busy.")
            return JSONResponse(status_code=409, content={"error": "Agent is busy with another task."})
        agent.stop_flag = False  # Reset stop flag
        agent_thread = threading.Thread(target=agent.run_agent, args=(req.task,))
        agent_thread.start()
        logging.info("Agent thread started.")
    return {"status": "started", "task": req.task}

@app.get("/status")
def get_status():
    return agent.agent_state

@app.get("/logs")
def get_logs():
    log_path = os.path.join(os.path.dirname(__file__), "..", "agent_ai", "logs", "agent.log")
    try:
        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()[-100:]
        if not lines:
            return {"logs": ["Log file is empty."]}
        return {"logs": lines}
    except FileNotFoundError:
        return {"logs": ["Log file not found."]}
    except Exception as e:
        return {"logs": [f"Error reading log file: {e}"]}

@app.get("/screenshot")
def get_screenshot():
    screenshot_path = os.path.join(os.path.dirname(__file__), "..", "agent_ai", "logs", "screens", "current_screen_step.png")
    if not os.path.exists(screenshot_path):
        raise HTTPException(status_code=404, detail="Screenshot not found.")
    return FileResponse(screenshot_path)

@app.post("/feedback")
def send_feedback(req: FeedbackRequest):
    agent.feedback_handler.receive_feedback(req.feedback)
    return {"status": "received", "feedback": req.feedback}

@app.post("/user_input")
def set_user_input(req: UserInputRequest):
    user_input_path = os.path.join(os.path.dirname(__file__), "..", "user_input.txt")
    with open(user_input_path, "w", encoding="utf-8") as f:
        f.write(req.user_input.strip())
    # Also process feedback in real time
    agent.feedback_handler.receive_feedback(req.user_input.strip())
    return {"status": "written", "user_input": req.user_input}

@app.get("/user_input")
def get_user_input():
    user_input_path = os.path.join(os.path.dirname(__file__), "..", "user_input.txt")
    if not os.path.exists(user_input_path):
        return {"user_input": ""}
    with open(user_input_path, "r", encoding="utf-8") as f:
        content = f.read().strip()
    return {"user_input": content}

@app.post("/reset")
def reset_agent():
    global agent_thread
    if agent_thread and agent_thread.is_alive():
        agent.stop_flag = True
        agent_thread.join(timeout=2)
        if agent_thread.is_alive():
            agent.agent_state["status"] = "aborted"
        agent_thread = None
    agent.stop_flag = False  # Reset stop flag after stopping
    agent.agent_state = agent.knowledge_base.load_agent_state() or {
        "status": "idle",
        "current_task": "None",
        "history": [],
        "current_plan": [],
        "plan_step": 0
    }
    agent.agent_state["status"] = "idle"  # Ensure status is idle after reset
    return {"status": "reset"}

@app.post("/kill")
def kill_switch():
    global agent_thread
    if agent_thread and agent_thread.is_alive():
        agent.stop_flag = True
        agent_thread.join(timeout=2)
        if agent_thread.is_alive():
            agent.agent_state["status"] = "aborted"
        agent_thread = None
    agent.stop_flag = False  # Reset stop flag after stopping
    agent.agent_state = agent.knowledge_base.load_agent_state() or {
        "status": "idle",
        "current_task": "None",
        "history": [],
        "current_plan": [],
        "plan_step": 0
    }
    agent.agent_state["status"] = "idle"  # Ensure status is idle after kill
    # Clear logs
    log_path = os.path.join(os.path.dirname(__file__), "..", "agent_ai", "logs", "agent.log")
    try:
        with open(log_path, "w", encoding="utf-8") as f:
            f.write("")
    except Exception:
        pass
    # Remove screenshot
    screenshot_path = os.path.join(os.path.dirname(__file__), "..", "agent_ai", "logs", "screens", "current_screen_step.png")
    try:
        if os.path.exists(screenshot_path):
            os.remove(screenshot_path)
    except Exception:
        pass
    # Clear user_input.txt
    user_input_path = os.path.join(os.path.dirname(__file__), "..", "user_input.txt")
    try:
        with open(user_input_path, "w", encoding="utf-8") as f:
            f.write("")
    except Exception:
        pass
    return {"status": "killed"}

@app.post("/clear_logs")
def clear_logs():
    log_path = os.path.join(os.path.dirname(__file__), "..", "agent_ai", "logs", "agent.log")
    try:
        with open(log_path, "w", encoding="utf-8") as f:
            f.write("")
        return {"status": "logs_cleared"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Failed to clear logs: {e}"})

@app.on_event("shutdown")
def shutdown_event():
    global agent_thread
    print("[FastAPI] Shutdown event triggered. Attempting graceful agent shutdown...")
    if agent_thread and agent_thread.is_alive():
        agent.stop_flag = True
        agent_thread.join(timeout=5)
        if agent_thread.is_alive():
            print("[FastAPI] Agent thread did not terminate in time. Forcing abort.")
            agent.agent_state["status"] = "aborted"
        else:
            print("[FastAPI] Agent thread stopped gracefully.")
        agent_thread = None
    # Ensure agent state is saved
    agent.knowledge_base.store_agent_state(agent.agent_state)
    print("[FastAPI] Agent state flushed to disk.")