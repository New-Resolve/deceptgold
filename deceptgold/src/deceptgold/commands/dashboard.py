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
import ipaddress
import threading
import time
from datetime import datetime, timedelta, timezone
from collections import Counter, defaultdict
from http.cookies import SimpleCookie
from http.server import SimpleHTTPRequestHandler
from importlib.resources import files
from pathlib import Path
from urllib import error as urllib_error, request as urllib_request
from urllib.parse import urlparse, parse_qs
import socketserver
from cyclopts import App
import qrcode_terminal

from deceptgold.helper.ai_model import list_installed_models

DASHBOARD_DIRECTORY = os.environ.get("DECEPTGOLD_DASHBOARD_DIR") or str(files("deceptgold.resources").joinpath("dashboard"))
DASHBOARD_TOKEN = os.environ.get("DECEPTGOLD_DASHBOARD_TOKEN")
DEFAULT_HOST = "0.0.0.0"
RUNTIME_DIR = Path("/tmp/deceptgold_dashboard")
PID_FILE = RUNTIME_DIR / "dashboard.pid"
STATE_FILE = RUNTIME_DIR / "dashboard_state.json"
GEO_CACHE_FILE = RUNTIME_DIR / "geo_cache.json"
GEO_CACHE_TTL = 60 * 60 * 24 * 14  # 14 days
MAX_GEO_CACHE_SIZE = 2000
MAX_GEO_LOOKUPS_PER_REQUEST = 200
PUBLIC_IP_CACHE_TTL = 60 * 10  # 10 minutes
_geo_cache = {}
_geo_cache_loaded = False
_geo_cache_lock = threading.Lock()
_public_ip_cache = {'ip': None, 'cached_at': 0}
_public_ip_lock = threading.Lock()
dashboard_app = App(name="dashboard", help="Dashboard commands")


def _load_geo_cache():
    global _geo_cache_loaded, _geo_cache
    if _geo_cache_loaded:
        return
    with _geo_cache_lock:
        if _geo_cache_loaded:
            return
        _ensure_runtime_dir()
        if GEO_CACHE_FILE.exists():
            try:
                _geo_cache = json.loads(GEO_CACHE_FILE.read_text(encoding="utf-8"))
            except Exception:
                _geo_cache = {}
        _geo_cache_loaded = True


def _save_geo_cache_locked():
    try:
        _ensure_runtime_dir()
        GEO_CACHE_FILE.write_text(json.dumps(_geo_cache, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


def _prune_geo_cache_locked():
    if len(_geo_cache) <= MAX_GEO_CACHE_SIZE:
        return
    excess = len(_geo_cache) - MAX_GEO_CACHE_SIZE
    oldest = sorted(_geo_cache.items(), key=lambda item: item[1].get('cached_at', 0))
    for i in range(excess):
        key, _ = oldest[i]
        _geo_cache.pop(key, None)


def _extract_ip(src_host):
    if not src_host:
        return None
    host = str(src_host).strip()
    if host.startswith('[') and ']' in host:
        closing = host.find(']')
        host = host[1:closing]
    elif ':' in host and host.count(':') == 1 and '.' in host:
        host = host.split(':', 1)[0]
    return host or None


def _extract_forwarded_ip(event):
    """Attempt to recover the original client IP from proxy headers/log fields."""
    if not isinstance(event, dict):
        return None

    candidate_values = []
    direct_candidates = [
        event.get('remote_ip'),
        event.get('remote_addr'),
        event.get('real_ip'),
    ]

    details = event.get('details')
    if isinstance(details, dict):
        direct_candidates.extend(
            details.get(key)
            for key in ('remote_ip', 'real_ip', 'forwarded_for', 'forwarded')
        )

    logdata = event.get('logdata')
    if isinstance(logdata, dict):
        header_keys = (
            'X-Forwarded-For',
            'X_FORWARDED_FOR',
            'X-Real-IP',
            'X_REAL_IP',
            'FORWARDED',
            'FORWARDED_FOR',
            'CLIENT_IP',
            'REMOTE_ADDR',
        )
        direct_candidates.extend(logdata.get(key) for key in header_keys)

        # Some log entries may embed raw headers or metadata as a blob
        for blob_key in ('HEADERS', 'RAW_HEADERS', 'headers', 'raw_headers'):
            blob = logdata.get(blob_key)
            if isinstance(blob, dict):
                for key, value in blob.items():
                    if key:
                        direct_candidates.append(value)
            elif isinstance(blob, str):
                for line in blob.splitlines():
                    if ':' not in line:
                        continue
                    key, value = line.split(':', 1)
                    if key.strip().lower() in {
                        'x-forwarded-for',
                        'x-real-ip',
                        'client-ip',
                        'forwarded',
                    }:
                        direct_candidates.append(value)

    candidate_values.extend(filter(None, direct_candidates))

    for candidate in candidate_values:
        text = str(candidate).strip()
        if not text:
            continue
        first_segment = text.split(',', 1)[0].strip()
        if not first_segment:
            continue
        ip_text = _extract_ip(first_segment)
        if not ip_text:
            continue
        try:
            ipaddress.ip_address(ip_text)
        except ValueError:
            continue
        return ip_text

    return None


def _should_skip_geo(ip_obj):
    return (
        ip_obj.is_private
        or ip_obj.is_loopback
        or ip_obj.is_reserved
        or ip_obj.is_multicast
        or ip_obj.is_unspecified
    )


def _normalize_geo_payload(data, ip):
    if not isinstance(data, dict):
        return None
    lat = data.get('lat') if data.get('lat') is not None else data.get('latitude')
    lon = data.get('lon') if data.get('lon') is not None else data.get('longitude')
    if lat is None or lon is None:
        return None
    return {
        'ip': data.get('query') or data.get('ip') or ip,
        'name': data.get('country') or data.get('country_name') or 'Unknown',
        'code': ((data.get('countryCode') or data.get('country_code') or '').upper()),
        'region': data.get('regionName') or data.get('region') or '',
        'city': data.get('city') or '',
        'lat': lat,
        'lon': lon,
    }


def _query_geo_service(ip):
    if os.environ.get("DECEPTGOLD_DISABLE_GEO_LOOKUP") == "1":
        return None
    urls = [
        f"http://ip-api.com/json/{ip}?fields=status,query,country,countryCode,regionName,city,lat,lon",
        f"https://ipwho.is/{ip}",
    ]
    for url in urls:
        try:
            with urllib_request.urlopen(url, timeout=1.8) as response:
                payload = response.read().decode('utf-8')
                data = json.loads(payload)
        except (urllib_error.URLError, TimeoutError, ValueError, json.JSONDecodeError):
            continue

        if url.startswith("http://ip-api.com/"):
            if data.get('status') != 'success':
                continue
        else:
            if data.get('success') is False:
                continue

        normalized = _normalize_geo_payload(data, ip)
        if normalized:
            return normalized
    return None


def _lookup_geo_info(src_host, lookup_state):
    ip_text = _extract_ip(src_host)
    if not ip_text:
        return None
    try:
        ip_obj = ipaddress.ip_address(ip_text)
    except ValueError:
        return None
    if _should_skip_geo(ip_obj):
        return None

    _load_geo_cache()
    cached = _geo_cache.get(ip_text)
    now = time.time()
    if cached and (now - cached.get('cached_at', 0)) < GEO_CACHE_TTL:
        return cached

    if lookup_state is not None and lookup_state.get('remaining', 0) <= 0:
        return cached

    geo_data = _query_geo_service(ip_text)
    if geo_data:
        entry = {**geo_data, 'cached_at': now}
        with _geo_cache_lock:
            _geo_cache[ip_text] = entry
            _prune_geo_cache_locked()
            _save_geo_cache_locked()
        if lookup_state is not None:
            lookup_state['remaining'] = max(lookup_state.get('remaining', 0) - 1, 0)
        return entry

    return cached


def _seed_geo_cache_from_log(max_events=400):
    """Warm the GeoIP cache using historical events so map markers persist after restarts."""
    log_path = "/tmp/.deceptgold.log"
    if not os.path.exists(log_path):
        return

    try:
        seen_ips = set()
        lookup_state = {'remaining': MAX_GEO_LOOKUPS_PER_REQUEST}

        with open(log_path, 'r', encoding='utf-8') as handle:
            for line in handle:
                if lookup_state['remaining'] <= 0 or len(seen_ips) >= max_events:
                    break

                line = line.strip()
                if not line or line.startswith('llama_context') or line.startswith('[!]'):
                    continue

                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue

                if not isinstance(event, dict):
                    continue

                src_candidates = [event.get('src_host')]

                details = event.get('details')
                if isinstance(details, dict):
                    src_candidates.append(details.get('src_host'))

                logdata = event.get('logdata') if isinstance(event.get('logdata'), dict) else {}
                for key in ('src_host', 'SRC', 'ip', 'IP', 'REMOTE_ADDR', 'remote_ip'):
                    value = logdata.get(key)
                    if value:
                        src_candidates.append(value)

                for candidate in src_candidates:
                    ip_text = _extract_ip(candidate)
                    if not ip_text or ip_text in seen_ips:
                        continue
                    try:
                        ip_obj = ipaddress.ip_address(ip_text)
                    except ValueError:
                        continue
                    if _should_skip_geo(ip_obj):
                        continue

                    seen_ips.add(ip_text)
                    _lookup_geo_info(ip_text, lookup_state)
                    if lookup_state['remaining'] <= 0:
                        break

    except (OSError, IOError):
        return


def _hour_series(counter):
    return [counter.get(hour, 0) for hour in range(24)]


def _is_loopback_source(src_host):
    if not src_host:
        return False
    host_text = str(src_host).strip().lower()
    if host_text in {'localhost', '::1', '[::1]'}:
        return True
    ip_text = _extract_ip(src_host)
    if not ip_text:
        return False
    try:
        return ipaddress.ip_address(ip_text).is_loopback
    except ValueError:
        return False


def _normalize_public_ip(candidate):
    if not candidate:
        return None
    text = str(candidate).strip()
    if not text:
        return None
    try:
        ip_obj = ipaddress.ip_address(text)
    except ValueError:
        return None
    if _should_skip_geo(ip_obj):
        return None
    return str(ip_obj)


def _get_machine_public_ip():
    if os.environ.get("DECEPTGOLD_DISABLE_GEO_LOOKUP") == "1":
        return None

    now = time.time()
    with _public_ip_lock:
        cached_ip = _public_ip_cache.get('ip')
        cached_at = _public_ip_cache.get('cached_at', 0)
        if cached_ip and (now - cached_at) < PUBLIC_IP_CACHE_TTL:
            return cached_ip

    sources = [
        ("https://api.ipify.org?format=json", "json", "ip"),
        ("https://ifconfig.me/ip", "text", None),
        ("https://icanhazip.com", "text", None),
    ]

    for url, mode, key in sources:
        try:
            with urllib_request.urlopen(url, timeout=1.5) as response:
                payload = response.read().decode('utf-8').strip()
        except (urllib_error.URLError, TimeoutError, ValueError):
            continue

        value = None
        if mode == "json":
            try:
                parsed = json.loads(payload)
                value = parsed.get(key) if isinstance(parsed, dict) else None
            except (ValueError, json.JSONDecodeError):
                value = None
        else:
            value = payload.splitlines()[0] if payload else None

        public_ip = _normalize_public_ip(value)
        if public_ip:
            with _public_ip_lock:
                _public_ip_cache['ip'] = public_ip
                _public_ip_cache['cached_at'] = now
            return public_ip

    return cached_ip if cached_ip else None

class DashboardHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DASHBOARD_DIRECTORY, **kwargs)
    
    def do_GET(self):
        parsed_path = urlparse(self.path)

        if not self.is_authorized(parsed_path):
            self.drop_unauthorized_connection()
            return

        if parsed_path.path == '/api/dashboard-data':
            self.serve_dashboard_data()
        elif parsed_path.path == '/api/ai-report/options':
            self.serve_ai_report_options()
        elif parsed_path.path == '/api/ai-report/directories':
            self.serve_ai_report_directories(parsed_path)
        elif parsed_path.path == '/' or parsed_path.path == '/dashboard':
            self.path = '/dashboard.html'
            super().do_GET()
        else:
            super().do_GET()

    def do_POST(self):
        parsed_path = urlparse(self.path)

        if not self.is_authorized(parsed_path):
            self.drop_unauthorized_connection()
            return

        if parsed_path.path == '/api/ai-report':
            self.handle_ai_report_request()
        else:
            self.send_error(404, "Endpoint not found")

    def is_authorized(self, parsed_path):
        """Validate access using a simple token via query string, header, or cookie."""
        if not DASHBOARD_TOKEN:
            return True

        provided_token = self.extract_token(parsed_path)
        if provided_token == DASHBOARD_TOKEN:
            self._authenticated_by_token = True
            return True

        cookie_header = self.headers.get('Cookie')
        if cookie_header:
            cookie = SimpleCookie()
            cookie.load(cookie_header)
            session_cookie = cookie.get('dg_dashboard_token')
            if session_cookie and session_cookie.value == DASHBOARD_TOKEN:
                self._authenticated_by_token = False
                return True

        return False

    def extract_token(self, parsed_path):
        auth_header = self.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            return auth_header.split(' ', 1)[1].strip()

        token_header = self.headers.get('X-Dashboard-Token')
        if token_header:
            return token_header.strip()

        query_params = parse_qs(parsed_path.query)
        return query_params.get('token', [None])[0]

    def drop_unauthorized_connection(self):
        self.close_connection = True
        try:
            self.connection.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        try:
            self.connection.close()
        except OSError:
            pass

    def end_headers(self):
        if getattr(self, '_authenticated_by_token', False):
            cookie = SimpleCookie()
            cookie['dg_dashboard_token'] = DASHBOARD_TOKEN
            cookie['dg_dashboard_token']['path'] = '/'
            cookie['dg_dashboard_token']['httponly'] = True
            cookie['dg_dashboard_token']['samesite'] = 'Strict'
            self.send_header('Set-Cookie', cookie.output(header='').strip())
            self._authenticated_by_token = False
        super().end_headers()
    
    def serve_dashboard_data(self):
        """Serve dashboard data as JSON."""
        try:
            data = self.load_log_data()
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            json_data = json.dumps(data, ensure_ascii=False, indent=2)
            self.wfile.write(json_data.encode('utf-8'))
            
        except Exception as e:
            self.send_error(500, f"Unable to load dashboard data: {str(e)}")

    def serve_ai_report_options(self):
        """Return available formats and installed AI models for report generation."""
        try:
            models = list_installed_models() or []
            normalized = [
                {
                    'key': str(m.get('key') or '').strip(),
                    'label': str(m.get('key') or '').strip(),
                    'description': str(m.get('description') or ''),
                    'specialty': str(m.get('specialty') or ''),
                    'installed': bool(m.get('installed')),
                }
                for m in models
                if m.get('key')
            ]

            default_format = 'pdf'
            payload = {
                'formats': [
                    {'value': 'pdf', 'label': 'PDF (.pdf)'},
                    {'value': 'markdown', 'label': 'Markdown (.md)'},
                ],
                'models': normalized,
                'defaultModel': normalized[0]['key'] if normalized else '',
                'defaultDest': self._build_default_report_path(default_format),
                'defaultFormat': default_format,
                'generatedAt': datetime.now().isoformat(),
            }

            body = json.dumps(payload, ensure_ascii=False)
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(body.encode('utf-8'))
        except Exception as exc:
            self.send_error(500, f"Unable to load AI report options: {exc}")

    def serve_ai_report_directories(self, parsed_path):
        """List directories within the user's home for destination selection."""
        try:
            query = parse_qs(parsed_path.query)
            raw_path = (query.get('path') or [str(Path.home())])[0]

            home_dir = Path.home().resolve()
            candidate = Path(raw_path).expanduser()
            if not candidate.is_absolute():
                candidate = (home_dir / candidate).resolve()
            else:
                candidate = candidate.resolve()

            if not str(candidate).startswith(str(home_dir)):
                candidate = home_dir

            if not candidate.exists() or not candidate.is_dir():
                candidate = home_dir

            entries = []
            try:
                for child in sorted(candidate.iterdir(), key=lambda p: p.name.lower()):
                    if not child.is_dir():
                        continue
                    has_children = False
                    try:
                        for sub in child.iterdir():
                            if sub.is_dir():
                                has_children = True
                                break
                    except PermissionError:
                        has_children = False

                    entries.append({
                        'name': child.name,
                        'path': str(child),
                        'hasChildren': has_children,
                        'selectable': True,
                    })
            except PermissionError:
                entries = []

            payload = {
                'path': str(candidate),
                'parent': str(candidate.parent) if candidate != home_dir else None,
                'isHome': candidate == home_dir,
                'entries': entries,
            }

            body = json.dumps(payload, ensure_ascii=False)
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(body.encode('utf-8'))
        except Exception as exc:
            self.send_error(500, f"Unable to list directories: {exc}")

    def handle_ai_report_request(self):
        """Execute the AI report command based on POSTed options."""
        import tempfile
        import base64
        
        try:
            length = int(self.headers.get('Content-Length', 0))
        except (TypeError, ValueError):
            length = 0

        raw_body = b''
        if length > 0:
            raw_body = self.rfile.read(length)

        try:
            payload = json.loads(raw_body.decode('utf-8') or '{}')
        except (UnicodeDecodeError, json.JSONDecodeError):
            self.send_error(400, 'Invalid JSON payload')
            return

        fmt = str(payload.get('format') or '').strip().lower()
        model_key = str(payload.get('model') or '').strip()

        if fmt not in {'markdown', 'pdf'}:
            self.send_error(400, "Format must be 'markdown' or 'pdf'")
            return

        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        extension = '.md' if fmt == 'markdown' else '.pdf'
        filename = f'deceptgold-report-{timestamp}{extension}'
        
        with tempfile.TemporaryDirectory() as tmpdir:
            dest_path = Path(tmpdir) / filename

            command = [
                sys.executable,
                '-m',
                'deceptgold',
                'reports',
                'ai-report',
                f'dest={str(dest_path)}',
                f'format={fmt}',
            ]

            if model_key:
                command.append(f'model={model_key}')

            env = os.environ.copy()
            env.setdefault('PYTHONUNBUFFERED', '1')

            try:
                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    check=False,
                    env=env,
                )
            except Exception as exc:
                self.send_error(500, f"Failed to execute report command: {exc}")
                return

            success = result.returncode == 0
            combined_output = "\n".join(
                [segment for segment in (result.stdout, result.stderr) if segment]
            ).strip()

            file_content = None
            if success and dest_path.exists():
                try:
                    with open(dest_path, 'rb') as f:
                        file_content = base64.b64encode(f.read()).decode('utf-8')
                except Exception as e:
                    success = False
                    combined_output += f"\nFailed to read generated file: {e}"

            response_body = json.dumps(
                {
                    'success': success,
                    'filename': filename,
                    'format': fmt,
                    'model': model_key,
                    'output': combined_output,
                    'fileContent': file_content,
                },
                ensure_ascii=False,
            )

            status_code = 200 if success else 422
            self.send_response(status_code)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(response_body.encode('utf-8'))

    def _build_default_report_path(self, fmt):
        base_dir = Path.home() / 'deceptgold-reports'
        base_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        extension = '.md' if fmt == 'markdown' else '.pdf'
        filename = f'deceptgold-report-{timestamp}{extension}'
        return str(base_dir / filename)
    
    def load_log_data(self):
        """Load and analyze data from the log file."""
        log_path = "/tmp/.deceptgold.log"

        if not os.path.exists(log_path):
            return self.get_default_data()

        _load_geo_cache()
        _seed_geo_cache_from_log()

        try:
            events_iter = self._iter_log_events(log_path)
            return self.analyze_events(events_iter)
        except Exception as e:
            print(f"Error reading log file: {e}")
            return self.get_default_data()

    def _iter_log_events(self, log_path):
        with open(log_path, 'r', encoding='utf-8') as handle:
            for line in handle:
                line = line.strip()
                if not line or line.startswith('llama_context') or line.startswith('[!]'):
                    continue

                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue

                if isinstance(event, dict):
                    yield event
    
    def analyze_events(self, events_iter):
        """Analyze events dynamically based on the JSON structure."""
        analysis = {
            'totalEvents': 0,
            'connectionEvents': 0,
            'loginAttempts': 0,
            'uniqueIPs': 0,
            'hourlyActivity': defaultdict(int),
            'hourlyActivityWindow': {'labels': [], 'values': []},
            'hourlyServiceActivity': {'labels': [], 'series': {}},
            'logtypeCounts': Counter(),
            'attackCounts': Counter(),
            'attackSeverityDistribution': {},
            'severityCounts': Counter(),
            'serviceCounts': Counter(),
            'countryCounts': Counter(),
            'countryHourlyActivity': defaultdict(lambda: defaultdict(int)),
            'countryRolling12h': {'labels': [], 'series': {}},
            'countryLocations': {},
            'geoPoints': {},
            'recentIncidents': [],
            'httpCredentialAttempts': [],
            'portCountryDistribution': {
                'ports': [],
                'series': {}
            }
        }
        
        src_hosts = set()
        lookup_state = {'remaining': MAX_GEO_LOOKUPS_PER_REQUEST}
        request_geo_cache = {}
        now_local = datetime.now().astimezone()
        rolling_window_end = now_local
        hourly_window_start = rolling_window_end - timedelta(hours=24)
        rolling_window_start = rolling_window_end - timedelta(hours=12)
        current_hour_start = now_local.replace(minute=0, second=0, microsecond=0)
        rolling24_window_end = current_hour_start + timedelta(hours=1)
        rolling24_window_start = rolling24_window_end - timedelta(hours=24)
        hourly_labels = [
            (hourly_window_start + timedelta(hours=i)).strftime('%d/%m %Hh')
            for i in range(24)
        ]
        rolling_hourly_activity = [0] * 24
        hourly_service_activity = defaultdict(lambda: [0] * 24)
        rolling_labels = [
            (rolling_window_start + timedelta(hours=i)).strftime('%d/%m %Hh')
            for i in range(12)
        ]
        rolling_country_activity = defaultdict(lambda: [0] * 12)
        rolling24_country_activity = defaultdict(lambda: [0] * 24)
        rolling24_labels = []
        attack_severity_buckets = defaultdict(lambda: Counter())
        port_country_counter = defaultdict(lambda: Counter())
        http_credentials_counter = Counter()
        for i in range(24):
            ts = rolling24_window_start + timedelta(hours=i)
            label = ts.strftime('%d/%m %Hh')
            if ts == current_hour_start:
                label += ' (agora)'
            rolling24_labels.append(label)

        def resolve_event_src_host(event):
            forwarded_ip = _extract_forwarded_ip(event)
            if forwarded_ip:
                return forwarded_ip

            primary_src = event.get('src_host')
            details = event.get('details')
            details_src = details.get('src_host') if isinstance(details, dict) else None

            primary_ip = _extract_ip(primary_src)
            details_ip = _extract_ip(details_src)

            if primary_ip and details_ip:
                try:
                    primary_obj = ipaddress.ip_address(primary_ip)
                    details_obj = ipaddress.ip_address(details_ip)
                    if _should_skip_geo(primary_obj) and not _should_skip_geo(details_obj):
                        return details_src
                except ValueError:
                    pass

            selected_src = primary_src or details_src
            if _is_loopback_source(selected_src):
                if forwarded_ip:
                    return forwarded_ip
                machine_public_ip = _get_machine_public_ip()
                if machine_public_ip:
                    return machine_public_ip
            return selected_src

        def resolve_geo(src_host):
            ip_text = _extract_ip(src_host)
            if not ip_text:
                return None
            if ip_text in request_geo_cache:
                return request_geo_cache[ip_text]
            geo_info = _lookup_geo_info(ip_text, lookup_state)
            request_geo_cache[ip_text] = geo_info
            return geo_info
        
        for event in events_iter:
            if not isinstance(event, dict):
                continue
            analysis['totalEvents'] += 1
            event_country_name = None
                
            logtype = event.get('logtype')
            if logtype is not None:
                logtype_category = self.categorize_logtype(logtype, event)
                analysis['logtypeCounts'][logtype_category] += 1
            
            attack_info = self.detect_attack_type(event)
            attack_type = attack_info['type'] or 'Unknown'
            analysis['attackCounts'][attack_type] += 1
            
            if self.is_connection_event(event):
                analysis['connectionEvents'] += 1
            
            if self.is_login_attempt(event):
                analysis['loginAttempts'] += 1
            
            service = self.extract_service_info(event)
            if service:
                analysis['serviceCounts'][service] += 1
            service_label = service or 'Desconhecido'
            logdata = event.get('logdata', {}) if isinstance(event.get('logdata'), dict) else {}
            if logdata and 'http' in service_label.lower():
                username = (
                    logdata.get('USERNAME') or logdata.get('username') or
                    logdata.get('user') or logdata.get('login')
                )
                password = (
                    logdata.get('PASSWORD') or logdata.get('password') or
                    logdata.get('pass') or logdata.get('passwd')
                )
                if username or password:
                    username_label = str(username).strip() if username not in [None, ''] else '(sem usuário)'
                    password_label = str(password).strip() if password not in [None, ''] else '(sem senha)'
                    key = (username_label[:80], password_label[:80])
                    http_credentials_counter[key] += 1
            
            src_host = resolve_event_src_host(event)
            if src_host and src_host not in ['', 'unknown', None]:
                src_hosts.add(src_host)
                geo_info = resolve_geo(src_host)
                if geo_info and geo_info.get('lat') is not None and geo_info.get('lon') is not None:
                    ip_text = _extract_ip(src_host) or src_host
                    country_name = geo_info.get('name') or 'Unknown'
                    event_country_name = country_name
                    country_code = geo_info.get('code') or country_name
                    city_name = geo_info.get('city') or ''
                    region_name = geo_info.get('region') or ''
                    point_label = city_name or region_name or country_name
                    analysis['countryCounts'][country_name] += 1
                    entry = analysis['countryLocations'].setdefault(
                        country_code,
                        {
                            'name': country_name,
                            'code': country_code,
                            'lat': geo_info.get('lat'),
                            'lon': geo_info.get('lon'),
                            'count': 0,
                        }
                    )
                    entry['name'] = country_name
                    entry['lat'] = geo_info.get('lat')
                    entry['lon'] = geo_info.get('lon')
                    entry['count'] += 1

                    geo_key = f"{country_code}:{city_name}:{region_name}:{geo_info.get('lat')}:{geo_info.get('lon')}"
                    point_entry = analysis['geoPoints'].setdefault(
                        geo_key,
                        {
                            'ip': ip_text,
                            'name': point_label,
                            'city': city_name,
                            'region': region_name,
                            'country': country_name,
                            'code': country_code,
                            'lat': geo_info.get('lat'),
                            'lon': geo_info.get('lon'),
                            'count': 0,
                        }
                    )
                    point_entry['count'] += 1
                else:
                    ip_text = _extract_ip(src_host)
                    event_country_name = 'Unknown'
                    if ip_text:
                        try:
                            ip_obj = ipaddress.ip_address(ip_text)
                            if _should_skip_geo(ip_obj):
                                event_country_name = 'Local/Private'
                        except ValueError:
                            event_country_name = 'Unknown'
            
            severity = event.get('severity')
            if severity:
                severity_level = severity
            else:
                severity_level = self.infer_severity(event)

            analysis['severityCounts'][severity_level] += 1
            attack_severity_buckets[attack_type][severity_level] += 1

            port_key = event.get('dst_port') or event.get('port') or event.get('dst_port_number')
            if port_key is None:
                details = event.get('details')
                if isinstance(details, dict):
                    port_key = details.get('dst_port') or details.get('port')
            if port_key is None:
                logdata = event.get('logdata')
                if isinstance(logdata, dict):
                    port_key = logdata.get('port') or logdata.get('dst_port')

            if port_key is not None and event_country_name:
                try:
                    port_int = int(port_key)
                except (TypeError, ValueError):
                    port_int = None

                if port_int is not None:
                    port_country_counter[port_int][event_country_name] += 1
            
            event_dt = self.extract_event_datetime(event)
            hour = event_dt.hour if event_dt is not None else self.extract_event_hour(event)
            if hour is not None:
                analysis['hourlyActivity'][hour] += 1
                if event_country_name:
                    analysis['countryHourlyActivity'][event_country_name][hour] += 1

            if event_dt and hourly_window_start <= event_dt < rolling_window_end:
                hourly_bucket = int((event_dt - hourly_window_start).total_seconds() // 3600)
                if 0 <= hourly_bucket < 24:
                    rolling_hourly_activity[hourly_bucket] += 1
                    hourly_service_activity[service_label][hourly_bucket] += 1

            if event_country_name and event_dt and rolling_window_start <= event_dt < rolling_window_end:
                bucket = int((event_dt - rolling_window_start).total_seconds() // 3600)
                if 0 <= bucket < 12:
                    rolling_country_activity[event_country_name][bucket] += 1
            # 24h rolling window for country trend (for main view)
            if event_country_name and event_dt and rolling24_window_start <= event_dt < rolling24_window_end:
                bucket24 = int((event_dt - rolling24_window_start).total_seconds() // 3600)
                if 0 <= bucket24 < 24:
                    rolling24_country_activity[event_country_name][bucket24] += 1
            
            if len(analysis['recentIncidents']) < 10000:
                incident = self.create_incident_from_event(event, attack_info)
                if incident:
                    analysis['recentIncidents'].append(incident)
        
        analysis['uniqueIPs'] = len(src_hosts)
        
        analysis['hourlyActivity'] = dict(analysis['hourlyActivity'])
        analysis['hourlyActivityWindow'] = {
            'labels': hourly_labels,
            'values': rolling_hourly_activity
        }

        service_entries = []
        for service_name, values in hourly_service_activity.items():
            total = sum(values)
            if total > 0:
                service_entries.append((service_name, values, total))

        if service_entries:
            service_entries.sort(key=lambda item: item[2], reverse=True)
            top_limit = 6
            top_entries = service_entries[:top_limit]

            if len(service_entries) > top_limit:
                outros_values = [0] * 24
                for _, values, _ in service_entries[top_limit:]:
                    for idx, value in enumerate(values):
                        outros_values[idx] += value
                if sum(outros_values) > 0:
                    top_entries.append(('Outros', outros_values, sum(outros_values)))

            analysis['hourlyServiceActivity'] = {
                'labels': hourly_labels,
                'series': {
                    service_name: values
                    for service_name, values, _ in top_entries
                }
            }

        if attack_severity_buckets:
            analysis['attackSeverityDistribution'] = {
                attack: dict(counter)
                for attack, counter in attack_severity_buckets.items()
            }

        if port_country_counter:
            port_entries = []
            for port, country_counts in port_country_counter.items():
                total = sum(country_counts.values())
                if total > 0:
                    port_entries.append((port, country_counts, total))

            if port_entries:
                port_entries.sort(key=lambda item: item[2], reverse=True)
                top_limit = 4
                top_ports = port_entries[:top_limit]

                if len(port_entries) > top_limit:
                    outros_counter = Counter()
                    for _, country_counts, _ in port_entries[top_limit:]:
                        outros_counter.update(country_counts)
                    if sum(outros_counter.values()) > 0:
                        top_ports.append(('Outras portas', outros_counter, sum(outros_counter.values())))

                ports = []
                series = {}
                for port, country_counts, _ in top_ports:
                    port_label = f"Port {port}" if isinstance(port, int) else str(port)
                    ports.append(port_label)
                    sorted_countries = sorted(
                        country_counts.items(),
                        key=lambda item: item[1],
                        reverse=True
                    )

                    selected = []
                    outros_total = 0
                    for index, (country, count) in enumerate(sorted_countries):
                        if index < 3:
                            selected.append((country, count))
                        else:
                            outros_total += count

                    if outros_total > 0:
                        selected.append(('Outros', outros_total))

                    series[port_label] = {
                        country: count
                        for country, count in selected
                    }

                analysis['portCountryDistribution'] = {
                    'ports': ports,
                    'series': series
                }

        if http_credentials_counter:
            analysis['httpCredentialAttempts'] = [
                {
                    'username': username,
                    'password': password,
                    'count': count
                }
                for (username, password), count in http_credentials_counter.most_common(200)
            ]

        analysis['logtypeCounts'] = dict(analysis['logtypeCounts'])
        analysis['attackCounts'] = dict(analysis['attackCounts'])
        analysis['severityCounts'] = dict(analysis['severityCounts'])
        analysis['serviceCounts'] = dict(analysis['serviceCounts'])
        analysis['countryCounts'] = dict(analysis['countryCounts'])
        analysis['countryHourlyActivity'] = {
            country: _hour_series(hours)
            for country, hours in sorted(
                analysis['countryHourlyActivity'].items(),
                key=lambda item: sum(item[1].values()),
                reverse=True,
            )
        }
        sorted_rolling = sorted(
            rolling_country_activity.items(),
            key=lambda item: sum(item[1]),
            reverse=True,
        )[:10]
        analysis['countryRolling12h'] = {
            'labels': rolling_labels,
            'series': {country: values for country, values in sorted_rolling}
        }
        sorted_rolling24 = sorted(
            rolling24_country_activity.items(),
            key=lambda item: sum(item[1]),
            reverse=True,
        )[:10]
        analysis['countryRolling24h'] = {
            'labels': rolling24_labels,
            'series': {country: values for country, values in sorted_rolling24}
        }
        analysis['countryLocations'] = sorted(
            analysis['countryLocations'].values(),
            key=lambda entry: entry['count'],
            reverse=True,
        )
        analysis['geoPoints'] = sorted(
            analysis['geoPoints'].values(),
            key=lambda entry: entry['count'],
            reverse=True,
        )
        
        return analysis
    
    def categorize_logtype(self, logtype, event):
        """Categorize logtype dynamically based on context."""
        if 1000 <= logtype < 2000:
            return 'System'
        elif 2000 <= logtype < 3000:
            return 'FTP'
        elif 3000 <= logtype < 4000:
            logdata = event.get('logdata', {})
            if isinstance(logdata, dict) and ('USERNAME' in logdata or 'PASSWORD' in logdata):
                return 'HTTP Login'
            return 'HTTP'
        elif 4000 <= logtype < 5000:
            logdata = event.get('logdata', {})
            if isinstance(logdata, dict) and 'REMOTEVERSION' in logdata:
                return 'SSH Handshake'
            elif isinstance(logdata, dict) and 'SESSION' in logdata:
                return 'SSH Session'
            return 'SSH'
        elif 5000 <= logtype < 6000:
            return 'Web3'
        else:
            return f'Type-{logtype}'
    
    def detect_attack_type(self, event):
        """Detect attack type dynamically."""
        attack_info = {'type': None, 'description': ''}
        
        attack_type = event.get('attack_type')
        if attack_type:
            attack_info['type'] = attack_type.replace('_', ' ').title()
            return attack_info
        
        logtype = event.get('logtype')
        logdata = event.get('logdata', {})
        
        if isinstance(logdata, dict):
            if 'USERNAME' in logdata and 'PASSWORD' in logdata:
                attack_info['type'] = 'Login Attempt'
                attack_info['description'] = f"User: {logdata.get('USERNAME')}"
            elif 'PATH' in logdata:
                path = logdata.get('PATH', '')
                if any(suspicious in path.lower() for suspicious in ['admin', 'login', 'wp-', 'phpmyadmin']):
                    attack_info['type'] = 'Web Scan'
                else:
                    attack_info['type'] = 'HTTP Request'
            elif 'SESSION' in logdata:
                attack_info['type'] = 'SSH Connection'
        
        if event.get('service'):
            service = event.get('service')
            if 'web3' in service.lower():
                attack_info['type'] = 'Web3 Interaction'
            elif 'wallet' in service.lower():
                attack_info['type'] = 'Wallet Access'
        
        return attack_info
    
    def is_connection_event(self, event):
        """Check whether this is a connection event."""
        attack_type = event.get('attack_type', '').lower()
        logtype = event.get('logtype')
        
        return (
            'connection' in attack_type or
            logtype in [4000, 5000] or
            event.get('service') is not None
        )
    
    def is_login_attempt(self, event):
        """Check whether this is a login attempt."""
        logdata = event.get('logdata', {})
        attack_type = event.get('attack_type', '').lower()
        
        return (
            isinstance(logdata, dict) and ('USERNAME' in logdata or 'PASSWORD' in logdata) or
            'login' in attack_type or
            event.get('logtype') in [2000, 3001]
        )
    
    def extract_service_info(self, event):
        """Extract service information dynamically."""
        service = event.get('service')
        if service:
            return service.replace('_', ' ').title()
        
        dst_port = event.get('dst_port')
        if dst_port:
            port_services = {
                22: 'SSH', 21: 'FTP', 80: 'HTTP', 443: 'HTTPS',
                2222: 'SSH Honeypot', 2121: 'FTP Honeypot',
                8080: 'HTTP Alt', 8090: 'HTTP Admin', 8546: 'Web3 RPC'
            }
            return port_services.get(dst_port, f'Port-{dst_port}')
        
        logtype = event.get('logtype')
        if logtype:
            if 2000 <= logtype < 3000:
                return 'FTP'
            elif 3000 <= logtype < 4000:
                return 'HTTP'
            elif 4000 <= logtype < 5000:
                return 'SSH'
            elif 5000 <= logtype < 6000:
                return 'Web3'
        
        return None
    
    def infer_severity(self, event):
        """Infer severity based on event context."""
        logtype = event.get('logtype')
        logdata = event.get('logdata', {})
        attack_type = event.get('attack_type', '').lower()
        
        if isinstance(logdata, dict) and ('USERNAME' in logdata and 'PASSWORD' in logdata):
            return 'high'
        
        if 'scan' in attack_type or 'brute' in attack_type:
            return 'medium'
        
        if 'connection' in attack_type:
            return 'low'
        
        if logtype:
            if logtype >= 3000:
                return 'medium'
            elif logtype >= 2000:
                return 'low'
        
        return 'info'
    
    def extract_timestamp(self, event):
        """Extract the event timestamp."""
        return (
            event.get('local_time_adjusted') or 
            event.get('local_time') or 
            event.get('timestamp') or
            event.get('utc_time')
        )

    def extract_event_hour(self, event):
        """Extract event hour prioritizing adjusted local time when available."""
        dt = self.extract_event_datetime(event)
        return dt.hour if dt is not None else None

    def extract_event_datetime(self, event):
        """Extract event datetime normalized to local timezone."""
        pairs = (
            ('local_time_adjusted', event.get('local_time_adjusted')),
            ('local_time', event.get('local_time')),
            ('timestamp', event.get('timestamp')),
            ('utc_time', event.get('utc_time')),
        )
        local_tz = datetime.now().astimezone().tzinfo
        for key, value in pairs:
            if not value:
                continue
            try:
                dt = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
            except Exception:
                continue

            # If timezone-aware, convert to local
            if dt.tzinfo is not None:
                return dt.astimezone()

            # If naive, assume timezone based on field semantic
            try:
                if key == 'utc_time':
                    return dt.replace(tzinfo=timezone.utc).astimezone()
                # Treat local_time/local_time_adjusted/timestamp as local naive times
                if local_tz is not None:
                    return dt.replace(tzinfo=local_tz).astimezone(local_tz)
                # Fallback: return naive (will be used only for hour extraction)
                return dt
            except Exception:
                # Fallback to naive dt
                return dt
        return None
    
    def create_incident_from_event(self, event, attack_info):
        """Create an incident from an event."""
        logtype = event.get('logtype')
        if not logtype:
            return None
        
        logdata = event.get('logdata', {})
        credentials = ""
        extra_info = ""
        
        if isinstance(logdata, dict):
            username = logdata.get('USERNAME')
            password = logdata.get('PASSWORD')
            if username and password:
                credentials = f" | {username}:{password}"
            
            if 'PATH' in logdata:
                extra_info = f" | Path: {logdata['PATH']}"
            elif 'HOSTNAME' in logdata:
                extra_info = f" | Host: {logdata['HOSTNAME']}"
        
        return {
            'type': self.categorize_logtype(logtype, event),
            'attack': attack_info['type'] or 'Unknown Activity',
            'srcHost': event.get('src_host', 'Unknown'),
            'severity': event.get('severity') or self.infer_severity(event),
            'timestamp': self.extract_timestamp(event) or datetime.now().isoformat(),
            'credentials': credentials,
            'extraInfo': extra_info
        }
    
    def get_default_data(self):
        """Return default data when no log is available."""
        now_local = datetime.now().astimezone()
        rolling_window_end = (now_local.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1))
        rolling_window_start = rolling_window_end - timedelta(hours=12)
        rolling_labels = [
            (rolling_window_start + timedelta(hours=i)).strftime('%Hh')
            for i in range(12)
        ]
        hourly_window_start = now_local - timedelta(hours=24)
        hourly_labels = [
            (hourly_window_start + timedelta(hours=i)).strftime('%d/%m %Hh')
            for i in range(24)
        ]
        return {
            'totalEvents': 0,
            'connectionEvents': 0,
            'loginAttempts': 0,
            'uniqueIPs': 0,
            'hourlyActivity': {},
            'hourlyActivityWindow': {'labels': hourly_labels, 'values': [0] * 24},
            'hourlyServiceActivity': {'labels': hourly_labels, 'series': {}},
            'logtypeCounts': {},
            'attackCounts': {},
            'attackSeverityDistribution': {},
            'severityCounts': {},
            'serviceCounts': {},
            'countryCounts': {},
            'countryHourlyActivity': {},
            'countryRolling12h': {'labels': rolling_labels, 'series': {}},
            'countryLocations': [],
            'geoPoints': [],
            'recentIncidents': [],
            'httpCredentialAttempts': []
        }
    
    def log_message(self, format, *args):
        """Override to suppress noisy HTTP logs."""
        pass

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
    global DASHBOARD_TOKEN
    if token:
        DASHBOARD_TOKEN = token
    try:
        with ThreadedTCPServer((host, port), DashboardHandler) as httpd:
            access_url = _build_access_url(host, port, DASHBOARD_TOKEN)
            print("Dashboard started")
            print(f"Static directory: {DASHBOARD_DIRECTORY}")
            if DASHBOARD_TOKEN:
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
        str(Path(__file__).resolve().parents[3] / "dashboard_server.py"),
        "--host",
        host,
        "--port",
        str(selected_port),
        "--token",
        token,
    ]
    process = subprocess.Popen(
        child_args,
        cwd=str(Path(__file__).resolve().parents[3]),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    if process.poll() is not None:
        print("Failed to start dashboard")
        return
    _write_runtime_state(process.pid, host, selected_port, token)

    print("Dashboard started")
    print(f"Mode: {'public' if public else 'internal'}")
    print(f"Access: {access_url}")
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
    global DASHBOARD_TOKEN

    if argv is None:
        argv = sys.argv[1:]

    port = 0
    host = DEFAULT_HOST

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
                DASHBOARD_TOKEN = argv[i + 1]

    if not DASHBOARD_TOKEN:
        DASHBOARD_TOKEN = secrets.token_urlsafe(24)

    start_dashboard_server(port, host, DASHBOARD_TOKEN)

if __name__ == "__main__":
    main()
