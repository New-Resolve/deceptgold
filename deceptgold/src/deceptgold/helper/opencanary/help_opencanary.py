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



def start_opencanary_internal(force_no_wallet='force_no_wallet=False', debug=False):
    parsed_args = parse_args([force_no_wallet])
    force_no_wallet = parsed_args.get('force_no_wallet', False)

    from twisted.python import log

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
        if config.moduleEnabled("portscan") and is_docker():
            # Remove portscan if running in DOCKER (specified in Dockerfile)
            print("Can't use portscan in Docker. Portscan module disabled.")
        else:
            from opencanary.modules.portscan import CanaryPortscan

            MODULES.append(CanaryPortscan)

    logger = getLogger(config)


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
        try:
            if 'logdata' in dict(msg):
                check_send_notify(dict(msg)['logdata'].lower().replace('canary', 'deceptgold'))
        except Exception:
            pass
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
        if debug:
            pprint(f"Executou em modo debug: veja o endereco da carteida do usuario: {address_user}")
        if not address_user:
            if force_no_wallet:
                logMsg("Warning: You are forcing the use of the honeypot without using the reward.")
            else:
                logMsg(f"The current user has not configured their public address to receive their rewards. The system will not continue. It is recommended to configure it before starting the fake services. Use the parameters: 'user --my-address 0xYourPublicAddress' or use the parameters 'service force-no-wallet=true' to continue without system interruption. But be careful, you will not be able to redeem your rewards now and/or retroactively.")
                sys.exit(1)
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
        msg_log = f"Generic Error: {str(e)}"
        logMsg(msg_log)
        print(f"\nERROR: {msg_log}")