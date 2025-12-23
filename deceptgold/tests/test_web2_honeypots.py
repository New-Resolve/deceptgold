"""
Unit tests for Web2 Honeypot Services (OpenCanary modules)

This module contains tests to verify that standard Web2 honeypot modules
can be correctly initialized and started within the Deceptgold environment.
"""

import pytest
import sys
from unittest.mock import Mock, MagicMock

# Mock opencanary.config before any opencanary modules are imported
# This prevents SystemExit: 1 when opencanary modules are imported in CI
if 'opencanary.config' not in sys.modules:
    mock_config_module = MagicMock()
    mock_config_module.ConfigException = Exception
    mock_config_instance = MagicMock()
    mock_config_instance.moduleEnabled.return_value = False
    mock_config_instance.getVal.return_value = None
    mock_config_module.config = mock_config_instance
    mock_config_module.Config.return_value = mock_config_instance
    sys.modules['opencanary.config'] = mock_config_module

# List of Web2 modules to test
WEB2_MODULE_IMPORTS = [
    ("opencanary.modules.http", "CanaryHTTP"),
    ("opencanary.modules.https", "CanaryHTTPS"),
    ("opencanary.modules.ftp", "CanaryFTP"),
    ("opencanary.modules.ssh", "CanarySSH"),
    ("opencanary.modules.telnet", "Telnet"),
    ("opencanary.modules.httpproxy", "HTTPProxy"),
    ("opencanary.modules.mysql", "CanaryMySQL"),
    ("opencanary.modules.mssql", "MSSQL"),
    ("opencanary.modules.ntp", "CanaryNtp"),
    ("opencanary.modules.tftp", "CanaryTftp"),
    ("opencanary.modules.vnc", "CanaryVNC"),
    ("opencanary.modules.sip", "CanarySIP"),
    ("opencanary.modules.git", "CanaryGit"),
    ("opencanary.modules.redis", "CanaryRedis"),
    ("opencanary.modules.tcpbanner", "CanaryTCPBanner"),
    ("opencanary.modules.rdp", "CanaryRDP"),
    ("opencanary.modules.snmp", "CanarySNMP"),
    ("opencanary.modules.llmnr", "CanaryLLMNR"),
    ("opencanary.modules.samba", "CanarySamba"),
    ("opencanary.modules.portscan", "CanaryPortscan")
]

@pytest.fixture
def mock_config():
    """Mock configuration object"""
    mock = Mock()
    mock.moduleEnabled.return_value = True
    mock.getVal.side_effect = lambda key, default=None: default
    return mock

@pytest.fixture
def mock_logger():
    """Mock logger object"""
    return Mock()

class TestWeb2HoneypotIntegration:
    """Integration tests for Web2 honeypots"""

    @pytest.mark.parametrize("module_path, class_name", WEB2_MODULE_IMPORTS)
    def test_module_initialization(self, module_path, class_name, mock_config, mock_logger):
        """Test that each Web2 module can be initialized and has required methods"""
        import importlib
        from unittest.mock import patch
        
        try:
            module = importlib.import_module(module_path)
            klass = getattr(module, class_name)
            
            # Special handling for modules with side-effects during __init__
            if class_name == "CanaryHTTPS":
                with patch.object(klass, 'load_certificates', return_value=None):
                    instance = klass(config=mock_config, logger=mock_logger)
            else:
                instance = klass(config=mock_config, logger=mock_logger)
            
            assert instance is not None
            # Standard OpenCanary modules should have startYourEngines or getService
            assert hasattr(instance, 'startYourEngines') or hasattr(instance, 'getService')
            
        except ImportError as e:
            pytest.skip(f"Module {module_path} not found or missing dependencies: {e}")
        except PermissionError as e:
            pytest.skip(f"Permission denied during {class_name} init: {e}")
        except Exception as e:
            pytest.fail(f"Failed to initialize {class_name} from {module_path}: {e}")

    def test_all_web2_modules_list(self):
        """Verify that we have a standard set of Web2 modules defined in our tests"""
        assert len(WEB2_MODULE_IMPORTS) >= 15
