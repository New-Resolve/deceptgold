import hashlib
import platform
import subprocess
import uuid
import re
import os

def get_cmd_windows_wmic():
    try:
        output = subprocess.check_output("wmic diskdrive get serialnumber", shell=True, text=True)
        lines = [line.strip() for line in output.strip().split("\n") if line.strip()]
        if len(lines) > 1 and lines[1]:
            return lines[1]
    except Exception:
        pass

def get_cmd_windows_powershell():
    try:
        ps_command = "Get-WmiObject win32_physicalmedia | Select-Object -ExpandProperty SerialNumber"
        output = subprocess.check_output(["powershell", "-Command", ps_command], text=True)
        lines = [line.strip() for line in output.strip().split("\n") if line.strip()]
        if lines and lines[0]:
            return lines[0]
    except Exception:
        pass


def get_cmd_windows_cmd():
    try:
        output = subprocess.check_output("vol C:", shell=True, text=True)
        match = re.search(
            r"(?:número de série do volume é|"
            r"volume serial number is|"
            r"el número de serie del volumen es|"
            r"numéro de série du volume est|"
            r"seriennummer des datenträgers ist|"
            r"numero di serie del volume è)"
            r"[\s:]+([A-Z0-9\-]+)",
            output,
            re.IGNORECASE
        )
        if match:
            return match.group(1)
    except Exception:
        pass


def get_cmd_linux_lsblk():
    try:
        output = subprocess.check_output("lsblk -o NAME,SERIAL", shell=True, text=True)
        lines = output.strip().split("\n")
        for line in lines[1:]:
            parts = line.strip().split()
            if len(parts) == 2 and parts[1] != "":
                return parts[1]
    except Exception:
        pass

def get_cmd_linux_disk():
    try:
        if os.path.exists("/dev/disk/by-id"):
            for name in os.listdir("/dev/disk/by-id"):
                if name.startswith("nvme-") or name.startswith("ata-"):
                    # tenta extrair serial com regex
                    match = re.search(r"_([A-Z0-9]{8,})", name)
                    if match:
                        return match.group(1)
                    else:
                        # se regex falhar, retorna o nome mesmo
                        return name
    except Exception:
        pass

def get_cmd_linux_block():
    try:
        for device in os.listdir("/sys/block"):
            if re.match(r"(sd[a-z]|nvme\d+n\d+)$", device):
                path = f"/sys/block/{device}/device/serial"
                if os.path.isfile(path):
                    with open(path, "r") as f:
                        serial = f.read().strip()
                        if serial:
                            return serial
    except Exception:
        pass



def get_disk_serial():
    try:
        system = platform.system().strip().lower()

        windows_cmds = [
            get_cmd_windows_wmic,
            get_cmd_windows_powershell,
            get_cmd_windows_cmd
        ]

        linux_cmds = [
            get_cmd_linux_lsblk,
            get_cmd_linux_disk,
            get_cmd_linux_block
        ]

        if system == "windows":
            for cmd_func in windows_cmds:
                result = cmd_func()
                if result:
                    return result

        elif system == "linux":
            for cmd_func in linux_cmds:
                result = cmd_func()
                if result:
                    return result

        return ""

    except Exception as e:
        return f"Erro geral: {e}"


def get_mac():
    try:
        mac = hex(uuid.getnode()).replace("0x", "").zfill(12)
        return mac
    except Exception as e:
        return ""


def get_machine_fingerprint():
    raw_string = f"{get_disk_serial()}-{get_mac()}".encode("utf-8")
    fingerprint = hashlib.sha256(raw_string).hexdigest()
    return fingerprint
