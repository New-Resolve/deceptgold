import hashlib
import platform
import subprocess
import uuid


def get_disk_serial():
    try:
        if platform.system().lower().strip() == "windows":
            output = subprocess.check_output("wmic diskdrive get serialnumber", shell=True, text=True)
            lines = output.strip().split("\n")
            return lines[1].strip() if len(lines) > 1 else ""
        else:
            output = subprocess.check_output("lsblk -o NAME,SERIAL", shell=True, text=True)
            lines = output.strip().split("\n")
            for line in lines[1:]:
                parts = line.strip().split()
                if len(parts) == 2 and parts[1] != "":
                    return parts[1]
            return ""
    except Exception as e:
        return ""


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
