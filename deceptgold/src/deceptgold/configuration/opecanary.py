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
    "git.enabled": False,
    "git.port" : 9418,
    "ftp.enabled": True,
    "ftp.port": 2121,
    "ftp.banner": "FTP server ready",
    "ftp.log_auth_attempt_initiated": False,
    "http.banner": "Apache/2.2.22 (Ubuntu)",
    "http.enabled": True,
    "http.port": 8090,
    "http.skin": "nasLogin",
    "http.log_unimplemented_method_requests": False,
    "http.log_redirect_request": False,
    "https.enabled": False,
    "https.port": 443,
    "https.skin": "nasLogin",
    "https.certificate": "/etc/ssl/opencanary/opencanary.pem",
    "https.key": "/etc/ssl/opencanary/opencanary.key",
    "httpproxy.enabled" : False,
    "httpproxy.port": 8080,
    "httpproxy.skin": "squid",
    "llmnr.enabled": False,
    "llmnr.query_interval": 60,
    "llmnr.query_splay": 5,
    "llmnr.hostname": "DC03",
    "llmnr.port": 5355,
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
    "portscan.enabled": False,
    "portscan.ignore_localhost": False,
    "portscan.logfile":"/var/log/kern.log",
    "portscan.synrate": 5,
    "portscan.nmaposrate": 5,
    "portscan.lorate": 3,
    "portscan.ignore_ports": [ ],
    "smb.auditfile": "/var/log/samba-audit.log",
    "smb.enabled": False,
    "mysql.enabled": False,
    "mysql.port": 3306,
    "mysql.banner": "5.5.43-0ubuntu0.14.04.1",
    "mysql.log_connection_made": False,
    "ssh.enabled": True if platform_system == "linux" else False,
    "ssh.port": 2222,
    "ssh.version": "SSH-2.0-OpenSSH_5.1p1 Debian-4",
    "redis.enabled": False,
    "redis.port": 6379,
    "rdp.enabled": False,
    "rdp.port": 3389,
    "sip.enabled": False,
    "sip.port": 5060,
    "snmp.enabled": False,
    "snmp.port": 161,
    "ntp.enabled": False,
    "ntp.port": 123,
    "tftp.enabled": False,
    "tftp.port": 69,
    "tcpbanner.maxnum":10,
    "tcpbanner.enabled": False,
    "tcpbanner_1.enabled": False,
    "tcpbanner_1.port": 8001,
    "tcpbanner_1.datareceivedbanner": "",
    "tcpbanner_1.initbanner": "",
    "tcpbanner_1.alertstring.enabled": False,
    "tcpbanner_1.alertstring": "",
    "tcpbanner_1.keep_alive.enabled": False,
    "tcpbanner_1.keep_alive_secret": "",
    "tcpbanner_1.keep_alive_probes": 11,
    "tcpbanner_1.keep_alive_interval":300,
    "tcpbanner_1.keep_alive_idle": 300,
    "telnet.enabled": False,
    "telnet.port": 23,
    "telnet.banner": "",
    "telnet.honeycreds": [
        {
            "username": "admin",
            "password": "$pbkdf2-sha512$19000$bG1NaY3xvjdGyBlj7N37Xw$dGrmBqqWa1okTCpN3QEmeo9j5DuV2u1EuVFD8Di0GxNiM64To5O/Y66f7UASvnQr8.LCzqTm6awC8Kj/aGKvwA"
        },
        {
            "username": "admin",
            "password": "admin1"
        }
    ],
    "telnet.log_tcp_connection": False,
    "mssql.enabled": False,
    "mssql.version": "2012",
    "mssql.port":1433,
    "vnc.enabled": False,
    "vnc.port":5000
}


logger = logging.getLogger(__name__)

def generate_config():
    config_file = PATH_CONFIG_OPENCANARY

    if os.path.exists(config_file):
        return

    with open(config_file, "w", encoding="utf-8") as file_config:
        json.dump(config_data, file_config, ensure_ascii=False, indent=4)


def toggle_service(service_name: str, enable: bool):
    """
    Enables or disables a service in the OpenCanary configuration file.
    """
    try:
        service_name = service_name.lower()

        if not os.path.exists(PATH_CONFIG_OPENCANARY):
            print("Configuration file not exists.")
            return

        with open(PATH_CONFIG_OPENCANARY, 'r') as f:
            config = json.load(f)

        enabled_key = f"{service_name}.enabled"

        if enabled_key not in config:
            print(f"The service '{service_name}' not exists.")
            return

        config[enabled_key] = enable

        with open(PATH_CONFIG_OPENCANARY, 'w') as f:
            json.dump(config, f, indent=4)
        return True
    except Exception:
        return False



generate_config()