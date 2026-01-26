"""
DeFi Protocol Honeypot
"""

from typing import Dict, Any
from collections import defaultdict
import time
from .base import Web3HoneypotBase


class DeFiProtocolHoneypot(Web3HoneypotBase):
    NAME = "web3.defi_protocol"
    """Simulates a DeFi protocol (DEX/Lending)"""
    
    def __init__(self, port: int = 8548, protocol_type: str = 'dex', config=None, logger=None):
        super().__init__(port, "web3_defi_protocol", config=config, logger=logger)
        self.protocol_type = protocol_type
        self.swap_history = defaultdict(list)
        
    def handle_flash_loan(self, token: str, amount: int) -> Dict[str, Any]:
        """Detect flash loan attack attempts (HIGH VALUE)"""
        details = {
            "method": "flash_loan",
            "token": token,
            "amount": str(amount),
            "src_host": "192.168.1.100"
        }
        
        self.log_attack("defi_flash_loan_attack", details, severity="high")
        self.generate_reward("defi_flash_loan_attack", 200)
        
        return {
            "detected": True,
            "attack_type": "defi_flash_loan_attack",
            "severity": "high",
            "reward": 200
        }
    
    def handle_contract_call(self, contract_address: str, data: str, recursive: bool = False) -> Dict[str, Any]:
        """Detect reentrancy attack attempts"""
        if recursive or len(data) > 200:
            details = {
                "method": "contract_call",
                "contract": contract_address,
                "recursive": recursive,
                "src_host": "192.168.1.100"
            }
            
            self.log_attack("defi_reentrancy_attempt", details, severity="high")
            self.generate_reward("defi_reentrancy_attempt", 180)
            
            return {
                "detected": True,
                "attack_type": "defi_reentrancy_attempt",
                "reward": 180
            }
        
        return {"detected": False}
    
    def handle_swap(self, token_in: str, token_out: str, amount: int, slippage: int = 1) -> Dict[str, Any]:
        """Detect swap manipulation and sandwich attacks"""
        swap_key = "-".join(sorted([token_in, token_out]))
        self.swap_history[swap_key].append({
            "timestamp": time.time(),
            "amount": amount,
            "slippage": slippage
        })
        
        if self.is_sandwich_attack_detected():
            details = {
                "method": "swap",
                "attack_type": "sandwich_attack",
                "src_host": "192.168.1.100"
            }
            self.log_attack("defi_sandwich_attack", details, severity="medium")
            self.generate_reward("defi_sandwich_attack", 100)
        
        # Detect price manipulation (very large swap)
        if amount > 1000000 * 10**18:
            details = {
                "method": "swap",
                "token_in": token_in,
                "token_out": token_out,
                "amount": str(amount),
                "src_host": "192.168.1.100"
            }
            
            self.log_attack("defi_price_manipulation", details, severity="high")
            
            return {
                "detected": True,
                "suspicious_patterns": ["price_manipulation"],
                "attack_type": "defi_price_manipulation"
            }
        
        return {"detected": False}
    
    def is_sandwich_attack_detected(self) -> bool:
        """Detect sandwich attack pattern"""
        # Check for rapid back-and-forth swaps
        for swaps in self.swap_history.values():
            if len(swaps) >= 2:
                recent = [s for s in swaps if time.time() - s["timestamp"] < 10]
                if len(recent) >= 2:
                    return True
        return False
