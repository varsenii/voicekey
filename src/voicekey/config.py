# src/voicekey/config.py
import yaml
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

def load_config(path: str) -> Dict:
    """
    Load YAML config and do basic validation.
    Returns a dict with key 'commands' -> list of {phrase, action}
    """
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not data or "commands" not in data:
        raise ValueError("Invalid config: missing 'commands' key")

    commands = []
    for entry in data["commands"]:
        phrase = entry.get("phrase")
        action = entry.get("action")
        if not phrase or not action or "type" not in action:
            raise ValueError(f"Invalid entry in config: {entry!r}")
        commands.append({"phrase": phrase.strip().lower(), "action": action})

    logger.info("Loaded %d command(s) from %s", len(commands), path)
    return {"commands": commands}