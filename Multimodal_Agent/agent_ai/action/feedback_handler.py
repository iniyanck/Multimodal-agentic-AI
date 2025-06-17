# agent_ai/action/feedback_handler.py

"""
FeedbackHandler class for managing agent feedback and user input.
"""

class FeedbackHandler:
    """Handles feedback queue and user input for the agent."""
    def __init__(self):
        from ..utils.logger import Logger
        self.logger = Logger()
        self.feedback_queue = []

    def receive_feedback(self, feedback: str):
        """Receives feedback from an external source (e.g., user, system)."""
        self.feedback_queue.append(feedback)
        self.logger.info(f"Feedback received: {feedback}")

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
        """Processes feedback and updates the agent's internal state or understanding."""
        self.logger.info(f"Processing feedback: '{feedback}' for agent state.")
        agent_state["last_feedback"] = feedback
        return agent_state

    '''def ask_user_for_input(self, question: str) -> str:
        """Web-compatible: writes question to pending_question.txt and waits for answer in pending_answer.txt."""
        import os, time
        pending_question_path = os.path.join(os.path.dirname(__file__), "..", "..", "pending_question.txt")
        pending_answer_path = os.path.join(os.path.dirname(__file__), "..", "..", "pending_answer.txt")
        # Write the question
        with open(pending_question_path, "w", encoding="utf-8") as f:
            f.write(question)
        self.logger.info(f"Agent asked user: {question}")
        # Wait for answer (poll every second, timeout after 5 minutes)
        for _ in range(300):
            if os.path.exists(pending_answer_path):
                with open(pending_answer_path, "r", encoding="utf-8") as f:
                    answer = f.read().strip()
                os.remove(pending_answer_path)
                self.logger.info(f"User answered: {answer}")
                return answer
            time.sleep(1)
        self.logger.error("Timed out waiting for user answer.")
        return ""'''

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