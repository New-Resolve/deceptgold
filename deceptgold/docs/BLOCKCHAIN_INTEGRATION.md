# Blockchain Integration Guide

Complete guide to understanding and working with Deceptgold's blockchain integration.

## Table of Contents

- [Overview](#overview)
- [Smart Contract Architecture](#smart-contract-architecture)
- [Cryptographic Signatures](#cryptographic-signatures)
- [Web3 Integration](#web3-integration)
- [Token Economics](#token-economics)
- [Network Configuration](#network-configuration)
- [Development and Testing](#development-and-testing)
- [Deployment](#deployment)

## Overview

Deceptgold uses blockchain technology to:

1. **Tokenize Attacks** - Convert verified attacks into ERC-20 tokens
2. **Ensure Integrity** - Cryptographically sign and verify attack logs
3. **Prevent Fraud** - On-chain validation prevents self-farming
4. **Enable Trading** - Tokens can be traded or used for intelligence access

### Technology Stack

- **Blockchain**: Ethereum-compatible networks (Ethereum, BSC, Polygon)
- **Token Standard**: ERC-20
- **Signature Algorithm**: ECDSA (Elliptic Curve Digital Signature Algorithm)
- **Hashing**: Keccak-256
- **Library**: Web3.py, eth-account, ecdsa

## Smart Contract Architecture

### Dual Contract System

Deceptgold uses two smart contracts for security and modularity:

#### 1. Token Contract (ERC-20)

**Purpose**: Manage DGLD token supply and transfers

**Key Functions**:
```solidity
// Standard ERC-20 functions
function balanceOf(address account) external view returns (uint256)
function transfer(address to, uint256 amount) external returns (bool)
function approve(address spender, uint256 amount) external returns (bool)

// Controlled minting
function mint(address to, uint256 amount) external onlyMinter
function burn(uint256 amount) external
```

**Contract Address** (BSC Testnet):
```
0x606c0fE69D437F42BfC11D3eec82F596cC02C02a
```

**Features**:
- Standard ERC-20 implementation
- Only validator contract can mint
- Users can burn tokens for utility
- Fully compatible with wallets and exchanges

#### 2. Validator Contract

**Purpose**: Verify attack signatures and authorize token minting

**Key Functions**:
```solidity
contract AttackValidator {
    address public authorizedSigner;
    address public tokenContract;
    mapping(bytes32 => bool) public processedAttacks;
    
    function validateAndMint(
        bytes32 attackHash,
        bytes memory signature,
        address recipient,
        uint256 reward
    ) external {
        // 1. Verify signature
        require(verifySignature(attackHash, signature), "Invalid signature");
        
        // 2. Check not already processed
        require(!processedAttacks[attackHash], "Already processed");
        
        // 3. Mark as processed
        processedAttacks[attackHash] = true;
        
        // 4. Mint tokens
        IDeceptgoldToken(tokenContract).mint(recipient, reward);
        
        emit AttackTokenized(attackHash, recipient, reward);
    }
    
    function verifySignature(
        bytes32 messageHash,
        bytes memory signature
    ) internal view returns (bool) {
        address signer = recoverSigner(messageHash, signature);
        return signer == authorizedSigner;
    }
}
```

**Contract Address** (BSC Testnet):
```
0x12485DAE42bFc5bF625f4Da5738847e79CFe2cAD
```

**Features**:
- ECDSA signature verification
- Replay attack protection
- Single authorized signer
- Event logging for transparency

### Contract Interaction Flow

```
Attack Detected
    ↓
Sign Attack Data (off-chain)
    ↓
Submit to Validator Contract
    ↓
Verify Signature (on-chain)
    ↓
Check Not Processed
    ↓
Mark as Processed
    ↓
Call Token Contract Mint
    ↓
Tokens Sent to User Wallet
```

## Cryptographic Signatures

### Signature Generation

**Process**:

1. **Serialize Attack Data**:
```python
import json

attack_data = {
    "timestamp": "2025-12-22T20:00:00Z",
    "source_ip": "192.168.1.100",
    "service": "ssh",
    "requests": 1000,
    "fingerprint": "unique_system_id"
}

# Canonical JSON (sorted keys)
message = json.dumps(attack_data, sort_keys=True)
```

2. **Hash Message** (Keccak-256):
```python
from eth_account.messages import encode_defunct
from web3 import Web3

# Create Ethereum-compatible message hash
message_hash = encode_defunct(text=message)
```

3. **Sign with Private Key**:
```python
from eth_account import Account

# Private key (embedded in obfuscated code)
private_key = "0x..."

# Sign
signed_message = Account.sign_message(message_hash, private_key)
signature = signed_message.signature.hex()
```

### Signature Verification

**On-Chain** (in smart contract):
```solidity
function recoverSigner(
    bytes32 messageHash,
    bytes memory signature
) internal pure returns (address) {
    bytes32 r;
    bytes32 s;
    uint8 v;
    
    // Extract signature components
    assembly {
        r := mload(add(signature, 32))
        s := mload(add(signature, 64))
        v := byte(0, mload(add(signature, 96)))
    }
    
    // Recover signer address
    return ecrecover(messageHash, v, r, s);
}
```

**Off-Chain** (for testing):
```python
from eth_account.messages import encode_defunct
from eth_account import Account

def verify_signature(message: str, signature: str, expected_address: str) -> bool:
    message_hash = encode_defunct(text=message)
    recovered_address = Account.recover_message(message_hash, signature=signature)
    return recovered_address.lower() == expected_address.lower()
```

### Security Considerations

**Private Key Protection**:
- Embedded in source code
- Protected by PyArmor obfuscation
- Platform-specific compilation
- Never transmitted or stored externally

**Signature Properties**:
- **Authenticity**: Only Deceptgold instances can sign
- **Integrity**: Tampering invalidates signature
- **Non-repudiation**: Signature proves origin
- **Uniqueness**: Each attack has unique signature

## Web3 Integration

### Connecting to Network

```python
from web3 import Web3

# RPC endpoint
rpc_url = "https://data-seed-prebsc-1-s1.binance.org:8545/"

# Create Web3 instance
w3 = Web3(Web3.HTTPProvider(rpc_url))

# Verify connection
if w3.is_connected():
    print(f"Connected to network: {w3.eth.chain_id}")
else:
    print("Connection failed")
```

### Loading Contracts

```python
import json
from web3 import Web3

# Load ABI
with open("TokenContract.abi.json") as f:
    token_abi = json.load(f)

# Contract address
token_address = Web3.to_checksum_address(
    "0x606c0fE69D437F42BfC11D3eec82F596cC02C02a"
)

# Create contract instance
token_contract = w3.eth.contract(
    address=token_address,
    abi=token_abi
)
```

### Reading Contract Data

```python
# Get token balance
user_address = Web3.to_checksum_address("0x...")
balance = token_contract.functions.balanceOf(user_address).call()

# Get token decimals
decimals = token_contract.functions.decimals().call()

# Format balance
balance_formatted = balance / (10 ** decimals)
print(f"Balance: {balance_formatted} DGLD")
```

### Submitting Transactions

```python
from eth_account import Account

# Prepare transaction
tx = validator_contract.functions.validateAndMint(
    attack_hash,
    signature,
    recipient_address,
    reward_amount
).build_transaction({
    'from': sender_address,
    'nonce': w3.eth.get_transaction_count(sender_address),
    'gas': 200000,
    'gasPrice': w3.eth.gas_price
})

# Sign transaction
signed_tx = Account.sign_transaction(tx, private_key)

# Send transaction
tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)

# Wait for confirmation
receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

if receipt['status'] == 1:
    print(f"Success! TX: {tx_hash.hex()}")
else:
    print(f"Failed! TX: {tx_hash.hex()}")
```

## Token Economics

### Reward Calculation

**Formula**:
```
Token Reward = base_reward × service_multiplier × volume_multiplier
```

**Base Rewards** (per attack type):
- SSH brute force: 10 DGLD
- HTTP flood: 5 DGLD
- FTP attempts: 8 DGLD
- MySQL probes: 12 DGLD
- SMB attacks: 15 DGLD

**Service Multiplier**:
- Single service: 1.0x
- 2-3 services: 1.2x
- 4+ services: 1.5x

**Volume Multiplier**:
```python
def calculate_volume_multiplier(requests: int) -> float:
    if requests < 100:
        return 0.5
    elif requests < 1000:
        return 1.0
    elif requests < 10000:
        return 1.5
    else:
        return 2.0
```

**Example**:
```
Attack: SSH brute force
Requests: 5000
Services: 1

Reward = 10 × 1.0 × 1.5 = 15 DGLD
```

### Token Utility

**Uses for DGLD Tokens**:

1. **Threat Intelligence Access**
   - IP reputation data
   - Attack pattern analysis
   - Geographic threat maps
   - Cost: 100 DGLD per month

2. **Premium Features**
   - Advanced analytics
   - Custom alerts
   - API access
   - Cost: 500 DGLD per month

3. **Trading**
   - Exchange for other cryptocurrencies
   - Peer-to-peer transfers
   - Liquidity pools

## Network Configuration

### Supported Networks

#### BSC Testnet (Default)
```python
{
    "network": "BSC Testnet",
    "rpc_url": "https://data-seed-prebsc-1-s1.binance.org:8545/",
    "chain_id": 97,
    "explorer": "https://testnet.bscscan.com",
    "token_address": "0x606c0fE69D437F42BfC11D3eec82F596cC02C02a",
    "validator_address": "0x12485DAE42bFc5bF625f4Da5738847e79CFe2cAD"
}
```

#### BSC Mainnet
```python
{
    "network": "BSC Mainnet",
    "rpc_url": "https://bsc-dataseed.binance.org/",
    "chain_id": 56,
    "explorer": "https://bscscan.com",
    "token_address": "TBD",
    "validator_address": "TBD"
}
```

#### Polygon
```python
{
    "network": "Polygon",
    "rpc_url": "https://polygon-rpc.com",
    "chain_id": 137,
    "explorer": "https://polygonscan.com",
    "token_address": "TBD",
    "validator_address": "TBD"
}
```

### Changing Networks

```python
from deceptgold.configuration.config_manager import update_config

# Update RPC endpoint
update_config('net_rpc', 'https://polygon-rpc.com', 'blockchain')

# Update contract addresses
update_config('contract_token_address', '0x...', 'blockchain')
update_config('contract_validator_address', '0x...', 'blockchain')
```

## Development and Testing

### Local Blockchain (Ganache)

```bash
# Install Ganache
npm install -g ganache

# Start local blockchain
ganache --port 8545 --deterministic

# Connect Deceptgold to local network
deceptgold config set blockchain.rpc_url http://localhost:8545
```

### Testnet Testing

**Get Testnet Tokens**:
1. Visit BSC Testnet Faucet: https://testnet.binance.org/faucet-smart
2. Enter your wallet address
3. Receive test BNB for gas fees

**Test Attack Submission**:
```python
# Simulate attack
attack_data = {
    "timestamp": "2025-12-22T20:00:00Z",
    "source_ip": "192.168.1.100",
    "service": "ssh",
    "requests": 1000
}

# Sign and submit
signature = sign_attack(attack_data)
tx_hash = submit_to_blockchain(attack_data, signature)

# Check on explorer
print(f"https://testnet.bscscan.com/tx/{tx_hash}")
```

### Unit Testing Blockchain Code

```python
import pytest
from unittest.mock import Mock, patch

@patch('web3.Web3')
def test_token_balance_query(mock_web3):
    """Test querying token balance."""
    # Setup mock
    mock_contract = Mock()
    mock_contract.functions.balanceOf.return_value.call.return_value = 1000000000000000000000
    mock_contract.functions.decimals.return_value.call.return_value = 18
    
    # Test
    balance = get_token_balance("0x123...", mock_contract)
    
    assert balance == 1000.0  # 1000 tokens
```

## Deployment

### Smart Contract Deployment

**Requirements**:
- Solidity compiler (solc)
- Deployment wallet with gas funds
- Network RPC endpoint

**Deployment Script**:
```python
from web3 import Web3
from solcx import compile_source

# Compile contract
with open("DeceptgoldToken.sol") as f:
    source = f.read()

compiled = compile_source(source)
contract_interface = compiled['<stdin>:DeceptgoldToken']

# Deploy
w3 = Web3(Web3.HTTPProvider(rpc_url))
Contract = w3.eth.contract(
    abi=contract_interface['abi'],
    bytecode=contract_interface['bin']
)

# Build transaction
tx = Contract.constructor().build_transaction({
    'from': deployer_address,
    'nonce': w3.eth.get_transaction_count(deployer_address),
    'gas': 3000000,
    'gasPrice': w3.eth.gas_price
})

# Sign and send
signed = w3.eth.account.sign_transaction(tx, private_key)
tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)

# Get contract address
receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
contract_address = receipt['contractAddress']

print(f"Contract deployed at: {contract_address}")
```

### Configuration Update

After deployment, update Deceptgold configuration:

```python
update_config('contract_token_address', contract_address, 'blockchain')
update_config('contract_validator_address', validator_address, 'blockchain')
update_config('key_public_expected_signer', signer_address, 'blockchain')
```

## Troubleshooting

### Common Issues

**Connection Failed**:
```python
# Check RPC endpoint
w3 = Web3(Web3.HTTPProvider(rpc_url))
print(f"Connected: {w3.is_connected()}")

# Try alternative RPC
alternative_rpc = "https://bsc-dataseed1.defibit.io/"
```

**Transaction Reverted**:
- Check gas limit (increase if needed)
- Verify signature is valid
- Ensure attack hash not already processed
- Check wallet has sufficient gas funds

**Invalid Signature**:
- Verify message format matches contract expectation
- Check private key matches authorized signer
- Ensure proper Keccak-256 hashing

## See Also

- [ARCHITECTURE.md](../ARCHITECTURE.md) - System architecture
- [API_REFERENCE.md](API_REFERENCE.md) - Command reference
- [TESTING.md](TESTING.md) - Testing guide
- [Whitepaper](../../documentation/whitepaper.md) - Project vision

---

**Questions?** Contact: contact@decept.gold
