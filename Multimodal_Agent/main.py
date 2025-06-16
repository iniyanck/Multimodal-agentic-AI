# main.py

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
from typing import Optional
import time
from agent_ai.core.agent_core import AgentCore
import google.generativeai as genai
from agent_ai.core.llm.loader import LLMLoader

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

    # Multi-LLM support (config only, no prompt)
    llm_loader = LLMLoader()
    llm_name, llm_info = llm_loader.get_default_llm()
    llm_client = llm_loader.get_llm_client(llm_name, llm_info)
    print(f"Using LLM: {llm_name} ({llm_info['provider']}, model: {llm_info['model']})")
    agent = AgentCore(llm_client=llm_client)

    initial_task = input("Enter the initial task for the AI agent: ")
    print(f"You can asynchronously redirect the agent by editing 'user_input.txt' in this folder.")
    run_agent_with_async_input(agent, initial_task)

if __name__ == "__main__":
    main()