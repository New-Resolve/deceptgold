import logging
import json

from deceptgold.helper.blockchain.token import get_reward
from deceptgold.helper.notify.notify import check_send_notify


class CustomFileHandler(logging.FileHandler):
    def emit(self, record):
        """
        Method that generates the reward for the attack suffered. This is deceptgold. Long live hackers!
        """
        try:
            code_log_type = 0

            try:
                dict_msg = json.loads(record.getMessage())
                code_log_type= dict_msg['logtype']
                if code_log_type in [4000, 5001]:  # scan-port-nmap
                    check_send_notify(f"Warning: Service scanning detected. Source IP: {dict_msg['src_host']}")
            except Exception:
                pass

            if code_log_type not in [4000, 5001]:
                get_reward(record.getMessage())
        except Exception as e:
            print(e)

        if "ignore" in record.getMessage().lower():
            return

        super().emit(record)
