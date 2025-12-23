"""
RPC Node Honeypot

Simulates an Ethereum/BSC RPC node to detect malicious blockchain interactions.
"""

import random
import json
from typing import Dict, Any
from .base import Web3HoneypotBase


class RPCNodeHoneypot(Web3HoneypotBase):
    NAME = "web3.rpc_node"
    """Simulates an Ethereum/BSC RPC node"""
    
    def __init__(self, port: int = 8545, chain_id: int = 56, config=None, logger=None):
        super().__init__(port, "web3_rpc_node", config=config, logger=logger)
        self.chain_id = chain_id
        self.fake_accounts = self._generate_fake_accounts()
        self.scanning_threshold = 50
        
    def _generate_fake_accounts(self) -> list:
        """Generate fake accounts with attractive balances"""
        accounts = []
        for i in range(10):
            account = {
                "address": f"0x{'0' * 39}{i:x}",
                "balance": random.randint(10**18, 100 * 10**18)  # 1-100 ETH
            }
            accounts.append(account)
        return accounts
    
    def handle_eth_getBalance(self, address: str) -> str:
        """Return fake balance to attract attackers"""
        self.track_request(address, "eth_getBalance")
        
        if self.is_scanning_detected():
            details = {
                "method": "eth_getBalance",
                "src_host": "192.168.1.100",
                "scanning_detected": True
            }
            self.log_attack("rpc_address_scanning", details, severity="medium")
            self.generate_reward("rpc_address_scanning", 20)
        
        # Return attractive fake balance
        balance_wei = random.randint(10**18, 100 * 10**18)
        return hex(balance_wei)
    
    def handle_personal_unlockAccount(self, address: str, password: str, duration: int = 300) -> Dict[str, Any]:
        """Detect account unlock attempts (CRITICAL attack)"""
        details = {
            "method": "personal_unlockAccount",
            "address": address,
            "duration": duration,
            "src_host": "192.168.1.100"  # Would be real IP in production
        }
        
        log_entry = self.log_attack(
            "rpc_account_unlock_attempt",
            details,
            severity="critical"
        )
        
        self.generate_reward("rpc_account_unlock_attempt", 100)
        
        return {
            "detected": True,
            "attack_type": "rpc_account_unlock_attempt",
            "severity": "critical",
            "reward": 100
        }
    
    def handle_eth_sendRawTransaction(self, raw_tx: str) -> Dict[str, Any]:
        """Detect malicious raw transaction attempts"""
        details = {
            "method": "eth_sendRawTransaction",
            "raw_tx": raw_tx[:100],  # Truncate for logging
            "src_host": "192.168.1.100"
        }
        
        # Analyze transaction for suspicious patterns
        suspicious = self._analyze_transaction(raw_tx)
        
        if suspicious:
            log_entry = self.log_attack(
                "rpc_malicious_transaction",
                details,
                severity="high"
            )
            
            self.generate_reward("rpc_malicious_transaction", 50)
            
            return {
                "detected": True,
                "attack_type": "rpc_malicious_transaction",
                "severity": "high",
                "reward": 50
            }
        
        return {"detected": False}
    
    def handle_eth_call(self, call_data: Dict[str, Any]) -> Dict[str, Any]:
        """Detect contract exploitation via eth_call"""
        details = {
            "method": "eth_call",
            "to": call_data.get("to"),
            "data": call_data.get("data", "")[:100],
            "from": call_data.get("from"),
            "src_host": "192.168.1.100"
        }
        
        suspicious_patterns = []
        
        # Check for suspicious data length
        if len(call_data.get("data", "")) > 200:
            suspicious_patterns.append("long_data")
        
        if suspicious_patterns:
            log_entry = self.log_attack(
                "rpc_contract_exploit_attempt",
                details,
                severity="medium"
            )
            
            return {
                "detected": True,
                "suspicious_patterns": suspicious_patterns,
                "attack_type": "rpc_contract_exploit_attempt"
            }
        
        return {"detected": False}
    
    def is_scanning_detected(self) -> bool:
        """Detect if address scanning is occurring"""
        # Check if multiple addresses were queried
        total_requests = sum(len(reqs) for reqs in self.request_history.values())
        return total_requests >= self.scanning_threshold
    
    def _analyze_transaction(self, raw_tx: str) -> bool:
        """Analyze transaction for malicious patterns"""
        # Simplified analysis - in production would decode and analyze
        # High value transfers, unknown recipients, etc.
        return len(raw_tx) > 100  # Simplified check
