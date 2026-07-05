"""Unit tests for config module."""
import json
import os
import pytest
from config import load_config, save_config, DEFAULT_CONFIG, CONFIG_FILE


@pytest.fixture(autouse=True)
def use_tmp_dir(tmp_path, monkeypatch):
    """Run each test in a temporary directory so config files don't persist."""
    monkeypatch.chdir(tmp_path)


class TestLoadConfig:
    def test_creates_default_config_when_file_missing(self):
        config = load_config()
        assert config == DEFAULT_CONFIG
        assert os.path.exists(CONFIG_FILE)

    def test_loads_existing_config(self):
        custom = {"education_level": "ALEVEL", "custom_key": "value"}
        with open(CONFIG_FILE, "w") as f:
            json.dump(custom, f)
        config = load_config()
        assert config == custom

    def test_default_config_has_expected_keys(self):
        config = load_config()
        assert "education_level" in config
        assert "forms_o_level" in config

    def test_default_education_level_is_olevel(self):
        config = load_config()
        assert config["education_level"] == "OLEVEL"


class TestSaveConfig:
    def test_saves_config_to_file(self):
        data = {"key": "value", "number": 42}
        save_config(data)
        assert os.path.exists(CONFIG_FILE)
        with open(CONFIG_FILE, "r") as f:
            loaded = json.load(f)
        assert loaded == data

    def test_overwrites_existing_config(self):
        save_config({"first": True})
        save_config({"second": True})
        with open(CONFIG_FILE, "r") as f:
            loaded = json.load(f)
        assert "second" in loaded
        assert "first" not in loaded

    def test_saves_with_indent(self):
        save_config({"key": "value"})
        with open(CONFIG_FILE, "r") as f:
            content = f.read()
        assert "    " in content  # indented with 4 spaces
