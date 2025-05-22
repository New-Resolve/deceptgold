from deceptgold.helper.signature import generate_signature_and_hash, verify_signature

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
    request_honeypot = {"dst_host": "127.0.0.1", "dst_port": 21, "local_time": "2025-04-17 16:56:29.789537", "local_time_adjusted": "2025-04-17 13:56:29.789555", "logdata": {"SESSION": "154"}, "logtype": 4000, "node_id": "opencanary-1", "src_host": "127.0.0.1", "src_port": 33382, "utc_time": "2025-04-17 16:56:29.789551"}
    signature, json_hash, json_string = generate_signature_and_hash(request_honeypot)
    assert verify_signature(signature, json_hash)


def test_signature_and_hash_list():
    list_honeypot = get_list_hash_honeypot()
    for i, request_honeypot in enumerate(list_honeypot, start=1):
        signature, json_hash, json_string = generate_signature_and_hash(request_honeypot)
        is_valid = verify_signature(signature, json_hash)
        if not is_valid:
            print(f"\n❌ Assinatura inválida no item {i}!")
            print("JSON:", json_string)
            print("Assinatura:", signature.hex())
            print("Hash:", json_hash.hex())
            assert False, f"Assinatura inválida no item {i} - abortando o teste!"
    assert True