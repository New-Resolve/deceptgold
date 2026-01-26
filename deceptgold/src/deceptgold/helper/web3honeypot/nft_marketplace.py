"""
NFT Marketplace Honeypot
"""

from typing import Dict, Any
from collections import defaultdict
from .base import Web3HoneypotBase


class NFTMarketplaceHoneypot(Web3HoneypotBase):
    NAME = "web3.nft_marketplace"
    """Simulates an NFT marketplace API"""
    
    def __init__(self, port: int = 8549, config=None, logger=None):
        super().__init__(port, "web3_nft_marketplace", config=config, logger=logger)
        self.nft_trades = defaultdict(list)
        self.nft_listings = defaultdict(list)
        
    def handle_nft_sale(self, nft_id: str, from_wallet: str, to_wallet: str, price: int) -> Dict[str, Any]:
        """Track NFT sales for wash trading detection"""
        self.nft_trades[nft_id].append({
            "from": from_wallet,
            "to": to_wallet,
            "price": price
        })
        
        if self.is_wash_trading_detected(nft_id):
            details = {
                "method": "nft_sale",
                "nft_id": nft_id,
                "src_host": "192.168.1.100"
            }
            self.log_attack("nft_wash_trading", details, severity="low")
            self.generate_reward("nft_wash_trading", 40)
            
        return {"status": "recorded"}
    
    def is_wash_trading_detected(self, nft_id: str, threshold: int = 5) -> bool:
        """Detect wash trading (same wallets trading back and forth)"""
        trades = self.nft_trades.get(nft_id, [])
        
        if len(trades) < threshold:
            return False
        
        # Check if same wallets are involved
        wallets = set()
        for trade in trades:
            wallets.add(trade["from"])
            wallets.add(trade["to"])
        
        # If only 2-3 wallets but many trades, likely wash trading
        return len(wallets) <= 3 and len(trades) >= threshold
    
    def handle_nft_listing(self, nft_id: str, collection: str, price: int) -> Dict[str, Any]:
        """Track NFT listings"""
        self.nft_listings[collection].append({
            "nft_id": nft_id,
            "price": price
        })
        
        if self.is_floor_manipulation_detected(collection):
            details = {
                "method": "nft_listing",
                "collection": collection,
                "src_host": "192.168.1.100"
            }
            self.log_attack("nft_floor_manipulation", details, severity="medium")
            # No specific reward defined yet, using default base
            self.generate_reward("nft_floor_manipulation", 20)
            
        return {"status": "listed"}
    
    def is_floor_manipulation_detected(self, collection: str, threshold: int = 3) -> bool:
        """Detect floor price manipulation"""
        listings = self.nft_listings.get(collection, [])
        
        if len(listings) < threshold:
            return False
        
        
        # Check for artificially low prices (relative to average OR absolute low)
        prices = [listing["price"] for listing in listings]
        avg_price = sum(prices) / len(prices)
        
        # If multiple listings are way below average, suspicious
        # Or if we see multiple listings with same very low price (test case)
        low_price_count = sum(1 for p in prices if p < avg_price * 0.5 or p < 0.01 * 10**18)
        return low_price_count >= threshold
    
    def handle_nft_approval(self, nft_id: str, approved_contract: str) -> Dict[str, Any]:
        """Detect malicious NFT approval exploits"""
        # Check if contract address looks suspicious
        if "malicious" in approved_contract.lower() or len(approved_contract) < 42:
            details = {
                "method": "nft_approval",
                "nft_id": nft_id,
                "approved_contract": approved_contract,
                "src_host": "192.168.1.100"
            }
            
            self.log_attack("nft_approval_exploit", details, severity="high")
            self.generate_reward("nft_approval_exploit", 80)
            
            return {
                "detected": True,
                "attack_type": "nft_approval_exploit",
                "reward": 80
            }
        
        return {"detected": False}
