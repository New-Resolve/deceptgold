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
                code_log_type = dict_msg['logtype']
                
                # Comprehensive attack detection system
                if code_log_type == 1001:
                    # Service information - usually not an attack, skip notification
                    pass
                    
                elif code_log_type == 3000:
                    # HTTP probe/reconnaissance
                    event_data = {
                        'attack_type': 'http_probe',
                        'severity': 'low',
                        'src_host': dict_msg.get('src_host', 'unknown'),
                        'service': f"http_port_{dict_msg.get('dst_port', 'unknown')}",
                        'logtype': code_log_type,
                        'logdata': dict_msg.get('logdata', {})
                    }
                    check_send_notify(f"HTTP reconnaissance detected from {dict_msg['src_host']}", event_data)
                    
                elif code_log_type == 3001:
                    # HTTP login attempts / brute force attacks
                    logdata = dict_msg.get('logdata', {})
                    username = logdata.get('USERNAME', 'unknown')
                    password = logdata.get('PASSWORD', 'unknown')
                    hostname = logdata.get('HOSTNAME', 'unknown')
                    dst_port = dict_msg.get('dst_port', 'unknown')
                    
                    event_data = {
                        'attack_type': 'brute_force_login',
                        'severity': 'high',
                        'src_host': dict_msg.get('src_host', 'unknown'),
                        'service': f'http_service_port_{dst_port}',
                        'logtype': code_log_type,
                        'username': username,
                        'password': password,
                        'hostname': hostname,
                        'logdata': logdata
                    }
                    check_send_notify(f"Brute force login attempt detected from {dict_msg['src_host']}", event_data)
                    
                elif code_log_type == 4000:
                    # Port scanning / network reconnaissance
                    event_data = {
                        'attack_type': 'port_scan',
                        'severity': 'medium',
                        'src_host': dict_msg.get('src_host', 'unknown'),
                        'service': 'network_services',
                        'logtype': code_log_type,
                        'dst_port': dict_msg.get('dst_port', 'unknown'),
                        'logdata': dict_msg.get('logdata', {})
                    }
                    check_send_notify(f"Network scanning detected from {dict_msg['src_host']}", event_data)
                    
                elif code_log_type == 5000:
                    # Web3/Blockchain attacks
                    attack_type = dict_msg.get('attack_type', 'web3_unknown')
                    service = dict_msg.get('service', 'web3_service')
                    severity = dict_msg.get('severity', 'medium')
                    
                    event_data = {
                        'attack_type': attack_type,
                        'severity': severity,
                        'src_host': dict_msg.get('src_host', 'unknown'),
                        'service': service,
                        'logtype': code_log_type,
                        'details': dict_msg.get('details', {}),
                        'logdata': dict_msg.get('logdata', {})
                    }
                    check_send_notify(f"Web3 attack detected: {attack_type} from {dict_msg['src_host']}", event_data)
                    
                elif code_log_type in [2000, 2001, 2002, 2003, 2004]:
                    # SSH attacks (various types)
                    attack_types = {
                        2000: 'ssh_connection',
                        2001: 'ssh_login_attempt', 
                        2002: 'ssh_brute_force',
                        2003: 'ssh_command_execution',
                        2004: 'ssh_file_transfer'
                    }
                    
                    event_data = {
                        'attack_type': attack_types.get(code_log_type, 'ssh_unknown'),
                        'severity': 'high' if code_log_type in [2001, 2002, 2003] else 'medium',
                        'src_host': dict_msg.get('src_host', 'unknown'),
                        'service': 'ssh_service',
                        'logtype': code_log_type,
                        'logdata': dict_msg.get('logdata', {})
                    }
                    check_send_notify(f"SSH attack detected from {dict_msg['src_host']}", event_data)
                    
                elif code_log_type in [6000, 6001, 6002]:
                    # FTP attacks
                    attack_types = {
                        6000: 'ftp_connection',
                        6001: 'ftp_login_attempt',
                        6002: 'ftp_file_access'
                    }
                    
                    event_data = {
                        'attack_type': attack_types.get(code_log_type, 'ftp_unknown'),
                        'severity': 'medium',
                        'src_host': dict_msg.get('src_host', 'unknown'),
                        'service': 'ftp_service',
                        'logtype': code_log_type,
                        'logdata': dict_msg.get('logdata', {})
                    }
                    check_send_notify(f"FTP attack detected from {dict_msg['src_host']}", event_data)
                    
                elif code_log_type in [7000, 7001, 7002]:
                    # Database attacks
                    attack_types = {
                        7000: 'database_connection',
                        7001: 'database_injection_attempt',
                        7002: 'database_enumeration'
                    }
                    
                    event_data = {
                        'attack_type': attack_types.get(code_log_type, 'database_unknown'),
                        'severity': 'high',
                        'src_host': dict_msg.get('src_host', 'unknown'),
                        'service': 'database_service',
                        'logtype': code_log_type,
                        'logdata': dict_msg.get('logdata', {})
                    }
                    check_send_notify(f"Database attack detected from {dict_msg['src_host']}", event_data)
                    
                else:
                    # Unknown/new attack types - still process them
                    event_data = {
                        'attack_type': f'unknown_logtype_{code_log_type}',
                        'severity': 'medium',
                        'src_host': dict_msg.get('src_host', 'unknown'),
                        'service': 'unknown_service',
                        'logtype': code_log_type,
                        'logdata': dict_msg.get('logdata', {}),
                        'full_message': dict_msg
                    }
                    check_send_notify(f"Unknown attack type {code_log_type} detected from {dict_msg['src_host']}", event_data)
                    
            except Exception:
                pass

            if code_log_type not in [3000, 4000, 1001]:
                get_reward(record.getMessage())
        except Exception as e:
            print(e)

        if "ignore" in record.getMessage().lower():
            return

        # super().emit(record)
