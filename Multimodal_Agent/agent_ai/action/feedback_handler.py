# agent_ai/action/feedback_handler.py

class FeedbackHandler:
    def __init__(self):
        self.feedback_queue = []

    def receive_feedback(self, feedback: str):
        """Receives feedback from an external source (e.g., user, system)."""
        self.feedback_queue.append(feedback)
        print(f"Feedback received: {feedback}")

    def get_latest_feedback(self) -> str | None:
        """Retrieves and clears the latest feedback."""
        if self.feedback_queue:
            return self.feedback_queue.pop(0) # FIFO
        return None

    def get_all_feedback(self) -> list[str]:
        """Retrieves and clears all pending feedback."""
        feedback = list(self.feedback_queue)
        self.feedback_queue.clear()
        return feedback

    def process_feedback(self, agent_state: dict, feedback: str) -> dict:
        """
        Processes feedback and updates the agent's internal state or understanding.
        This is where your agent's reasoning about feedback will go.
        For now, it's a placeholder.
        """
        print(f"Processing feedback: '{feedback}' for agent state.")
        agent_state["last_feedback"] = feedback
        return agent_state

    def ask_user_for_input(self, question: str) -> str:
        """
        Asks the user a question and returns their input.
        This is a blocking call for user interaction.
        """
        print(f"\n--- Agent needs input ---")
        print(f"Agent Question: {question}")
        user_input = input("Your response: ")
        self.receive_feedback(f"User provided input: {user_input}") # Log user's response as feedback
        return user_input

# Example Usage
if __name__ == "__main__":
    feedback_handler = FeedbackHandler()
    feedback_handler.receive_feedback("Good job on the last task!")
    feedback_handler.receive_feedback("You missed a step here.")
    
    agent_state = {"current_task": "logging in"}
    updated_state = feedback_handler.process_feedback(agent_state, feedback_handler.get_latest_feedback())
    print(f"Updated agent state after feedback: {updated_state}")
    
    all_feedback = feedback_handler.get_all_feedback()
    print(f"All remaining feedback: {all_feedback}")

    user_answer = feedback_handler.ask_user_for_input("What is your favorite color?")
    print(f"User's favorite color: {user_answer}")