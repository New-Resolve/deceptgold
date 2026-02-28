import os
from unittest.mock import Mock

import pytest


def _require_integration_tests_enabled():
    if os.environ.get("RUN_INTEGRATION_TESTS") != "1":
        pytest.skip("Integration tests disabled. Set RUN_INTEGRATION_TESTS=1 to enable.")


def _mock_config():
    cfg = Mock()
    cfg.moduleEnabled.return_value = True
    cfg.getVal.side_effect = lambda key, default=None: default
    return cfg


@pytest.mark.integration
@pytest.mark.parametrize(
    "honeypot_cls, kwargs",
    [
        ("deceptgold.helper.web3honeypot.rpc_node.RPCNodeHoneypot", {"port": 0}),
        ("deceptgold.helper.web3honeypot.wallet_service.WalletServiceHoneypot", {"port": 0}),
        (
            "deceptgold.helper.web3honeypot.ipfs_gateway.IPFSGatewayHoneypot",
            {"port": 0, "api_port": 0},
        ),
    ],
)
def test_web3_services_can_bind_port(honeypot_cls, kwargs):
    _require_integration_tests_enabled()

    import importlib

    module_name, class_name = honeypot_cls.rsplit(".", 1)
    module = importlib.import_module(module_name)
    klass = getattr(module, class_name)

    hp = klass(config=_mock_config(), logger=Mock(), **kwargs)
    service = hp.getService()

    service.startService()
    try:
        assert getattr(service, "_port", None) is not None
    finally:
        service.stopService()


@pytest.mark.integration
@pytest.mark.parametrize(
    "module_path, class_name",
    [
        ("opencanary.modules.http", "CanaryHTTP"),
        ("opencanary.modules.ssh", "CanarySSH"),
    ],
)
def test_web2_services_can_bind_port_when_supported(module_path, class_name):
    _require_integration_tests_enabled()

    import importlib

    try:
        module = importlib.import_module(module_path)
    except ImportError as e:
        pytest.skip(f"Module {module_path} not available: {e}")

    klass = getattr(module, class_name)

    cfg = _mock_config()
    logger = Mock()

    instance = klass(config=cfg, logger=logger)

    if not hasattr(instance, "getService"):
        pytest.skip(f"{class_name} does not expose getService()")

    service = instance.getService()

    if not hasattr(service, "startService"):
        pytest.skip(f"{class_name} service is not a Twisted service")

    service.startService()
    try:
        assert getattr(service, "_port", None) is not None
    finally:
        service.stopService()
