import os
import json

# Default settings template
_defaults = {
    "src_channel": None,
    "dst_channel": None,
    "from_id": None,
    "to_id": None
}

# Path ../settings.json (one level above src/)
SETTINGS_FILE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', 'settings.json')
)

def load_settings():
    # If it doesn't exist yet, write the defaults
    if not os.path.exists(SETTINGS_FILE):
        save_settings(_defaults)
        return _defaults.copy()

    with open(SETTINGS_FILE, 'r') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = {}

    # ensure all keys exist
    for k, v in _defaults.items():
        data.setdefault(k, v)
    return data

def save_settings(settings):
    # Ensure the directory exists
    os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=2)
