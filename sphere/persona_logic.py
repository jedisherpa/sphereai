'''
Logic for the `sphere persona` command.

Author: Martin Fowler
'''

import os
import json

SPHERE_DIR = os.path.expanduser("~/.sphere")
PERSONAS_DIR = os.path.join(SPHERE_DIR, "personas")
CONFIG_FILE = os.path.join(SPHERE_DIR, "config.json")

DEFAULT_PERSONA_NAME = "general"

DEFAULT_PERSONA_CONTENT = {
    "name": "General Analysis",
    "agents": [
        {"role": "Rationalist", "prompt": "Analyze the query from a purely logical and rational perspective."},
        {"role": "Skeptic", "prompt": "Question the assumptions and premises of the query."},
        {"role": "Historian", "prompt": "Provide historical context and precedent for the query."},
        {"role": "Futurist", "prompt": "Extrapolate the long-term implications of the query."},
        {"role": "Artist", "prompt": "Explore the creative and aesthetic dimensions of the query."},
        {"role": "Economist", "prompt": "Analyze the financial and economic factors related to the query."},
        {"role": "Technologist", "prompt": "Examine the technological aspects and feasibility of the query."},
        {"role": "Ethicist", "prompt": "Consider the moral and ethical implications of the query."},
        {"role": "Strategist", "prompt": "Formulate a strategic approach to the query."},
        {"role": "Storyteller", "prompt": "Weave a narrative around the query to make it more compelling."},
        {"role": "Synthesizer", "prompt": "Combine the insights from all other agents into a coherent whole."},
        {"role": "Critic", "prompt": "Provide a critical review of the synthesis, pointing out weaknesses."}
    ]
}

def initialize_personas():
    """Ensures the personas directory and default persona exist."""
    if not os.path.exists(PERSONAS_DIR):
        os.makedirs(PERSONAS_DIR)

    default_persona_path = os.path.join(PERSONAS_DIR, f"{DEFAULT_PERSONA_NAME}.json")
    if not os.path.exists(default_persona_path):
        with open(default_persona_path, "w") as f:
            json.dump(DEFAULT_PERSONA_CONTENT, f, indent=2)

    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w") as f:
            json.dump({"active_persona": DEFAULT_PERSONA_NAME}, f, indent=2)

def list_personas():
    """Lists all available personas."""
    initialize_personas()
    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
        active_persona = config.get("active_persona", DEFAULT_PERSONA_NAME)
    except (FileNotFoundError, json.JSONDecodeError):
        active_persona = DEFAULT_PERSONA_NAME

    personas = []
    for filename in os.listdir(PERSONAS_DIR):
        if filename.endswith(".json"):
            name = filename[:-5]
            personas.append({"name": name, "is_active": name == active_persona})
    return personas

def use_persona(name):
    """Sets the active persona."""
    initialize_personas()
    persona_path = os.path.join(PERSONAS_DIR, f"{name}.json")
    if not os.path.exists(persona_path):
        return False, f"Persona '{name}' not found."

    with open(CONFIG_FILE, "w") as f:
        json.dump({"active_persona": name}, f, indent=2)
    return True, f"Successfully set active persona to '{name}'."

def show_persona(name=None):
    """Shows the content of a specific or the active persona."""
    initialize_personas()
    if not name:
        try:
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
            name = config.get("active_persona", DEFAULT_PERSONA_NAME)
        except (FileNotFoundError, json.JSONDecodeError):
            name = DEFAULT_PERSONA_NAME

    persona_path = os.path.join(PERSONAS_DIR, f"{name}.json")
    if not os.path.exists(persona_path):
        return None, f"Persona '{name}' not found."

    with open(persona_path, "r") as f:
        try:
            content = json.load(f)
            return content, None
        except json.JSONDecodeError as e:
            return None, f"Error reading persona file {name}.json: {e}"

def get_active_persona():
    """Gets the content of the currently active persona."""
    content, err = show_persona()
    if err:
        # This might happen if the active persona file was deleted. Fallback to default.
        return DEFAULT_PERSONA_CONTENT
    return content
