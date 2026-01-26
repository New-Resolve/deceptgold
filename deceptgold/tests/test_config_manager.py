from pathlib import Path

from deceptgold.configuration.config_manager import update_config, get_config

def test_create_config(tmp_path):
    config_file = tmp_path / ".deceptgold.conf"
    update_config("create_test", "value_create_test", config_file=config_file)
    assert config_file.exists()

def test_set_config(tmp_path):
    config_file = tmp_path / ".deceptgold.conf"
    update_config("key_test", "value_test", config_file=config_file)
    assert get_config(module_name_honeypot="test_config_manager", key="key_test", file_config=config_file) == "value_test"

def test_set_config_not_exists_str(tmp_path):
    config_file = tmp_path / ".deceptgold.conf"
    assert get_config(module_name_honeypot="test_config_manager", key="not_key", default="not_found", file_config=config_file) == "not_found"

def test_set_config_not_exists_bool(tmp_path):
    config_file = tmp_path / ".deceptgold.conf"
    assert get_config(module_name_honeypot="test_config_manager", key="not_key", default=False, file_config=config_file) == False