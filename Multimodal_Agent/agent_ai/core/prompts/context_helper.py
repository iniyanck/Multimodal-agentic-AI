"""
ContextHelper class for summarizing current relevant context for the LLM.
"""

class ContextHelper:
    def get_current_context(self, agent_state: dict) -> str:
        context = []
        if agent_state.get('last_action_feedback'):
            context.append(f"Last action feedback: {agent_state['last_action_feedback']}")
        if agent_state.get('last_read_content'):
            context.append(f"Last file content read: {agent_state['last_read_content'][:200]}...")
        if agent_state.get('last_directory_list'):
            context.append(f"Last directory listing: {agent_state['last_directory_list']}")
        if agent_state.get('last_retrieved_knowledge'):
            context.append(f"Last retrieved knowledge: {agent_state['last_retrieved_knowledge']}")
        return "\n".join(context) if context else "No specific observations yet."
