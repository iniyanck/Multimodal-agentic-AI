# main.py

import os
import sys

# Add the parent directory to the system path to allow for relative imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'agent_ai')))

from agent_ai.core.agent_core import AgentCore

# --- UNCOMMENT AND CONFIGURE THESE LINES ---
import google.generativeai as genai

def main():
    # It's highly recommended to load API keys from environment variables for security.
    # Set your GOOGLE_API_KEY environment variable.
    api_key = os.environ.get("GOOGLE_API_KEY") 
    if not api_key:
        print("WARNING: GOOGLE_API_KEY environment variable not set.")
        print("Please set it (e.g., export GOOGLE_API_KEY='your_key_here') or replace the placeholder in main.py.")
        # For demonstration purposes ONLY, you can hardcode it here if you understand the security implications.
        # api_key = "YOUR_HARDCODED_GEMINI_API_KEY" # <--- REPLACE WITH YOUR ACTUAL API KEY IF NOT USING ENV VARS!
        sys.exit("API Key not found. Exiting.")


    genai.configure(api_key=api_key) 
    print("Available models:")
    for m in genai.list_models():
        # Only list models that support generateContent (text generation) and optionally vision if needed
        if "generateContent" in m.supported_generation_methods:
            print(f"- {m.name} (supports generateContent)")

    # Initialize your LLM client here
    # For multimodal (Gemini 1.5 Flash is recommended for its speed and cost-effectiveness with vision):
    llm_client = genai.GenerativeModel('gemini-2.0-flash') 
    
    agent = AgentCore(llm_client=llm_client)
    
    initial_task = input("Enter the initial task for the AI agent: ")
    agent.run_agent(initial_task)

if __name__ == "__main__":
    main()