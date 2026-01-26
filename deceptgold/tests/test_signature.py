import os
import importlib
import json

from eth_account import Account
from eth_account.messages import encode_defunct
from eth_utils import keccak


_account = Account.create()
_test_private_key = _account.key.hex()
if not _test_private_key.startswith("0x"):
    _test_private_key = f"0x{_test_private_key}"


def _load_signature_module(*, expected_address: str):
    os.environ["DECEPTGOLD_SIGNING_PRIVATE_KEY"] = _test_private_key
    os.environ["DECEPTGOLD_SIGNING_EXPECTED_ADDRESS"] = expected_address

    import deceptgold.helper.signature as signature
    importlib.reload(signature)
    return signature


def _sign_request(*, private_key: str, request_honeypot: dict):
    json_string = json.dumps(request_honeypot, separators=(",", ":"), sort_keys=True)
    message_hash = keccak(text=json_string)
    signed_message = Account.sign_message(encode_defunct(hexstr=message_hash.hex()), private_key=private_key)
    return signed_message.signature, message_hash

def get_list_hash_honeypot():
    return [
        {"dst_host": "127.0.0.1", "dst_port": 2223, "local_time": "2025-04-17 16:56:29.835081",
         "local_time_adjusted": "2025-04-17 13:56:29.835109",
         "logdata": {"LOCALVERSION": "SSH-2.0-OpenSSH_5.1p1 Debian-4", "PASSWORD": "admin",
                     "REMOTEVERSION": "SSH-2.0-OpenSSH_9.2p1 Debian-2+deb12u5", "USERNAME": "root"},
         "logtype": 4002, "node_id": "opencanary-1", "src_host": "127.0.0.1", "src_port": 33374,
         "utc_time": "2025-04-17 16:56:29.835101"},
        {"dst_host": "127.0.0.1", "dst_port": 22, "local_time": "2025-04-17 16:56:29.824626",
         "local_time_adjusted": "2025-04-17 13:56:29.824645", "logdata": {"SESSION": "158"}, "logtype": 4000,
         "node_id": "opencanary-1", "src_host": "127.0.0.1", "src_port": 33482,
         "utc_time": "2025-04-17 16:56:29.824641"}

    ]
def test_signature_and_hash_simple():
    signature_mod = _load_signature_module(expected_address=_account.address)
    request_honeypot = {"dst_host": "127.0.0.1", "dst_port": 21, "local_time": "2025-04-17 16:56:29.789537", "local_time_adjusted": "2025-04-17 13:56:29.789555", "logdata": {"SESSION": "154"}, "logtype": 4000, "node_id": "opencanary-1", "src_host": "127.0.0.1", "src_port": 33382, "utc_time": "2025-04-17 16:56:29.789551"}
    signature, json_hash = _sign_request(private_key=_test_private_key, request_honeypot=request_honeypot)
    assert signature_mod.verify_signature(signature, json_hash, expected_address=_account.address)


def test_signature_and_hash_fails_with_wrong_expected_address():
    wrong_address = Account.create().address
    signature_mod = _load_signature_module(expected_address=wrong_address)
    request_honeypot = {"dst_host": "127.0.0.1", "dst_port": 21, "local_time": "2025-04-17 16:56:29.789537", "local_time_adjusted": "2025-04-17 13:56:29.789555", "logdata": {"SESSION": "154"}, "logtype": 4000, "node_id": "opencanary-1", "src_host": "127.0.0.1", "src_port": 33382, "utc_time": "2025-04-17 16:56:29.789551"}
    signature, json_hash = _sign_request(private_key=_test_private_key, request_honeypot=request_honeypot)
    assert not signature_mod.verify_signature(signature, json_hash, expected_address=wrong_address)


def test_signature_and_hash_list():
    signature_mod = _load_signature_module(expected_address=_account.address)
    list_honeypot = get_list_hash_honeypot()
    for i, request_honeypot in enumerate(list_honeypot, start=1):
        signature, json_hash = _sign_request(private_key=_test_private_key, request_honeypot=request_honeypot)
        is_valid = signature_mod.verify_signature(signature, json_hash, expected_address=_account.address)
        if not is_valid:
            print(f"\n❌ Assinatura inválida no item {i}!")
            print("Assinatura:", signature.hex())
            print("Hash:", json_hash.hex())
            assert False, f"Assinatura inválida no item {i} - abortando o teste!"
    assert True