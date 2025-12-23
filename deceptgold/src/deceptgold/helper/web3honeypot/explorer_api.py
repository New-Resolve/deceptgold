"""
Blockchain Explorer API Honeypot
"""

from typing import Dict, Any
from collections import defaultdict
import time
from .base import Web3HoneypotBase


class BlockchainExplorerAPIHoneypot(Web3HoneypotBase):
    NAME = "web3.explorer_api"
    """Simulates a blockchain explorer API"""
    
    def __init__(self, port: int = 8547, rate_limit: int = 5, config=None, logger=None):
        super().__init__(port, "web3_explorer_api", config=config, logger=logger)
        self.rate_limit = rate_limit
        self.api_requests = defaultdict(list)
        self.vulnerability_searches = defaultdict(int)
        
    def handle_api_request(self, module: str, action: str, address: str = None, search_pattern: str = None) -> Dict[str, Any]:
        """Handle API requests and detect abuse"""
        source = "192.168.1.100"  # Would be real IP in production
        
        self.api_requests[source].append({
            "timestamp": time.time(),
            "module": module,
            "action": action
        })
        
        # Track vulnerability searches
        if search_pattern:
            self.vulnerability_searches[source] += 1
        
        # Clean old requests
        cutoff = time.time() - 60
        self.api_requests[source] = [
            req for req in self.api_requests[source]
            if req["timestamp"] > cutoff
        ]
        
        if self.is_scraping_detected():
            details = {
                "method": "api_request",
                "src_host": source,
                "module": module
            }
            self.log_attack("explorer_api_scraping", details, severity="low")
            self.generate_reward("explorer_api_scraping", 20)

        return {"status": "ok", "result": "fake_data"}
    
    def is_scraping_detected(self, threshold: int = 50) -> bool:
        """Detect API scraping"""
        total_requests = sum(len(reqs) for reqs in self.api_requests.values())
        return total_requests >= threshold
    
    def is_rate_limit_exploited(self, threshold: int = 30) -> bool:
        """Detect rate limit exploitation"""
        for source, requests in self.api_requests.items():
            recent = [r for r in requests if time.time() - r["timestamp"] < 10]
            if len(recent) >= threshold:
                return True
        return False
    
    def is_vulnerability_search_detected(self, threshold: int = 3) -> bool:
        """Detect searching for vulnerable contracts"""
        return any(count >= threshold for count in self.vulnerability_searches.values())
