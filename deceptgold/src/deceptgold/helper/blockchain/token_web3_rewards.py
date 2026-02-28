

# Web3 Attack Rewards
WEB3_ATTACK_REWARDS = {
    "rpc_malicious_transaction": 50,
    "rpc_account_unlock_attempt": 100,
    "wallet_seed_phrase_phishing": 150,
    "wallet_private_key_export": 120,
    "ipfs_malicious_upload": 30,
    "explorer_api_scraping": 20,
    "defi_flash_loan_attack": 200,
    "defi_reentrancy_attempt": 180,
    "nft_wash_trading": 40,
    "nft_approval_exploit": 80,
}


def calculate_web3_reward(attack_type: str, details: dict = None) -> int:
    """
    Calculate reward for Web3-specific attacks
    
    Args:
        attack_type: Type of Web3 attack detected
        details: Additional details about the attack
    
    Returns:
        int: Reward amount in DGLD tokens
    """
    if details is None:
        details = {}
    
    base_reward = WEB3_ATTACK_REWARDS.get(attack_type, 10)
    
    # Multipliers based on sophistication
    if details.get("automated_bot"):
        base_reward = int(base_reward * 1.5)
    
    if details.get("multiple_attempts"):
        base_reward = int(base_reward * 1.2)
    
    return base_reward
