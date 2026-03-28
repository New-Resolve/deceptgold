#!/usr/bin/env python3
"""
Web server for the Deceptgold dashboard.
Serves the HTML page and provides a real-time data API.
"""

import json
import os
import secrets
import socket
import signal
import subprocess
import sys
from datetime import datetime
from pathlib import Path
import socketserver
from cyclopts import App
import qrcode_terminal

from deceptgold.commands.dashboard_handler import DashboardHandler, set_dashboard_token

DEFAULT_HOST = "0.0.0.0"
RUNTIME_DIR = Path("/tmp/deceptgold_dashboard")
PID_FILE = RUNTIME_DIR / "dashboard.pid"
STATE_FILE = RUNTIME_DIR / "dashboard_state.json"
dashboard_app = App(name="dashboard", help="Dashboard commands")


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """TCP server with threading support."""
    allow_reuse_address = True
    daemon_threads = True


def _ensure_runtime_dir():
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)


def _read_pid():
    try:
        return int(PID_FILE.read_text(encoding="utf-8").strip())
    except Exception:
        return None


def _is_process_running(pid):
    if not pid:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _is_port_in_use(host, port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.5)
            return sock.connect_ex((_resolve_display_host(host), port)) == 0
    except OSError:
        return False


def _find_high_random_port(host):
    for _ in range(100):
        candidate = secrets.randbelow(9999) + 55000
        if not _is_port_in_use(host, candidate):
            return candidate
    raise RuntimeError("Unable to allocate a high random port for the dashboard")


def _write_runtime_state(pid, host, port, token):
    _ensure_runtime_dir()
    started_at = datetime.now().isoformat()
    PID_FILE.write_text(str(pid), encoding="utf-8")
    STATE_FILE.write_text(
        json.dumps(
            {
                "pid": pid,
                "host": host,
                "port": port,
                "token": token,
                "url": _build_access_url(host, port, token),
                "started_at": started_at,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def _read_runtime_state():
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return None


def _format_uptime(started_at):
    if not started_at:
        return "unknown"
    try:
        started = datetime.fromisoformat(started_at)
        delta = datetime.now() - started
        total_seconds = int(delta.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        if minutes > 0:
            return f"{minutes}m {seconds}s"
        return f"{seconds}s"
    except Exception:
        return "unknown"


def _clear_runtime_state():
    for path in (PID_FILE, STATE_FILE):
        try:
            if path.exists():
                path.unlink()
        except OSError:
            pass


def _resolve_display_host(host):
    if host not in {"0.0.0.0", "::"}:
        return host
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
    except Exception:
        return "127.0.0.1"


def _resolve_internal_bind_host():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            candidate = sock.getsockname()[0]
        import ipaddress
        if ipaddress.ip_address(candidate).is_private:
            return candidate
    except Exception:
        pass
    return "127.0.0.1"


def _build_access_url(host, port, token=None):
    display_host = _resolve_display_host(host)
    if token:
        return f"http://{display_host}:{port}/?token={token}"
    return f"http://{display_host}:{port}"


def start_dashboard_server(port=8080, host="0.0.0.0", token=None):
    """Start the dashboard server."""
    if token:
        set_dashboard_token(token)
    try:
        with ThreadedTCPServer((host, port), DashboardHandler) as httpd:
            access_url = _build_access_url(host, port, token)
            print("Dashboard started")
            print(f"Static directory: {os.environ.get('DECEPTGOLD_DASHBOARD_DIR', 'default')}")
            if token:
                print(f"Access: {access_url}")
            else:
                generated = secrets.token_urlsafe(24)
                print("Token not configured")
                print(f"Suggested token: {generated}")
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\nDashboard stopped")
        _clear_runtime_state()
    except OSError as e:
        if e.errno == 98:
            print(f"Port {port} is already in use")
        else:
            print(f"Error starting dashboard server: {e}")
    except Exception as e:
        print(f"Unexpected dashboard server error: {e}")


@dashboard_app.command(name="start", help="Start the dashboard server")
def start(public: bool = False, port: int = 0):
    host = DEFAULT_HOST if public else _resolve_internal_bind_host()
    running_pid = _read_pid()
    if _is_process_running(running_pid):
        print("Dashboard is already running")
        return

    selected_port = port or _find_high_random_port(host)

    if _is_port_in_use(host, selected_port):
        print(f"Dashboard port {selected_port} is already in use")
        return

    token = secrets.token_urlsafe(24)
    access_url = _build_access_url(host, selected_port, token)

    child_args = [
        sys.executable,
        "-c",
        f"from deceptgold.commands.dashboard import main; main(['--host', '{host}', '--port', '{selected_port}', '--token', '{token}'])",
    ]
    
    log_file = RUNTIME_DIR / "dashboard.log"
    _ensure_runtime_dir()
    
    with open(log_file, 'w') as log:
        process = subprocess.Popen(
            child_args,
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    if process.poll() is not None:
        print("Failed to start dashboard")
        print(f"Check logs at: {log_file}")
        return
    _write_runtime_state(process.pid, host, selected_port, token)

    print("Dashboard started")
    print(f"Mode: {'public' if public else 'internal'}")
    print(f"Access: {access_url}")
    print(f"Logs: {log_file}")
    qrcode_terminal.draw(access_url)


@dashboard_app.command(name="stop", help="Stop the internal dashboard server")
def stop():
    pid = _read_pid()
    if not _is_process_running(pid):
        _clear_runtime_state()
        print("Dashboard is not running")
        return

    try:
        os.kill(pid, signal.SIGTERM)
    except OSError:
        pass

    _clear_runtime_state()
    print("Dashboard stopped")


@dashboard_app.command(name="status", help="Show dashboard runtime status")
def status():
    state = _read_runtime_state()
    pid = _read_pid()

    if not state or not _is_process_running(pid):
        _clear_runtime_state()
        print("Dashboard is not running")
        return

    url = state.get("url")
    host = state.get("host", DEFAULT_HOST)
    port = state.get("port")
    started_at = state.get("started_at")
    token = state.get("token", "")

    print("Dashboard status")
    print(f"Running: yes")
    print(f"PID: {pid}")
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"Uptime: {_format_uptime(started_at)}")
    print(f"Token length: {len(token)}")
    print(f"Access: {url}")
    qrcode_terminal.draw(url)


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    port = 0
    host = DEFAULT_HOST
    token = None

    if len(argv) > 0:
        for i, arg in enumerate(argv):
            if arg == "--port" and i + 1 < len(argv):
                try:
                    port = int(argv[i + 1])
                except ValueError:
                    print("Port must be a number")
                    sys.exit(1)
            if arg == "--host" and i + 1 < len(argv):
                host = argv[i + 1]
            if arg == "--token" and i + 1 < len(argv):
                token = argv[i + 1]

    if not token:
        token = secrets.token_urlsafe(24)

    start_dashboard_server(port, host, token)


if __name__ == "__main__":
    main()
