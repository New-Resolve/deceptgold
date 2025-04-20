from pathlib import Path

from deceptgold.configuration.config_manager import update_config, get_config

def test_create_config():
    update_config("create_test", "value_create_test")
    CONFIG_PATH = Path.home() / ".deceptgold.conf"
    assert CONFIG_PATH.exists()

def test_set_config():
    update_config("key_test", "value_test")
    assert get_config(module_name_honeypot="test_config_manager", key="key_test") == "value_test"

def test_set_config_not_exists_str():
    assert get_config(module_name_honeypot="test_config_manager", key="not_key", default="not_found") == "not_found"

def test_set_config_not_exists_bool():
    assert get_config(module_name_honeypot="test_config_manager", key="not_key", default=False) == False