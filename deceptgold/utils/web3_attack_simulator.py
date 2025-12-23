"""
Attack simulation scripts for Web3 honeypots

This module provides scripts to simulate various Web3 attacks for testing purposes.
Use these to validate that honeypots correctly detect and log attacks.
"""

import requests
import json
import time
from web3 import Web3
from eth_account import Account


class Web3AttackSimulator:
    """Simulates various Web3 attacks for testing honeypots"""
    
    def __init__(self, honeypot_host='localhost'):
        self.honeypot_host = honeypot_host
        self.session = requests.Session()
    
    def simulate_rpc_account_unlock(self, port=8545):
        """
        Simulate personal_unlockAccount attack
        This is a critical attack that should generate high rewards
        """
        print("[*] Simulating RPC account unlock attack...")
        
        url = f"http://{self.honeypot_host}:{port}"
        payload = {
            "jsonrpc": "2.0",
            "method": "personal_unlockAccount",
            "params": [
                "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
                "password123",
                300
            ],
            "id": 1
        }
        
        response = self.session.post(url, json=payload)
        print(f"[+] Response: {response.status_code}")
        print(f"[+] Data: {response.json()}")
        
        return response.json()
    
    def simulate_balance_scanning(self, port=8545, num_addresses=100):
        """
        Simulate address balance scanning
        This should be detected as reconnaissance
        """
        print(f"[*] Simulating balance scanning ({num_addresses} addresses)...")
        
        url = f"http://{self.honeypot_host}:{port}"
        
        for i in range(num_addresses):
            address = f"0x{'0' * 39}{i:x}"
            payload = {
                "jsonrpc": "2.0",
                "method": "eth_getBalance",
                "params": [address, "latest"],
                "id": i
            }
            
            response = self.session.post(url, json=payload)
            if i % 10 == 0:
                print(f"[+] Scanned {i} addresses...")
            
            time.sleep(0.1)  # Small delay to avoid overwhelming
        
        print(f"[+] Scanning complete!")
    
    def simulate_malicious_transaction(self, port=8545):
        """
        Simulate sending a malicious raw transaction
        """
        print("[*] Simulating malicious transaction...")
        
        # Create a fake transaction
        w3 = Web3()
        account = Account.create()
        
        tx = {
            'nonce': 0,
            'gasPrice': w3.to_wei('50', 'gwei'),
            'gas': 21000,
            'to': '0x0000000000000000000000000000000000000000',  # Burn address
            'value': w3.to_wei('100', 'ether'),  # High value
            'data': b'',
            'chainId': 56
        }
        
        signed = account.sign_transaction(tx)
        raw_tx = signed.rawTransaction.hex()
        
        url = f"http://{self.honeypot_host}:{port}"
        payload = {
            "jsonrpc": "2.0",
            "method": "eth_sendRawTransaction",
            "params": [raw_tx],
            "id": 1
        }
        
        response = self.session.post(url, json=payload)
        print(f"[+] Response: {response.status_code}")
        print(f"[+] Data: {response.json()}")
    
    def simulate_wallet_seed_phishing(self, port=8546):
        """
        Simulate seed phrase phishing attempt
        This is a CRITICAL attack
        """
        print("[*] Simulating wallet seed phrase phishing...")
        
        url = f"http://{self.honeypot_host}:{port}/api/v1/wallet/import"
        
        # Fake seed phrase (never use real ones!)
        fake_seed = "abandon abandon abandon abandon abandon abandon " + \
                   "abandon abandon abandon abandon abandon art"
        
        payload = {
            "seed_phrase": fake_seed
        }
        
        response = self.session.post(url, json=payload)
        print(f"[+] Response: {response.status_code}")
        print(f"[+] Data: {response.json()}")
    
    def simulate_private_key_export(self, port=8546):
        """
        Simulate private key export attempt
        """
        print("[*] Simulating private key export...")
        
        url = f"http://{self.honeypot_host}:{port}/api/v1/wallet/export"
        
        payload = {
            "wallet_id": "wallet_123",
            "password": "password123"
        }
        
        response = self.session.post(url, json=payload)
        print(f"[+] Response: {response.status_code}")
        print(f"[+] Data: {response.json()}")
    
    def simulate_ipfs_malicious_upload(self, port=5001):
        """
        Simulate malicious file upload to IPFS
        """
        print("[*] Simulating IPFS malicious upload...")
        
        url = f"http://{self.honeypot_host}:{port}/api/v0/add"
        
        # Malicious HTML with XSS
        malicious_content = b"<script>alert('XSS Attack!')</script>"
        
        files = {
            'file': ('malicious.html', malicious_content)
        }
        
        response = self.session.post(url, files=files)
        print(f"[+] Response: {response.status_code}")
        print(f"[+] Data: {response.text}")
    
    def simulate_ipfs_path_traversal(self, port=8080):
        """
        Simulate path traversal attack on IPFS gateway
        """
        print("[*] Simulating IPFS path traversal...")
        
        malicious_paths = [
            "../../../etc/passwd",
            "../../.ssh/id_rsa",
            "../config/secrets.json"
        ]
        
        for path in malicious_paths:
            url = f"http://{self.honeypot_host}:{port}/ipfs/{path}"
            response = self.session.get(url)
            print(f"[+] Tried: {path} - Status: {response.status_code}")
    
    def simulate_flash_loan_attack(self, port=8548):
        """
        Simulate DeFi flash loan attack
        This should generate VERY HIGH rewards (200+ DGLD)
        """
        print("[*] Simulating flash loan attack...")
        
        url = f"http://{self.honeypot_host}:{port}/api/v1/flashloan"
        
        payload = {
            "token": "0x1234567890123456789012345678901234567890",
            "amount": str(1000000 * 10**18),  # 1M tokens
            "callback_data": "0x" + "a" * 200
        }
        
        response = self.session.post(url, json=payload)
        print(f"[+] Response: {response.status_code}")
        print(f"[+] Data: {response.json()}")
    
    def simulate_reentrancy_attack(self, port=8548):
        """
        Simulate reentrancy attack on DeFi protocol
        """
        print("[*] Simulating reentrancy attack...")
        
        url = f"http://{self.honeypot_host}:{port}/api/v1/withdraw"
        
        # Simulate recursive withdrawal
        payload = {
            "amount": str(100 * 10**18),
            "recursive": True,
            "callback": "malicious_contract_address"
        }
        
        response = self.session.post(url, json=payload)
        print(f"[+] Response: {response.status_code}")
        print(f"[+] Data: {response.json()}")
    
    def simulate_sandwich_attack(self, port=8548):
        """
        Simulate sandwich attack (front-running + back-running)
        """
        print("[*] Simulating sandwich attack...")
        
        url = f"http://{self.honeypot_host}:{port}/api/v1/swap"
        
        # Front-run
        payload1 = {
            "token_in": "0xToken1",
            "token_out": "0xToken2",
            "amount": str(100 * 10**18),
            "slippage": 50  # High slippage
        }
        
        print("[+] Front-running transaction...")
        response1 = self.session.post(url, json=payload1)
        
        time.sleep(1)  # Victim transaction would be here
        
        # Back-run
        payload2 = {
            "token_in": "0xToken2",
            "token_out": "0xToken1",
            "amount": str(100 * 10**18),
            "slippage": 50
        }
        
        print("[+] Back-running transaction...")
        response2 = self.session.post(url, json=payload2)
        
        print(f"[+] Sandwich attack complete!")
    
    def simulate_nft_wash_trading(self, port=8549):
        """
        Simulate NFT wash trading
        """
        print("[*] Simulating NFT wash trading...")
        
        url = f"http://{self.honeypot_host}:{port}/api/v1/nft/sale"
        
        wallet1 = "0xWallet1"
        wallet2 = "0xWallet2"
        nft_id = "nft_123"
        
        # Trade back and forth to inflate volume
        for i in range(10):
            if i % 2 == 0:
                payload = {
                    "nft_id": nft_id,
                    "from": wallet1,
                    "to": wallet2,
                    "price": str(1 * 10**18)
                }
            else:
                payload = {
                    "nft_id": nft_id,
                    "from": wallet2,
                    "to": wallet1,
                    "price": str(1.1 * 10**18)
                }
            
            response = self.session.post(url, json=payload)
            print(f"[+] Trade {i+1}/10 - Status: {response.status_code}")
            time.sleep(0.5)
    
    def simulate_explorer_api_scraping(self, port=8547):
        """
        Simulate API scraping on blockchain explorer
        """
        print("[*] Simulating explorer API scraping...")
        
        base_url = f"http://{self.honeypot_host}:{port}/api"
        
        # Rapid API calls to scrape data
        for i in range(100):
            params = {
                "module": "account",
                "action": "balance",
                "address": f"0x{'0' * 39}{i:x}"
            }
            
            response = self.session.get(base_url, params=params)
            
            if i % 10 == 0:
                print(f"[+] Scraped {i} addresses...")
            
            time.sleep(0.05)  # Very fast requests
        
        print(f"[+] Scraping complete!")
    
    def run_all_attacks(self):
        """
        Run all attack simulations
        """
        print("=" * 60)
        print("RUNNING ALL WEB3 ATTACK SIMULATIONS")
        print("=" * 60)
        
        attacks = [
            ("RPC Account Unlock", lambda: self.simulate_rpc_account_unlock()),
            ("Balance Scanning", lambda: self.simulate_balance_scanning(num_addresses=50)),
            ("Malicious Transaction", lambda: self.simulate_malicious_transaction()),
            ("Wallet Seed Phishing", lambda: self.simulate_wallet_seed_phishing()),
            ("Private Key Export", lambda: self.simulate_private_key_export()),
            ("IPFS Malicious Upload", lambda: self.simulate_ipfs_malicious_upload()),
            ("IPFS Path Traversal", lambda: self.simulate_ipfs_path_traversal()),
            ("Flash Loan Attack", lambda: self.simulate_flash_loan_attack()),
            ("Reentrancy Attack", lambda: self.simulate_reentrancy_attack()),
            ("Sandwich Attack", lambda: self.simulate_sandwich_attack()),
            ("NFT Wash Trading", lambda: self.simulate_nft_wash_trading()),
            ("Explorer API Scraping", lambda: self.simulate_explorer_api_scraping()),
        ]
        
        for name, attack_func in attacks:
            print(f"\n{'=' * 60}")
            print(f"Attack: {name}")
            print(f"{'=' * 60}")
            
            try:
                attack_func()
                print(f"[✓] {name} completed successfully")
            except Exception as e:
                print(f"[✗] {name} failed: {e}")
            
            time.sleep(2)  # Pause between attacks
        
        print("\n" + "=" * 60)
        print("ALL ATTACK SIMULATIONS COMPLETE")
        print("=" * 60)


def main():
    """Main function to run attack simulations"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Web3 Honeypot Attack Simulator')
    parser.add_argument('--host', default='localhost', help='Honeypot host')
    parser.add_argument('--attack', choices=[
        'rpc_unlock', 'balance_scan', 'malicious_tx', 'seed_phishing',
        'key_export', 'ipfs_upload', 'ipfs_traversal', 'flash_loan',
        'reentrancy', 'sandwich', 'wash_trading', 'api_scraping', 'all'
    ], default='all', help='Attack type to simulate')
    
    args = parser.parse_args()
    
    simulator = Web3AttackSimulator(honeypot_host=args.host)
    
    attack_map = {
        'rpc_unlock': simulator.simulate_rpc_account_unlock,
        'balance_scan': simulator.simulate_balance_scanning,
        'malicious_tx': simulator.simulate_malicious_transaction,
        'seed_phishing': simulator.simulate_wallet_seed_phishing,
        'key_export': simulator.simulate_private_key_export,
        'ipfs_upload': simulator.simulate_ipfs_malicious_upload,
        'ipfs_traversal': simulator.simulate_ipfs_path_traversal,
        'flash_loan': simulator.simulate_flash_loan_attack,
        'reentrancy': simulator.simulate_reentrancy_attack,
        'sandwich': simulator.simulate_sandwich_attack,
        'wash_trading': simulator.simulate_nft_wash_trading,
        'api_scraping': simulator.simulate_explorer_api_scraping,
        'all': simulator.run_all_attacks
    }
    
    attack_func = attack_map.get(args.attack)
    if attack_func:
        attack_func()
    else:
        print(f"Unknown attack type: {args.attack}")


if __name__ == '__main__':
    main()
