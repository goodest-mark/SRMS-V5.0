import json
import os

CONFIG_FILE = "school_settings.json"

DEFAULT_CONFIG = {
    "education_level": "OLEVEL",
    "forms_o_level": ["Form I", "Form II", "Form III", "Form IV"]
}

def load_config():
    if not os.path.exists(CONFIG_FILE):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG

    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def save_config(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4)