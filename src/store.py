import os, json

# Will live next to the project root\SETTINGS_FILE = os.path.join(os.path.dirname(__file__), '..', 'settings.json')
DEFAULTS = {
    "src_channel": None,
    "dst_channel": None,
    "from_id": None,
    "to_id": None
}

def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        save_settings(DEFAULTS)
        return DEFAULTS.copy()
    with open(SETTINGS_FILE, 'r') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = {}
    for k, v in DEFAULTS.items():
        data.setdefault(k, v)
    return data


def save_settings(settings):
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=2)
