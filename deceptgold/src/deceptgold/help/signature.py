import json
import hashlib
from ecdsa import SigningKey, VerifyingKey

# nose: B105 - Intentional use of hardcoded key for cryptographic signature
def generate_signature_and_hash(json_honeypot):
    """
    WARNING: INTENTIONAL USE OF HARDCODED PRIVATE KEY
    This private key is purposefully embedded to ensure that
    the honeypot generates consistent and verifiable signatures by a smart contract.
    The security of the key is guaranteed by other means such as via pyarmor

    ATTENTION: Change private key when repository goes to new private version control.
    """
    PRIVATE_KEY_PEM = """-----BEGIN EC PRIVATE KEY-----
    MHQCAQEEILMae4Sd8YfFS1lVru4tE5NK/6z6fEGsRuM0j4BxQ+RHoAcGBSuBBAAKoUQDQgAENEN0
    GIdlOh4ufpvZz2m7t7xBPgP7nz8v2cB3iaT91HBeamJTIbajCXQY8/g4FBNXV0wiGbb2Mn8Km4se
    6vftbw==
    -----END EC PRIVATE KEY-----"""
    private_key = SigningKey.from_pem(PRIVATE_KEY_PEM)
    json_string = json.dumps(json_honeypot, separators=(',', ':'), sort_keys=True)
    json_hash = hashlib.sha256(json_string.encode()).digest()
    signature = private_key.sign(json_hash)
    return signature, json_hash

def validate_signature_and_hash(signature_and_hash: tuple[bytes, bytes]):
    PUBLIC_KEY_PEM = """-----BEGIN PUBLIC KEY-----
    MFYwEAYHKoZIzj0CAQYFK4EEAAoDQgAENEN0GIdlOh4ufpvZz2m7t7xBPgP7nz8v2cB3iaT91HBe
    amJTIbajCXQY8/g4FBNXV0wiGbb2Mn8Km4se6vftbw==
    -----END PUBLIC KEY-----"""
    public_key = VerifyingKey.from_pem(PUBLIC_KEY_PEM)
    try:
        public_key.verify(signature_and_hash[0], signature_and_hash[1])
        return True
    except Exception:
        return False
