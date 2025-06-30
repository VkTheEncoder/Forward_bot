# src/store.py

import os
import json
from logger import logger

# Default settings template
_defaults = {
    "src_channel": None,
    "dst_channel": None,
    "from_id":    None,
    "to_id":      None
}

# Path one level above this file
SETTINGS_FILE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "settings.json")
)
logger.info(f"[store] SETTINGS_FILE = {SETTINGS_FILE}")

def load_settings():
    logger.info("[store] load_settings() called")
    if not os.path.exists(SETTINGS_FILE):
        logger.info("[store] settings.json not found, writing defaults")
        save_settings(_defaults)
        return _defaults.copy()

    with open(SETTINGS_FILE, "r") as f:
        try:
            data = json.load(f)
            logger.info(f"[store] read data = {data}")
        except json.JSONDecodeError:
            logger.warning("[store] JSON decode error, resetting to defaults")
            data = {}

    # Ensure all keys exist
    for k, v in _defaults.items():
        data.setdefault(k, v)

    logger.info(f"[store] returning merged data = {data}")
    return data

def save_settings(settings):
    logger.info(f"[store] save_settings() called with {settings}")
    os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)
    logger.info("[store] write complete")
