"""
Wallet Service Honeypot

Simulates a wallet service API to detect phishing and key theft attempts.
"""

import secrets
from typing import Dict, Any
from collections import defaultdict
from .base import Web3HoneypotBase


class WalletServiceHoneypot(Web3HoneypotBase):
    NAME = "web3.wallet_service"
    """Simulates a wallet service API"""
    
    def __init__(self, port: int = 8546, config=None, logger=None):
        super().__init__(port, "web3_wallet_service", config=config, logger=logger)
        self.login_attempts = defaultdict(list)
        
    def handle_wallet_import(self, seed_phrase: str) -> Dict[str, Any]:
        """Detect seed phrase phishing attempts (CRITICAL)"""
        details = {
            "method": "wallet_import",
            "seed_phrase_length": len(seed_phrase.split()),
            "src_host": "192.168.1.100"
        }
        
        log_entry = self.log_attack(
            "wallet_seed_phrase_phishing",
            details,
            severity="critical"
        )
        
        self.generate_reward("wallet_seed_phrase_phishing", 150)
        
        return {
            "detected": True,
            "severity": "critical",
            "attack_type": "wallet_seed_phrase_phishing",
            "reward": 150
        }
    
    def handle_wallet_export(self, wallet_id: str, password: str) -> Dict[str, Any]:
        """Detect private key export attempts"""
        details = {
            "method": "wallet_export",
            "wallet_id": wallet_id,
            "src_host": "192.168.1.100"
        }
        
        log_entry = self.log_attack(
            "wallet_private_key_export",
            details,
            severity="critical"
        )
        
        self.generate_reward("wallet_private_key_export", 120)
        
        # Return fake private key
        fake_key = "0x" + secrets.token_hex(32)
        
        return {
            "detected": True,
            "attack_type": "wallet_private_key_export",
            "fake_private_key": fake_key,
            "reward": 120
        }
    
    def handle_transaction_sign(self, tx_data: Dict[str, Any]) -> Dict[str, Any]:
        """Detect malicious transaction signing attempts"""
        suspicious_patterns = []
        
        # Check for burn address
        if tx_data.get("to") == "0x0000000000000000000000000000000000000000":
            suspicious_patterns.append("burn_address")
        
        # Check for high value
        value = int(tx_data.get("value", "0x0"), 16)
        if value > 10**18:  # > 1 ETH
            suspicious_patterns.append("high_value_transfer")
        
        if suspicious_patterns:
            details = {
                "method": "transaction_sign",
                "to": tx_data.get("to"),
                "value": tx_data.get("value"),
                "suspicious_patterns": suspicious_patterns,
                "src_host": "192.168.1.100"
            }
            
            log_entry = self.log_attack(
                "wallet_malicious_transaction",
                details,
                severity="high"
            )
            
            return {
                "detected": True,
                "suspicious_patterns": suspicious_patterns,
                "attack_type": "wallet_malicious_transaction"
            }
        
        return {"detected": False}
    
    def handle_wallet_login(self, wallet_id: str, password: str):
        """Track login attempts for brute force detection"""
        import time
        self.login_attempts[wallet_id].append(time.time())
        
        # Clean old attempts (older than 5 minutes)
        cutoff = time.time() - 300
        self.login_attempts[wallet_id] = [
            t for t in self.login_attempts[wallet_id] if t > cutoff
        ]
        
        if self.is_brute_force_detected(wallet_id):
            details = {
                "method": "wallet_login",
                "wallet_id": wallet_id,
                "src_host": "192.168.1.100"
            }
            self.log_attack("wallet_brute_force", details, severity="high")
            self.generate_reward("wallet_brute_force", 80)
    
    def is_brute_force_detected(self, wallet_id: str, threshold: int = 50) -> bool:
        """Detect brute force password attempts"""
        return len(self.login_attempts.get(wallet_id, [])) >= threshold
