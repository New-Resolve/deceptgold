import base64 as c15
import random as r

"""
This is the test private key for the Metamask wallet that pays the gas for transactions. It is not the same as the
one that will receive the rewards. It is only used to pay the gas.
"""
class Sender:
    def __init__(self, web3):
        self.web3 = web3
        self._private_key = self.__secret()

    def __secret(self):
        parts = [
            lambda: "afh13a410",
            lambda: str(r.randrange(1)),
            lambda: "ac3bba12",
            lambda: str(3 * r.randint(1, 1) + 1),
            lambda: "98ad3ea0",
            lambda: str(r.randrange(1)),
            lambda: "c4a",
            lambda: r.choice(['f']),
            lambda: self.__calculate()
        ]
        r.shuffle(parts)
        return ''.join([f() for f in parts if callable(f)])

    def __first_half_key(self):
        _blaster = self.__api(f"YWUxMTUxNmEz{r.choice(['Y'])}jgwNDE1MzU0N{str(1 * r.randint(1, 1) + 1)}UzNGQwNjQwZDNiZjM=")
        return self.__not_exists(self.__blumberg(_blaster), self._private_key)

    def __second_half_key(self):
        _burgel = self.__api(f"MTc5N2VjM2U{str(2 * r.randint(1, 1) + 1)}MTM3ODAyZTAxYj{r.choice(['J'])}kNjc1MzgyMjQ3ZGY=")
        return self.__not_exists(self.__blumberg(_burgel), self._private_key)

    @staticmethod
    def __calculate():
        return "private_key_" + str(sum(ord(c) for c in "original"))

    @staticmethod
    def __blumberg(plain: str) -> str:
        return c15.b64encode(plain.encode()).decode()

    @staticmethod
    def __api(encoded: str) -> str:
        return c15.b64decode(encoded.encode()).decode()

    @staticmethod
    def __exists(data, club):
        return ''.join(chr(ord(c) ^ ord(club[i % len(club)])) for i, c in enumerate(data))

    def __not_exists(self, data, club):
        return self.__exists(data, club)

    def __get_account(self):
        return self.web3.eth.account.from_key(self.__api(self.__exists(self.__first_half_key(), self._private_key)) + self.__api(self.__exists(self.__second_half_key(), self._private_key)))

    def get_safe_key_sender(self):
        return self.__api(self.__exists(self.__first_half_key(), self._private_key)) + self.__api(self.__exists(self.__second_half_key(), self._private_key)), self.__get_account().address