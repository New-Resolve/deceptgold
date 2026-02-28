import json
import os
import logging
import socket
import platform

from deceptgold.helper.helper import get_temp_log_path, NAME_FILE_LOG

filelog_temp = get_temp_log_path(NAME_FILE_LOG)
platform_system = platform.system().lower().strip()
if platform_system == "windows":
    filelog_temp = get_temp_log_path(NAME_FILE_LOG).replace('\\', '\\\\')

NODE_ID = socket.gethostname()
FILE_CONF_OPENCANARY = ".opencanary.conf"
PATH_CONFIG_OPENCANARY = os.path.join(os.path.expanduser("~"), FILE_CONF_OPENCANARY)

config_data = {
    "device.node_id": NODE_ID,
    "ip.ignorelist": [  ],
    "logtype.ignorelist": [  ],
    "web2.git.enabled": False,
    "web2.git.port" : 9418,
    "web2.ftp.enabled": True,
    "web2.ftp.port": 2121,
    "web2.ftp.banner": "FTP server ready",
    "web2.ftp.log_auth_attempt_initiated": False,
    "web2.http.banner": "Apache/2.2.22 (Ubuntu)",
    "web2.http.enabled": True,
    "web2.http.port": 8090,
    "web2.http.skin": "nasLogin",
    "web2.http.log_unimplemented_method_requests": False,
    "web2.http.log_redirect_request": False,
    "web2.https.enabled": False,
    "web2.https.port": 443,
    "web2.https.skin": "nasLogin",
    "web2.https.certificate": "/etc/ssl/opencanary/opencanary.pem",
    "web2.https.key": "/etc/ssl/opencanary/opencanary.key",
    "web2.httpproxy.enabled" : False,
    "web2.httpproxy.port": 8080,
    "web2.httpproxy.skin": "squid",
    "web2.llmnr.enabled": False,
    "web2.llmnr.query_interval": 60,
    "web2.llmnr.query_splay": 5,
    "web2.llmnr.hostname": "DC03",
    "web2.llmnr.port": 5355,
    "logger": {
        "class": "PyLogger",
        "kwargs": {
            "formatters": {
                "plain": {
                    "format": "%(message)s"
                },
                "syslog_rfc": {
                    "format": "opencanaryd[%(process)-5s:%(thread)d]: %(name)s %(levelname)-5s %(message)s"
                },
                "default": {
                    "format": "%(asctime)s %(levelname)s: %(message)s"
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                    "formatter": "plain"
                },
                "file": {
                    "class": "logging.FileHandler",
                    "filename": f"{filelog_temp}",
                    "formatter": "default"
                }
            }
        }
    },
    "web2.portscan.enabled": False,
    "web2.portscan.ignore_localhost": False,
    "web2.portscan.logfile":"/var/log/kern.log",
    "web2.portscan.synrate": 5,
    "web2.portscan.nmaposrate": 5,
    "web2.portscan.lorate": 3,
    "web2.portscan.ignore_ports": [ ],
    "web2.smb.auditfile": "/var/log/samba-audit.log",
    "web2.smb.enabled": False,
    "web2.mysql.enabled": False,
    "web2.mysql.port": 3306,
    "web2.mysql.banner": "5.5.43-0ubuntu0.14.04.1",
    "web2.mysql.log_connection_made": False,
    "web2.ssh.enabled": True if platform_system == "linux" else False,
    "web2.ssh.port": 2222,
    "web2.ssh.version": "SSH-2.0-OpenSSH_5.1p1 Debian-4",
    "web2.redis.enabled": False,
    "web2.redis.port": 6379,
    "web2.rdp.enabled": False,
    "web2.rdp.port": 3389,
    "web2.sip.enabled": False,
    "web2.sip.port": 5060,
    "web2.snmp.enabled": False,
    "web2.snmp.port": 161,
    "web2.ntp.enabled": False,
    "web2.ntp.port": 123,
    "web2.tftp.enabled": False,
    "web2.tftp.port": 69,
    "web2.tcpbanner.maxnum":10,
    "web2.tcpbanner.enabled": False,
    "web2.tcpbanner_1.enabled": False,
    "web2.tcpbanner_1.port": 8001,
    "web2.tcpbanner_1.datareceivedbanner": "",
    "web2.tcpbanner_1.initbanner": "",
    "web2.tcpbanner_1.alertstring.enabled": False,
    "web2.tcpbanner_1.alertstring": "",
    "web2.tcpbanner_1.keep_alive.enabled": False,
    "web2.tcpbanner_1.keep_alive_secret": "",
    "web2.tcpbanner_1.keep_alive_probes": 11,
    "web2.tcpbanner_1.keep_alive_interval":300,
    "web2.tcpbanner_1.keep_alive_idle": 300,
    "web2.telnet.enabled": False,
    "web2.telnet.port": 23,
    "web2.telnet.banner": "",
    "web2.telnet.honeycreds": [
        {
            "username": "admin",
            "password": "$pbkdf2-sha512$19000$bG1NaY3xvjdGyBlj7N37Xw$dGrmBqqWa1okTCpN3QEmeo9j5DuV2u1EuVFD8Di0GxNiM64To5O/Y66f7UASvnQr8.LCzqTm6awC8Kj/aGKvwA"
        },
        {
            "username": "admin",
            "password": "admin1"
        }
    ],
    "web2.telnet.log_tcp_connection": False,
    "web2.mssql.enabled": False,
    "web2.mssql.version": "2012",
    "web2.mssql.port":1433,
    "web2.vnc.enabled": False,
    "web2.vnc.port":5000,
    
    # Web3 Services
    "web3.rpc_node.enabled": False,
    "web3.rpc_node.port": 8545,
    "web3.rpc_node.chain_id": 56,  # BSC
    "web3.rpc_node.network_name": "Binance Smart Chain",
    
    "web3.wallet_service.enabled": False,
    "web3.wallet_service.port": 8546,
    "web3.wallet_service.api_version": "v1",
    
    "web3.ipfs_gateway.enabled": False,
    "web3.ipfs_gateway.port": 8081,
    "web3.ipfs_gateway.api_port": 5001,
    
    "web3.explorer_api.enabled": False,
    "web3.explorer_api.port": 8547,
    "web3.explorer_api.rate_limit": 5,  # requests per second
    
    "web3.defi_protocol.enabled": False,
    "web3.defi_protocol.port": 8548,
    "web3.defi_protocol.protocol_type": "dex",  # dex, lending, staking
    
    "web3.nft_marketplace.enabled": False,
    "web3.nft_marketplace.port": 8549
}


logger = logging.getLogger(__name__)

def generate_config():
    config_file = PATH_CONFIG_OPENCANARY
    if os.path.exists(config_file):
        return
    with open(config_file, "w", encoding="utf-8") as file_config:
        json.dump(config_data, file_config, ensure_ascii=False, indent=4)

def get_config():
    if not os.path.exists(PATH_CONFIG_OPENCANARY):
        print("Configuration file not exists.")
        return False
    with open(PATH_CONFIG_OPENCANARY, 'r') as f:
        return json.load(f)

def get_full_service_key(service):
    """Helper to add prefix if needed"""
    web2_services = ['git', 'ftp', 'http', 'https', 'httpproxy', 'llmnr', 'portscan', 'smb', 'mysql', 'ssh',
                     'redis', 'rdp', 'sip', 'snmp', 'ntp', 'tftp', 'tcpbanner', 'telnet', 'mssql', 'vnc']
    service_lower = service.lower()
    
    # Check if it's a known web2 service without prefix
    if service_lower in web2_services:
        return f"web2.{service_lower}"
        
    # Check if it's tcpbanner sub-service (e.g. tcpbanner_1)
    if 'tcpbanner_' in service_lower and not service_lower.startswith('web2.'):
        return f"web2.{service_lower}"

    return service_lower

def get_config_value(service, configuration):
    try:
        full_service = get_full_service_key(service)
        return get_config()[f"{full_service}.{configuration}"]
    except Exception as e:
        raise Exception('Error getting deceptgold wrapper configuration.')

def toggle_config(service, configuration: str, value):
    """
    Configuration a service in the OpenCanary configuration file.
    Examples:
        toggle_config(service_name, 'enabled', False)
        toggle_config(service_name, 'port', new_port)
    """
    try:
        config = get_config()
        full_service = get_full_service_key(service)
        config[f"{full_service}.{configuration}"] = value
        with open(PATH_CONFIG_OPENCANARY, 'w') as f:
            json.dump(config, f, indent=4)
        return True
    except Exception as e:
        raise Exception(f'Error setting deceptgold wrapper configuration. {e}')




generate_config()
