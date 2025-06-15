# main.py

import os
import sys
from dotenv import load_dotenv
from typing import Optional
import threading
import time

# Add the parent directory to the system path to allow for relative imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'agent_ai')))

from agent_ai.core.agent_core import AgentCore
import google.generativeai as genai

USER_INPUT_FILE = os.path.join(os.path.dirname(__file__), 'user_input.txt')

def check_for_user_input(last_seen: float) -> Optional[str]:
    """Check if user_input.txt has been updated. Returns new input if found."""
    if os.path.exists(USER_INPUT_FILE):
        mtime = os.path.getmtime(USER_INPUT_FILE)
        if mtime > last_seen:
            with open(USER_INPUT_FILE, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            return content, mtime
    return None, last_seen

# Patch AgentCore to support async user input
from agent_ai.core.agent_core import AgentCore

def run_agent_with_async_input(agent: AgentCore, initial_task: str):
    last_seen = 0.0
    agent.run_agent(initial_task)
    # Only allow new input if the agent did NOT complete the task
    while agent.agent_state.get("status") not in ["completed", "aborted"]:
        user_input, last_seen = check_for_user_input(last_seen)
        if user_input:
            print(f"\n[Async User Input Detected]: {user_input}")
            agent.run_agent(user_input)
        time.sleep(2)  # Check every 2 seconds
    print("\nAgent has completed or aborted the task. No further user input will be processed until restart.")

def main() -> None:
    """Entry point for the Multimodal Agent. Loads environment, configures LLM, and starts the agent."""
    # Load environment variables from .env if present
    dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path)
    else:
        load_dotenv()

    api_key: Optional[str] = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("WARNING: GOOGLE_API_KEY environment variable not set.")
        print("Please set it (e.g., export GOOGLE_API_KEY='your_key_here') or add it to a .env file in the project root.")
        sys.exit("API Key not found. Exiting.")

    genai.configure(api_key=api_key)
    print("Available models:")
    models = [m for m in genai.list_models() if "generateContent" in getattr(m, "supported_generation_methods", [])]
    if not models:
        print("No models supporting generateContent found.")
        sys.exit(1)
    for m in models:
        print(f"- {m.name} (supports generateContent)")

    # For multimodal (Gemini 1.5 Flash is recommended for its speed and cost-effectiveness with vision):
    llm_client = genai.GenerativeModel('gemini-2.0-flash')
    agent = AgentCore(llm_client=llm_client)

    initial_task = input("Enter the initial task for the AI agent: ")
    print(f"You can asynchronously redirect the agent by editing 'user_input.txt' in this folder.")
    run_agent_with_async_input(agent, initial_task)

if __name__ == "__main__":
    main()