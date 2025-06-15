# Multimodal Agentic AI (Aether)

## Project Overview

"Aether" is an autonomous Multimodal Agentic AI designed to interact with your computer's environment, perceive visual information (via screen capture), perform file system operations, execute shell commands, and learn from user feedback to accomplish complex tasks. This agent leverages a Large Language Model (LLM) as its "brain" to reason, plan, and execute actions based on its observations and goals.

The agent operates in a continuous loop of `Perceive -> Think -> Act`, allowing it to adapt to dynamic environments and achieve user-defined objectives.

## Key Features

* **Multimodal Perception:**
    * **Screen Capture:** The agent can capture screenshots of the entire screen or specific regions, enabling it to "see" and interpret visual information on your desktop.
    * **File I/O:** Ability to read and write files, crucial for interacting with local data and scripts.
* **Intelligent Reasoning & Planning:**
    * Powered by a Large Language Model (e.g., Google Gemini Pro Vision) for advanced understanding of tasks, dynamic planning, and decision-making.
    * Utilizes a `GlobalPrompt` to define its persona, overarching goals, and available tools, ensuring consistent behavior.
* **Autonomous Action Execution:**
    * **System Interaction:** Can execute arbitrary shell commands, allowing for broad control over the operating system.
    * **File Management:** Performs file reading and writing operations.
    * **User Interaction:** Capable of asking clarifying questions to the user when uncertain, facilitating collaborative task completion.
* **Memory Systems:**
    * **Short-Term Memory:** Maintains a buffer of recent observations and actions to retain context within a task.
    * **Long-Term Knowledge Base:** Stores persistent information (key-value pairs, agent state) using SQLite, allowing the agent to learn and remember across sessions.
* **Feedback Mechanism:** Incorporates a `FeedbackHandler` to receive and process external (e.g., user) feedback, enabling the agent to learn from mistakes and refine its strategies.
* **Robust Logging:** Detailed logging (`Logger`) tracks the agent's internal thoughts, actions, and system responses, crucial for debugging and understanding its behavior.

## Project Structure

The project is organized into logical modules:

* `agent_ai/core/`: Contains the central `AgentCore` logic and `GlobalPrompt` definitions.
* `agent_ai/perception/`: Handles how the agent perceives its environment (e.g., `file_io.py`, `screen_capture.py`).
* `agent_ai/action/`: Defines the actions the agent can perform (e.g., `system_interaction.py`, `feedback_handler.py`).
* `agent_ai/memory/`: Manages the agent's memory systems (`knowledge_base.py`, `short_term_memory.py`).
* `agent_ai/utils/`: Utility functions, such as `logger.py`.
* `main.py`: The entry point for running the agent.

## Setup and Installation

### Prerequisites

* Python 3.8+
* `pip` package installer

### Environment Setup

1.  **Clone the repository:**
    ```bash
    git clone <your-repository-url>
    cd <your-repository-directory>
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    # On Windows:
    .\venv\Scripts\activate
    # On macOS/Linux:
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up environment variables:**
    - Copy `.env.example` to `.env` and add your API key:
      ```bash
      cp .env.example .env
      # Then edit .env and set GOOGLE_API_KEY=your_gemini_api_key_here
      ```
    - Alternatively, you can set the environment variable manually:
      * **Linux/macOS:**
        ```bash
        export GOOGLE_API_KEY="YOUR_GEMINI_API_KEY"
        ```
      * **Windows (Command Prompt):**
        ```cmd
        set GOOGLE_API_KEY=YOUR_GEMINI_API_KEY
        ```
      * **Windows (PowerShell):**
        ```powershell
        $env:GOOGLE_API_KEY="YOUR_GEMINI_API_KEY"
        ```

    - The agent will automatically load variables from a `.env` file if present.

## Running the Agent

To start the agent, run the `main.py` script:

```bash
python main.py
```