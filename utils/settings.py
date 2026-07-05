# utils/settings.py
"""A tiny key-value settings store saved to settings.json in the project."""
import json
import os

SETTINGS_FILE = os.path.join(os.getcwd(), "settings.json")


def _load():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def get_setting(key, default=None):
    return _load().get(key, default)


def set_setting(key, value):
    data = _load()
    data[key] = value
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return value


def all_settings():
    return _load()