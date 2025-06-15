# agent_ai/memory/knowledge_base.py

import sqlite3
import json
import os

class KnowledgeBase:
    """KnowledgeBase manages the storage and retrieval of agent knowledge and state using a SQLite database."""

    def __init__(self, db_name: str = "agent_knowledge.db"):
        """Initializes the knowledge base with a SQLite database."""
        self.db_path = os.path.join(os.path.dirname(__file__), db_name)
        self._initialize_db()

    def _initialize_db(self):
        """Initializes the SQLite database schema."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS knowledge (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agent_state (
                    id INTEGER PRIMARY KEY,
                    state_data TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            print(f"KnowledgeBase initialized at {self.db_path}")
        except sqlite3.Error as e:
            print(f"Error initializing database: {e}")
        finally:
            if conn:
                conn.close()

    def store_knowledge(self, key: str, value: str) -> bool:
        """Stores a key-value pair in the knowledge base."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO knowledge (key, value) VALUES (?, ?)", (key, value))
            conn.commit()
            print(f"Stored knowledge: {key} = {value[:50]}...") # Truncate for display
            return True
        except sqlite3.Error as e:
            print(f"Error storing knowledge: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def retrieve_knowledge(self, key: str) -> str | None:
        """Retrieves knowledge by key."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM knowledge WHERE key = ?", (key,))
            result = cursor.fetchone()
            if result:
                print(f"Retrieved knowledge for {key}")
                return result[0]
            print(f"No knowledge found for key: {key}")
            return None
        except sqlite3.Error as e:
            print(f"Error retrieving knowledge: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def delete_knowledge(self, key: str) -> bool:
        """Deletes knowledge by key."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM knowledge WHERE key = ?", (key,))
            conn.commit()
            print(f"Deleted knowledge for key: {key}")
            return True
        except sqlite3.Error as e:
            print(f"Error deleting knowledge: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def store_agent_state(self, state: dict) -> bool:
        """Stores the current state of the agent."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            state_json = json.dumps(state)
            # We'll just update the single agent state entry, or insert if it doesn't exist
            cursor.execute("INSERT OR REPLACE INTO agent_state (id, state_data) VALUES (1, ?)", (state_json,))
            conn.commit()
            print("Agent state stored.")
            return True
        except sqlite3.Error as e:
            print(f"Error storing agent state: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def load_agent_state(self) -> dict | None:
        """Loads the last saved state of the agent."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT state_data FROM agent_state WHERE id = 1")
            result = cursor.fetchone()
            if result:
                state = json.loads(result[0])
                print("Agent state loaded.")
                return state
            print("No agent state found.")
            return None
        except sqlite3.Error as e:
            print(f"Error loading agent state: {e}")
            return None
        finally:
            if conn:
                conn.close()

# Example Usage
if __name__ == "__main__":
    kb = KnowledgeBase(db_name="test_agent_knowledge.db")
    
    kb.store_knowledge("favorite_color", "blue")
    kb.store_knowledge("api_key_service_x", "sk-12345abcdef")
    
    print(f"Retrieved favorite color: {kb.retrieve_knowledge('favorite_color')}")
    print(f"Retrieved non-existent key: {kb.retrieve_knowledge('non_existent_key')}")
    
    agent_current_state = {"last_action": "read file", "current_task": "analyze data"}
    kb.store_agent_state(agent_current_state)
    
    loaded_state = kb.load_agent_state()
    if loaded_state:
        print(f"Loaded agent state: {loaded_state}")
    
    kb.delete_knowledge("favorite_color")
    print(f"Retrieved favorite color after deletion: {kb.retrieve_knowledge('favorite_color')}")