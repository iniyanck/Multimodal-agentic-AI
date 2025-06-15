# agent_ai/memory/short_term_memory.py

class ShortTermMemory:
    def __init__(self, max_size: int = 10):
        """Initializes short-term memory with a buffer of limited size."""
        from ..utils.logger import Logger
        self.logger = Logger()
        self.memory_buffer = []
        self.max_size = max_size # Keep last N relevant observations/thoughts

    def add_event(self, event: str, type: str = "observation"):
        """Adds an event or observation to short-term memory."""
        self.memory_buffer.append({"type": type, "event": event})
        if len(self.memory_buffer) > self.max_size:
            self.memory_buffer.pop(0) # Remove oldest

    def get_recent_events(self) -> list[dict]:
        """Retrieves recent events from memory."""
        return list(self.memory_buffer) # Return a copy

    def clear_memory(self):
        """Clears the short-term memory."""
        self.memory_buffer = []
        self.logger.info("Short-term memory cleared.")

# Example Usage
if __name__ == "__main__":
    stm = ShortTermMemory(max_size=3)
    stm.add_event("Observed button A", "visual")
    stm.add_event("User clicked OK", "feedback")
    stm.add_event("Typed 'Hello'", "action")
    stm.add_event("Received error message", "system_output")

    print(stm.get_recent_events())
    stm.clear_memory()
    print(stm.get_recent_events())