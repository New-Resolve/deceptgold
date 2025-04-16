from deceptgold.help.signature import generate_signature_and_hash, validate_signature_and_hash


def test_signature_and_hash():
    json_honeypot = {"a": 1}
    sig_hash = generate_signature_and_hash(json_honeypot)
    assert validate_signature_and_hash(sig_hash)