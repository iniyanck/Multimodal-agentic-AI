# main.py

import os
import sys
from dotenv import load_dotenv
from typing import Optional

# Add the parent directory to the system path to allow for relative imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'agent_ai')))

from agent_ai.core.agent_core import AgentCore
import google.generativeai as genai

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
    agent.run_agent(initial_task)

if __name__ == "__main__":
    main()