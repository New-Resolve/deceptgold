"""
IPFS Gateway Honeypot
"""

from typing import Dict, Any
from .base import Web3HoneypotBase


class IPFSGatewayHoneypot(Web3HoneypotBase):
    NAME = "web3.ipfs_gateway"
    """Simulates an IPFS gateway"""
    
    def __init__(self, port: int = 8080, api_port: int = 5001, config=None, logger=None):
        super().__init__(port, "web3_ipfs_gateway", config=config, logger=logger)
        self.api_port = api_port
        self.upload_count = 0
        
    def handle_file_add(self, file_content: bytes, file_name: str) -> Dict[str, Any]:
        """Detect malicious file uploads"""
        self.upload_count += 1
        
        if self.is_dos_detected():
            details = {
                "method": "file_add",
                "upload_count": self.upload_count,
                "src_host": "192.168.1.100"
            }
            self.log_attack("ipfs_dos_attack", details, severity="medium")
            self.generate_reward("ipfs_dos_attack", 20)
        
        # Check for malicious content
        malicious_patterns = [b"<script>", b"alert(", b"eval("]
        is_malicious = any(pattern in file_content for pattern in malicious_patterns)
        
        if is_malicious:
            details = {
                "method": "file_add",
                "file_name": file_name,
                "file_size": len(file_content),
                "src_host": "192.168.1.100"
            }
            
            self.log_attack("ipfs_malicious_upload", details, severity="medium")
            self.generate_reward("ipfs_malicious_upload", 30)
            
            return {
                "detected": True,
                "attack_type": "ipfs_malicious_upload",
                "reward": 30
            }
        
        return {"detected": False}
    
    def handle_ipfs_get(self, cid: str) -> Dict[str, Any]:
        """Detect path traversal attempts"""
        path_traversal_patterns = ["../", "..\\\\", "/etc/", "/.ssh/"]
        is_traversal = any(pattern in cid for pattern in path_traversal_patterns)
        
        if is_traversal:
            details = {
                "method": "ipfs_get",
                "cid": cid,
                "src_host": "192.168.1.100"
            }
            
            self.log_attack("ipfs_path_traversal", details, severity="high")
            self.generate_reward("ipfs_path_traversal", 40)
            
            return {
                "detected": True,
                "attack_type": "ipfs_path_traversal",
                "reward": 40
            }
        
        return {"detected": False}
    
    def is_dos_detected(self, threshold: int = 500) -> bool:
        """Detect DoS via massive uploads"""
        return self.upload_count >= threshold
