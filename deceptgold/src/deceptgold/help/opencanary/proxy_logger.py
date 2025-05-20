import logging

from deceptgold.help.blockchain.token import get_reward


class CustomFileHandler(logging.FileHandler):
    def emit(self, record):
        """
        Method that generates the reward for the attack suffered. This is deceptgold. Long live hackers!
        """
        try:
            get_reward(record.getMessage())
        except Exception as e:
            print(e)

        if "ignore" in record.getMessage().lower():
            return

        # super().emit(record)
