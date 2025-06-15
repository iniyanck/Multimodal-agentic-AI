# docs/advanced_usage.md

## Advanced Usage

### Customizing the Agent
- You can extend the agent by adding new tools in `agent_ai/action/` or new perception modules in `agent_ai/perception/`.
- Update the `GlobalPrompt` to describe new tools for the LLM.

### Platform-Specific Notes
- **Window focusing** is only supported on Windows.
- **Screen capture** may require extra permissions or dependencies on macOS/Linux.

### Debugging
- Check `agent_ai/logs/agent.log` for detailed logs.
- Use the `test_*.py` files to validate core functionality.

### API Key Management
- Use a `.env` file for local development. Never commit your real API key.

### Extending Memory
- The agent uses SQLite for persistent memory. You can add new tables or fields as needed.

---
For more, see the code comments and open an issue if you need help!
