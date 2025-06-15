# Basic smoke test for AgentCore
import sys
import os
import unittest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'agent_ai')))
from agent_ai.core.agent_core import AgentCore

class MockLLMClient:
    def generate_content(self, contents, generation_config):
        return type('obj', (object,), {'text': '{"action": "task_complete"}'})

class AgentCoreTest(unittest.TestCase):
    def test_agent_init(self):
        agent = AgentCore(llm_client=MockLLMClient())
        self.assertIsNotNone(agent)

    def test_run_agent_completes(self):
        agent = AgentCore(llm_client=MockLLMClient())
        agent.run_agent("Test task")
        self.assertEqual(agent.agent_state["status"], "completed")

if __name__ == "__main__":
    unittest.main()
