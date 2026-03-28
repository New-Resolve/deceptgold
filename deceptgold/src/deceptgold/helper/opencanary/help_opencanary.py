import os
import tracemalloc
from functools import wraps

from deceptgold.configuration.config_manager import get_config
from deceptgold.helper.helper import parse_args
from deceptgold.helper.notify.notify import check_send_notify


def global_twisted_error_handler(eventDict):
    if eventDict.get('isError'):
        failure = eventDict.get('failure')
        if failure:
            if isinstance(failure.value, RuntimeError) and "KEXINIT" in str(failure.value):
                return
        print("[!] Unexpected error caught by global handler.")
        return



_forwarded_patch_applied = False
_trace_enabled = bool(int(os.environ.get("DECEPTGOLD_TRACE_ALLOC", "0") or 0))
_trace_every = max(int(os.environ.get("DECEPTGOLD_TRACE_EVERY", "0") or 0), 0)
_trace_top_n = max(int(os.environ.get("DECEPTGOLD_TRACE_TOP", "5") or 5), 1)
_trace_counter = 0
_trace_log_path = os.environ.get("DECEPTGOLD_TRACE_LOG", "/tmp/deceptgold_tracemalloc.log")


def _normalize_header_value(value):
    if value in (None, "", b""):
        return "<not supplied>"
    if isinstance(value, bytes):
        try:
            return value.decode('utf-8', errors='replace')
        except Exception:
            return repr(value)
    return str(value)


def _wrap_log_with_forwarded_headers(log_fn, request):
    forwarded = _normalize_header_value(request.getHeader("x-forwarded-for"))
    real_ip = _normalize_header_value(request.getHeader("x-real-ip"))

    def patched(logdata, *args, **kwargs):
        if isinstance(logdata, dict):
            logdata.setdefault("X-Forwarded-For", forwarded)
            logdata.setdefault("X-Real-IP", real_ip)

        if _trace_enabled:
            global _trace_counter
            _trace_counter += 1
            should_trace = (_trace_every == 0) or (_trace_counter % _trace_every == 0)
            
            if should_trace:
                if not tracemalloc.is_tracing():
                    tracemalloc.start()
                snapshot = tracemalloc.take_snapshot()
                top_stats = snapshot.statistics('lineno')[:_trace_top_n]
                lines = []
                lines.append(
                    f"[DECEPTGOLD][MEM] request=#{_trace_counter} context={request.path.decode('utf-8', 'ignore')}\n"
                )
                current, peak = tracemalloc.get_traced_memory()
                lines.append(
                    f"[DECEPTGOLD][MEM] Current: {current / 1024 / 1024:.2f} MB | Peak: {peak / 1024 / 1024:.2f} MB\n"
                )
                for stat in top_stats:
                    size_mb = stat.size / 1024 / 1024
                    lines.append(
                        f"[DECEPTGOLD][MEM] {stat.count} blocks | {size_mb:.2f} MB | {stat.traceback}\n"
                    )
                try:
                    with open(_trace_log_path, 'a', encoding='utf-8') as fh:
                        fh.writelines(lines)
                except Exception:
                    pass

        return log_fn(logdata, *args, **kwargs)

    return patched


def _patch_http_logging():
    global _forwarded_patch_applied
    if _forwarded_patch_applied:
        return

    try:
        from opencanary.modules import http as http_module
    except Exception:
        return

    def wrap_method(method):
        if getattr(method, "__dg_forwarded_patch__", False):
            return method

        @wraps(method)
        def wrapper(self, request, *args, **kwargs):
            # Always track memory for debugging
            import gc
            import time
            import os
            import resource
            
            mem_before = None
            rss_before = 0
            path_str = ''
            
            # Get RSS (actual process memory)
            try:
                rss_before = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            except Exception:
                pass
            
            if tracemalloc.is_tracing():
                mem_before, _ = tracemalloc.get_traced_memory()
                try:
                    path_str = request.path.decode('utf-8', 'ignore') if hasattr(request.path, 'decode') else str(request.path)
                except Exception:
                    path_str = 'unknown'
            
            original_bound_attr = self.factory.__dict__.get('log', None)
            original_log = self.factory.log
            self.factory.log = _wrap_log_with_forwarded_headers(original_log, request)
            try:
                # Capture memory DURING processing
                if tracemalloc.is_tracing():
                    mem_mid_start, _ = tracemalloc.get_traced_memory()
                
                result = method(self, request, *args, **kwargs)
                
                # Capture right after method execution (peak should be here)
                rss_during = 0
                try:
                    rss_during = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
                except Exception:
                    pass
                
                if tracemalloc.is_tracing():
                    mem_mid_end, peak_mid = tracemalloc.get_traced_memory()
                    delta_during = (mem_mid_end - mem_mid_start) / 1024 / 1024
                    # RSS is in KB on Linux, bytes on macOS
                    rss_delta_mb = (rss_during - rss_before) / 1024  # Assume Linux (KB)
                    try:
                        with open('/tmp/deceptgold_memory_peak.log', 'a', encoding='utf-8') as f:
                            snapshot = tracemalloc.take_snapshot()
                            top_stats = snapshot.statistics('lineno')[:10]
                            f.write(f"\n=== [PEAK] {path_str} ===\n")
                            f.write(f"Python heap delta: {delta_during:.2f} MB | Peak: {peak_mid/1024/1024:.2f} MB\n")
                            f.write(f"RSS delta: {rss_delta_mb:.2f} MB | RSS total: {rss_during/1024:.2f} MB\n")
                            f.write(f"Top Python allocations:\n")
                            for stat in top_stats:
                                f.write(f"  {stat.count} blocks | {stat.size/1024/1024:.2f} MB | {stat.traceback}\n")
                    except Exception as e:
                        pass
                
                return result
            finally:
                if original_bound_attr is None:
                    self.factory.__dict__.pop('log', None)
                else:
                    self.factory.log = original_bound_attr
                
                # Log memory delta
                rss_after = 0
                try:
                    rss_after = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
                except Exception:
                    pass
                
                if tracemalloc.is_tracing() and mem_before is not None:
                    mem_after, peak = tracemalloc.get_traced_memory()
                    delta_mb = (mem_after - mem_before) / 1024 / 1024
                    peak_mb = peak / 1024 / 1024
                    rss_delta_mb = (rss_after - rss_before) / 1024
                    try:
                        with open('/tmp/deceptgold_memory_debug.log', 'a', encoding='utf-8') as f:
                            f.write(f"[HTTP] {path_str} | Python: {delta_mb:.2f} MB | Peak: {peak_mb:.2f} MB | RSS: {rss_delta_mb:.2f} MB | Total RSS: {rss_after/1024:.2f} MB\n")
                    except Exception:
                        pass
                gc.collect()

        wrapper.__dg_forwarded_patch__ = True
        return wrapper

    targets = (
        ("BasicLogin", "render_GET"),
        ("BasicLogin", "render_POST"),
        ("BasicLogin", "_log_unimplemented_method"),
        ("RedirectCustomHeaders", "render"),
    )

    for cls_name, method_name in targets:
        cls = getattr(http_module, cls_name, None)
        if cls is None:
            continue
        original = getattr(cls, method_name, None)
        if original is None:
            continue
        setattr(cls, method_name, wrap_method(original))

    _forwarded_patch_applied = True


def start_opencanary_internal(force_no_wallet='force_no_wallet=False', debug=False):
    parsed_args = parse_args([force_no_wallet])
    force_no_wallet = parsed_args.get('force_no_wallet', False)

    from twisted.python import log

    # Always start tracemalloc for memory debugging
    if not tracemalloc.is_tracing():
        tracemalloc.start()

    log.startLoggingWithObserver(global_twisted_error_handler, setStdout=False)

    import sys
    import traceback
    import warnings
    import time
    import builtins

    original_print = builtins.print

    def fake_print(*args, **kwargs):
        try:
            if isinstance(args[0], str):
                if 'We hope you enjoy using' in args[0]:
                    return None

                if '[-] Failed to open' in args[0]:
                    return None

                if 'We hope you enjoy using' in args[0]:
                    return None

                if '[-] Using config file:' in args[0]:
                    return None

                original_print(args[0].msg)
            else:
                original_print(args[0])
        except Exception:
            pass



    builtins.print = fake_print

    from opencanary.config import config

    class Web2ConfigWrapper:
        def __init__(self, original_config):
            self.original_config = original_config
        
        def moduleEnabled(self, module_name):
            if self.original_config.moduleEnabled(module_name): return True
            if self.original_config.moduleEnabled(f"web2.{module_name}"): return True
            return False

        def getVal(self, key, default=None):
            try:
                val = self.original_config.getVal(key)
                if val is not None: return val
            except: pass
            
            try:
                val = self.original_config.getVal(f"web2.{key}")
                if val is not None: return val
            except: pass
            
            return default

        def setVal(self, key, val):
            return self.original_config.setVal(key, val)
            
        def __getattr__(self, name):
            return getattr(self.original_config, name)

    config = Web2ConfigWrapper(config)
    
    # Refactoring: Map web2.* configuration to standard keys (legacy compatibility)
    try:
        import json
        import os
        conf_path = os.path.join(os.path.expanduser("~"), ".opencanary.conf")
        if os.path.exists(conf_path):
            with open(conf_path, 'r') as f:
                data = json.load(f)
                for key, val in data.items():
                    if key.startswith("web2."):
                        std_key = key[5:]
                        try:
                            # Ensure module can find its config without prefix
                            config.setVal(std_key, val)
                        except:
                            pass
    except Exception as e:
        print(f"Error mapping web2 config: {e}")

    from opencanary.logger import getLogger
    from opencanary.modules.http import CanaryHTTP
    from opencanary.modules.https import CanaryHTTPS
    from opencanary.modules.ftp import CanaryFTP
    from opencanary.modules.ssh import CanarySSH
    from opencanary.modules.telnet import Telnet
    from opencanary.modules.httpproxy import HTTPProxy
    from opencanary.modules.mysql import CanaryMySQL
    from opencanary.modules.mssql import MSSQL
    from opencanary.modules.ntp import CanaryNtp
    from opencanary.modules.tftp import CanaryTftp
    from opencanary.modules.vnc import CanaryVNC
    from opencanary.modules.sip import CanarySIP
    from opencanary.modules.git import CanaryGit
    from opencanary.modules.redis import CanaryRedis
    from opencanary.modules.tcpbanner import CanaryTCPBanner
    from opencanary.modules.rdp import CanaryRDP

    from twisted.internet import reactor
    from twisted.application.app import startApplication
    from twisted.internet.error import CannotListenError
    from twisted.application import service
    from pkg_resources import iter_entry_points


    """
    To earn 1 full DGLD in 1 year, a user needs to make exactly: 1,000,000,000 requests. 
    This means maintaining an average of: 31.71 requests per second
    """
    RATE_LIMIT = 32
    RATE_WINDOW = 1

    connections = {}

    def is_rate_limited(ip):
        now = time.time()
        timestamps = connections.get(ip, [])
        timestamps = [t for t in timestamps if now - t < RATE_WINDOW]

        if len(timestamps) >= RATE_LIMIT:
            return True

        timestamps.append(now)
        connections[ip] = timestamps
        return False

    class RateLimitedFactory:
        def __init__(self, original_factory):
            self.original_factory = original_factory

        def buildProtocol(self, addr):
            ip = addr.host
            if is_rate_limited(ip):
                # print(f"[!] Rate limit exceeded for {ip}")
                return None
            try:
                return self.original_factory.buildProtocol(addr)
            except Exception as error:
                logMsg(f"[!] Erro ao construir protocolo para {ip}: {str(error)}")
                return None

        def __getattr__(self, name):
            return getattr(self.original_factory, name)

    original_listenTCP = reactor.listenTCP

    def patched_listenTCP(port, factory, *args, **kwargs):
        return original_listenTCP(port, RateLimitedFactory(factory), *args, **kwargs)

    reactor.listenTCP = patched_listenTCP


    def warn(*args, **kwargs):
        pass


    warnings.warn = warn


    # from opencanary.modules.example0 import CanaryExample0
    # from opencanary.modules.example1 import CanaryExample1

    ENTRYPOINT = "canary.usermodule"
    _patch_http_logging()

    MODULES = [
        CanaryFTP,
        CanaryGit,
        CanaryHTTP,
        CanaryHTTPS,
        CanaryMySQL,
        CanaryNtp,
        CanaryRDP,
        CanaryRedis,
        CanarySIP,
        CanarySSH,
        CanaryTCPBanner,
        CanaryTftp,
        CanaryVNC,
        HTTPProxy,
        MSSQL,
        Telnet,
        # CanaryExample0,
        # CanaryExample1,
    ]

    builtins.print = original_print

    if config.moduleEnabled("snmp"):
        try:
            # Module need Scapy, but the rest of OpenCanary doesn't
            from opencanary.modules.snmp import CanarySNMP

            MODULES.append(CanarySNMP)
        except ImportError:
            print("Can't import SNMP. Please ensure you have Scapy installed.")

    if config.moduleEnabled("llmnr"):
        try:
            # Module needs Scapy, but the rest of OpenCanary doesn't
            from opencanary.modules.llmnr import CanaryLLMNR

            MODULES.append(CanaryLLMNR)
        except ImportError:
            print("Can't import LLMNR. Please ensure you have Scapy installed.")

    # NB: imports below depend on inotify, only available on linux
    if sys.platform.startswith("linux"):
        from opencanary.modules.samba import CanarySamba

        MODULES.append(CanarySamba)
        if config.moduleEnabled("portscan"):
            from opencanary.modules.portscan import CanaryPortscan
            MODULES.append(CanaryPortscan)

    logger = getLogger(config)

    # Web3 Services Integration
    if config.moduleEnabled("web3.rpc_node"):
        try:
            from deceptgold.helper.web3honeypot.rpc_node import RPCNodeHoneypot
            MODULES.append(RPCNodeHoneypot)
        except ImportError as e:
            print(f"Failed to import RPCNodeHoneypot: {e}")

    if config.moduleEnabled("web3.wallet_service"):
        try:
            from deceptgold.helper.web3honeypot.wallet_service import WalletServiceHoneypot
            MODULES.append(WalletServiceHoneypot)
        except ImportError as e:
            print(f"Failed to import WalletServiceHoneypot: {e}")

    if config.moduleEnabled("web3.ipfs_gateway"):
        try:
            from deceptgold.helper.web3honeypot.ipfs_gateway import IPFSGatewayHoneypot
            MODULES.append(IPFSGatewayHoneypot)
        except ImportError as e:
            print(f"Failed to import IPFSGatewayHoneypot: {e}")

    if config.moduleEnabled("web3.defi_protocol"):
        try:
            from deceptgold.helper.web3honeypot.defi_protocol import DeFiProtocolHoneypot
            MODULES.append(DeFiProtocolHoneypot)
        except ImportError as e:
            print(f"Failed to import DeFiProtocolHoneypot: {e}")

    if config.moduleEnabled("web3.nft_marketplace"):
        try:
            from deceptgold.helper.web3honeypot.nft_marketplace import NFTMarketplaceHoneypot
            MODULES.append(NFTMarketplaceHoneypot)
        except ImportError as e:
            print(f"Failed to import NFTMarketplaceHoneypot: {e}")

    if config.moduleEnabled("web3.explorer_api"):
        try:
            from deceptgold.helper.web3honeypot.explorer_api import BlockchainExplorerAPIHoneypot
            MODULES.append(BlockchainExplorerAPIHoneypot)
        except ImportError as e:
            print(f"Failed to import BlockchainExplorerAPIHoneypot: {e}")


    def start_mod(application, klass):  # noqa: C901
        try:
            obj = klass(config=config, logger=logger)
        except Exception:
            err = "Failed to instantiate instance of class %s in %s. %s" % (
                klass.__name__,
                klass.__module__,
                traceback.format_exc(),
            )
            logMsg({"logdata": err})
            return

        if hasattr(obj, "startYourEngines"):
            try:
                obj.startYourEngines()
                msg = "Ran startYourEngines on class %s in %s" % (
                    klass.__name__,
                    klass.__module__,
                )
                logMsg({"logdata": msg})

            except Exception:
                err = "Failed to run startYourEngines on %s in %s. %s" % (
                    klass.__name__,
                    klass.__module__,
                    traceback.format_exc(),
                )
                logMsg({"logdata": err})
        elif hasattr(obj, "getService"):
            try:
                service = obj.getService()
                if not isinstance(service, list):
                    service = [service]
                for s in service:
                    s.setServiceParent(application)
                msg = "Added service from class %s in %s to fake" % (
                    klass.__name__,
                    klass.__module__,
                )
                logMsg({"logdata": msg})
            except Exception:
                err = "Failed to add service from class %s in %s. %s" % (
                    klass.__name__,
                    klass.__module__,
                    traceback.format_exc(),
                )
                logMsg({"logdata": err})
        else:
            err = "The class %s in %s does not have any required starting method." % (
                klass.__name__,
                klass.__module__,
            )
            logMsg({"logdata": err})

    def logMsg(msg):
        msg = str(msg).lower().replace('canary', 'deceptgold')
        data = {}
        data["logdata"] = {"msg": msg}
        logger.log(data, retry=False)


    application = service.Application("opencanaryd")

    # List of modules to start
    start_modules = []
    # Add all custom modules
    # (Permanently enabled as they don't officially use settings yet)
    for ep in iter_entry_points(ENTRYPOINT):
        try:
            klass = ep.load(require=False)
            start_modules.append(klass)
        except Exception:
            err = "Failed to load class from the entrypoint: %s. %s" % (
                str(ep),
                traceback.format_exc(),
            )
            logMsg({"logdata": err})

    # Add only enabled modules
    start_modules.extend(filter(lambda m: config.moduleEnabled(m.NAME), MODULES))

    for klass in start_modules:
        start_mod(application, klass)

    try:
        address_user = get_config("user", "address")
        if not address_user:
            if force_no_wallet:
                logMsg("Warning: You are forcing the use of the honeypot without using the reward.")
            else:
                logMsg(f"The current user has not configured their public address to receive their rewards. The system will not continue. It is recommended to configure it before starting the fake services. Use the parameters: 'user --my-address 0xYourPublicAddress' or use the parameters 'service force-no-wallet=true' to continue without system interruption. But be careful, you will not be able to redeem your rewards now and/or retroactively.")
                sys.exit(1)
        check_send_notify("Deceptgold has been initialized.")
        startApplication(application, False)
        reactor.run()
    except OSError as oserror:
        msg_log = oserror
        logMsg(msg_log)
        print(f"\nERROR: {msg_log}")
    except CannotListenError as e:
        msg_log = str(e)
        try:
            port_except = str(e).split(':')[1]
        except Exception as e2:
            port_except = 0
        if hasattr(e, "socketError") and hasattr(e.socketError, "errno"):
            if e.socketError.errno == 13:
                msg_log = f"Permission denied: Could not create service on specific port: {port_except}. Try running with administrator permissions, example: `sudo deceptgold <command>`. or changed port number."
            if e.socketError.errno == 98:
                msg_log = f"Address already in use: {e.port}"
            logMsg(msg_log)
            print(f"\nERROR: {msg_log}")
    except Exception as e:
        if debug:
            msg_log = f"Generic Error: {str(e)}"
            logMsg(msg_log)
            print(f"\nERROR: {msg_log}")