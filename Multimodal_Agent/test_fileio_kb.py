import unittest
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'agent_ai')))
from agent_ai.perception.file_io import FileIO
from agent_ai.memory.knowledge_base import KnowledgeBase

class FileIOTest(unittest.TestCase):
    def setUp(self):
        self.file_io = FileIO()
        self.test_filename = "test_file.txt"
        self.test_content = "Hello, world!"

    def tearDown(self):
        if os.path.exists(self.test_filename):
            os.remove(self.test_filename)

    def test_write_and_read_file(self):
        self.assertTrue(self.file_io.write_file(self.test_filename, self.test_content))
        content = self.file_io.read_file(self.test_filename)
        self.assertEqual(content, self.test_content)

    def test_list_directory(self):
        files = self.file_io.list_directory('.')
        self.assertIsInstance(files, list)
        self.assertIn(self.test_filename, files)

class KnowledgeBaseTest(unittest.TestCase):
    def setUp(self):
        self.kb = KnowledgeBase(db_name="test_agent_knowledge.db")

    def tearDown(self):
        if os.path.exists(os.path.join(os.path.dirname(__file__), 'agent_ai', 'memory', 'test_agent_knowledge.db')):
            os.remove(os.path.join(os.path.dirname(__file__), 'agent_ai', 'memory', 'test_agent_knowledge.db'))

    def test_store_and_retrieve_knowledge(self):
        self.assertTrue(self.kb.store_knowledge("foo", "bar"))
        value = self.kb.retrieve_knowledge("foo")
        self.assertEqual(value, "bar")
        self.assertTrue(self.kb.delete_knowledge("foo"))
        self.assertIsNone(self.kb.retrieve_knowledge("foo"))

    def test_store_and_load_agent_state(self):
        state = {"test": 123}
        self.assertTrue(self.kb.store_agent_state(state))
        loaded = self.kb.load_agent_state()
        self.assertEqual(loaded, state)

if __name__ == "__main__":
    unittest.main()
