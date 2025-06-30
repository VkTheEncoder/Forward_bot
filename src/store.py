import os
import json

# Define the path to settings.json next to the project root
defaults = {
    "src_channel": None,
    "dst_channel": None,
    "from_id": None,
    "to_id": None
}

# Compute SETTINGS_FILE relative to this file's parent directory
SETTINGS_FILE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', 'settings.json')
)

def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        save_settings(defaults)
        return defaults.copy()
    with open(SETTINGS_FILE, 'r') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = {}
    # Ensure all keys exist
    for k, v in defaults.items():
        data.setdefault(k, v)
    return data


def save_settings(settings):
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=2)
