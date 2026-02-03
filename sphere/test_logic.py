"""
Logic for the `sphere test` command.

Author: Kent Beck
"""

import click

from . import persona_logic

def run_single_agent_test(agent_role: str, query: str):
    """
    Finds a specific agent in the active persona and runs a simulated test.
    """
    active_persona = persona_logic.get_active_persona()
    agents = active_persona.get("agents", [])

    target_agent = None
    for agent in agents:
        if agent["role"].lower() == agent_role.lower():
            target_agent = agent
            break

    if not target_agent:
        return False, f"Agent role '{agent_role}' not found in the active persona '{active_persona.get('name')}'."

    # In a real implementation, this would call a local LLM with the agent's prompt and the user's query.
    # For now, we simulate the output.
    simulated_output = f"""## Test Result for Agent: {target_agent["role"]}

- **Query**: "{query}"
- **Agent Prompt**: "{target_agent["prompt"]}"

---

### Simulated LLM Output:

Based on my role as **{target_agent["role"]}**, my analysis of the query is as follows:

[This is a simulated response. A real LLM would generate a detailed analysis here based on the provided prompt and query.]

"""

    return True, simulated_output
