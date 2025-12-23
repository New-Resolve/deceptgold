"""
Base class for Web3 honeypots
"""

import logging
import time
from datetime import datetime
from typing import Dict, Any, List
from collections import defaultdict

from twisted.internet import protocol, reactor
from twisted.application import internet

class Web3Protocol(protocol.Protocol):
    def __init__(self, factory):
        self.factory = factory

    def connectionMade(self):
        peer = self.transport.getPeer()
        self.factory.honeypot.log_attack(
            "connection_made",
            {"src_host": peer.host, "src_port": peer.port},
            severity="low"
        )

    def dataReceived(self, data):
        # Basic echo/logging for now. In future, parse HTTP/JSON-RPC here.
        peer = self.transport.getPeer()
        try:
            decoded_data = data.decode('utf-8', errors='ignore')
        except:
            decoded_data = str(data)
            
        self.factory.honeypot.log_attack(
            "data_received",
            {"src_host": peer.host, "data_preview": decoded_data[:100]},
            severity="info"
        )
        
        # Simple HTTP response if it looks like HTTP request
        if b"HTTP" in data:
             # Add some headers that might help identification (though nmap is picky)
             response = (
                 b"HTTP/1.1 200 OK\r\n"
                 b"Content-Type: application/json\r\n"
                 b"Server: " + self.factory.honeypot.service_name.encode() + b"\r\n"
                 b"X-Network-Name: " + str(self.factory.honeypot.config.getVal(f"{self.factory.honeypot.config_base}.network_name", "Web3 Network")).encode() + b"\r\n"
                 b"\r\n"
                 b"{\"jsonrpc\":\"2.0\",\"id\":1,\"result\":\"0x1\"}"
             )
             self.transport.write(response)
             self.transport.loseConnection()

class Web3Factory(protocol.Factory):
    def __init__(self, honeypot):
        self.honeypot = honeypot

    def buildProtocol(self, addr):
        return Web3Protocol(self)

class Web3HoneypotBase:
    """Base class for all Web3 honeypots"""
    
    def __init__(self, port: int = None, service_name: str = "web3_base", config=None, logger=None):
        self.config = config
        self.service_name = service_name
        
        # Determine the base config key (e.g. web3.rpc_node)
        # We prefer the NAME attribute set on subclasses
        self.config_base = getattr(self, 'NAME', service_name.replace('_', '.'))
        
        # Determine port from config if available, otherwise use default
        if config:
            try:
                # Try to get port from config (e.g. "web3.rpc_node.port")
                config_key = f"{self.config_base}.port"
                self.port = int(config.getVal(config_key, port))
            except:
                self.port = port
        else:
            self.port = port
            
        # Use provided logger or create default
        if logger:
            self.logger = logger
        else:
            self.logger = logging.getLogger(f"web3honeypot.{service_name}")
            
        self.reward_system = None
        self.attack_log = []
        self.request_history = defaultdict(list)
        self.start_time = None
        
    def start(self):
        """Satisfy tests and log start-up (deprecated in favor of getService)"""
        self.start_time = datetime.now()
        self.logger.log({"logdata": f"{self.service_name} honeypot started on port {self.port}"})

    def getService(self):
        """Return a Twisted Service to open the port"""
        # Log startup here
        self.logger.log({"logdata": f"{self.service_name} honeypot started on port {self.port}"})
        factory = Web3Factory(self)
        return internet.TCPServer(self.port, factory)
    
    def stop(self):
        """Stop the honeypot service"""
        self.logger.log({"logdata": f"{self.service_name} honeypot stopped"})
    
    def log_attack(self, attack_type: str, details: Dict[str, Any], severity: str = "medium"):
        """Log an attack attempt"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "logtype": 5000,  # Web3 attack logtype
            "service": self.service_name,
            "attack_type": attack_type,
            "details": details,
            "severity": severity,
            "src_host": details.get("src_host", "unknown")
        }
        
        self.attack_log.append(log_entry)
        
        if self.logger:
            self.logger.log(log_entry)
        
        return log_entry
    
    def generate_reward(self, attack_type: str, amount: int):
        """Generate reward for detected attack"""
        if self.reward_system:
            self.reward_system.generate_reward(amount, attack_type)
    
    def track_request(self, source: str, request_type: str):
        """Track requests for pattern detection"""
        self.request_history[source].append({
            "type": request_type,
            "timestamp": time.time()
        })
        
        # Clean old requests (older than 1 hour)
        cutoff = time.time() - 3600
        self.request_history[source] = [
            req for req in self.request_history[source]
            if req["timestamp"] > cutoff
        ]
    
    def is_rate_limit_exceeded(self, source: str, limit: int = 100, window: int = 60) -> bool:
        """Check if rate limit is exceeded"""
        cutoff = time.time() - window
        recent_requests = [
            req for req in self.request_history[source]
            if req["timestamp"] > cutoff
        ]
        return len(recent_requests) > limit
    
    def detect_pattern(self, source: str, pattern_type: str, threshold: int = 10) -> bool:
        """Detect suspicious patterns in requests"""
        pattern_requests = [
            req for req in self.request_history[source]
            if req["type"] == pattern_type
        ]
        return len(pattern_requests) >= threshold
