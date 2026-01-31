# Architecture Overview

This document provides a comprehensive overview of the Deceptgold system architecture, explaining how components interact to transform cyber attacks into valuable digital assets.

## Table of Contents

- [System Overview](#system-overview)
- [Core Components](#core-components)
- [Data Flow](#data-flow)
- [Smart Contract Architecture](#smart-contract-architecture)
- [Security Design](#security-design)
- [Technology Stack](#technology-stack)
- [Deployment Architecture](#deployment-architecture)

## System Overview

Deceptgold is a next-generation cybersecurity platform that monetizes cyber attacks through a sophisticated deception and tokenization system.

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Deceptgold System                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐   │
│  │   Honeypot   │────▶│  Signature   │────▶|  Blockchain  │   |
│  │    System    │      │  Validation  │      │  Integration │   │
│  │ (OpenCanary) │      │   (ECDSA)    │      │   (Web3)     │   │
│  └──────────────┘      └──────────────┘      └──────────────┘   │
│         │                      │                      │         │
│         ▼                      ▼                      ▼         │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐   │
│  │   Attack     │      │    Crypto    │      │    Token     │   │
│  │   Logging    │      │   Signing    │      │   Minting    │   │
│  └──────────────┘      └──────────────┘      └──────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Key Principles

1. **Deception-First**: Deploy realistic honeypots to attract attackers
2. **Cryptographic Integrity**: Every attack is cryptographically signed
3. **Blockchain Validation**: Smart contracts verify and tokenize attacks
4. **Anti-Farming**: Multiple mechanisms prevent self-farming
5. **Privacy-Preserving**: User data is anonymized and protected

## Core Components

### 1. CLI Application Layer

**Technology**: Cyclopts (Python CLI framework)

**Purpose**: User interface for all system operations

**Key Files**:
- `src/deceptgold/__main__.py` - Application entry point
- `src/deceptgold/commands/` - Command implementations

**Commands**:
```
deceptgold
├── user              # User management
│   ├── create        # Create new user account
│   ├── wallet        # Manage crypto wallet
│   └── config        # User configuration
├── service           # Service control
│   ├── start         # Start honeypot service
│   ├── stop          # Stop honeypot service
│   └── status        # Check service status
└── notify            # Notifications
    ├── telemetry     # Send telemetry data
    └── alerts        # Configure alerts
```

**Architecture**:
```python
# Application initialization flow
init_app()
  ├─ Load configuration
  ├─ Initialize logging
  ├─ Register commands (user, service, notify)
  ├─ Execute telemetry
  └─ Run CLI application
```

### 2. Honeypot System

**Technology**: OpenCanary (customized)

**Purpose**: Attract and log attack attempts

**Key Files**:
- `src/deceptgold/helper/opencanary/` - Honeypot implementation
- `src/deceptgold/helper/opencanary/proxy_logger.py` - Custom logging

**Supported Services**:
- SSH (port 22)
- HTTP/HTTPS (ports 80/443)
- FTP (port 21)
- MySQL (port 3306)
- SMB (port 445)
- And more...

**Attack Detection Flow**:
```
Attacker → Honeypot Service → Attack Detected → Log Entry Created
                                                        ↓
                                                 Signature Added
                                                        ↓
                                                 Validation Queue
```

**Log Format**:
```json
{
  "timestamp": "2025-12-22T19:58:22Z",
  "source_ip": "192.168.1.100",
  "service": "ssh",
  "attack_type": "brute_force",
  "requests_count": 1500,
  "fingerprint": "system_unique_id",
  "signature": "0x..."
}
```

### 3. Cryptographic Signature System

**Technology**: ECDSA (Elliptic Curve Digital Signature Algorithm)

**Purpose**: Ensure attack logs are authentic and tamper-proof

**Key Files**:
- `src/deceptgold/helper/signature.py` - Signature generation/validation

**Process**:

1. **Attack Log Creation**:
   ```python
   attack_data = {
       "timestamp": current_time,
       "source_ip": attacker_ip,
       "service": "ssh",
       "requests": 1500
   }
   ```

2. **Serialization**:
   ```python
   message = json.dumps(attack_data, sort_keys=True)
   ```

3. **Hashing** (Keccak-256):
   ```python
   message_hash = keccak_256(message.encode())
   ```

4. **Signing** (ECDSA):
   ```python
   signature = private_key.sign(message_hash)
   ```

5. **Verification** (on-chain):
   ```solidity
   function verifySignature(
       bytes32 messageHash,
       bytes memory signature
   ) public view returns (bool) {
       address signer = ecrecover(messageHash, signature);
       return signer == authorizedSigner;
   }
   ```

**Security Properties**:
- **Authenticity**: Only Deceptgold instances can sign logs
- **Integrity**: Any tampering invalidates the signature
- **Non-repudiation**: Signatures prove origin
- **Privacy**: Private key is obfuscated in compiled code

### 4. Blockchain Integration

**Technology**: Web3.py, Ethereum-compatible networks

**Purpose**: Tokenize verified attacks on-chain

**Key Files**:
- `src/deceptgold/helper/blockchain/` - Web3 integration

**Supported Networks**:
- Ethereum Mainnet
- Polygon
- Binance Smart Chain
- Testnets (Sepolia, Mumbai, etc.)

**Smart Contract Interaction**:

```python
from web3 import Web3

# Connect to network
w3 = Web3(Web3.HTTPProvider(rpc_url))

# Load contract
contract = w3.eth.contract(
    address=contract_address,
    abi=contract_abi
)

# Submit attack for tokenization
tx = contract.functions.mintTokens(
    attack_hash,
    signature,
    reward_amount
).build_transaction({
    'from': user_address,
    'nonce': w3.eth.get_transaction_count(user_address)
})

# Sign and send
signed_tx = w3.eth.account.sign_transaction(tx, private_key)
tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
```

### 5. Fingerprinting and Anti-Farming

**Technology**: Custom system identification

**Purpose**: Prevent users from farming their own tokens

**Key Files**:
- `src/deceptgold/helper/fingerprint.py` - System fingerprinting

**Mechanisms**:

1. **System Fingerprinting**:
   - Hardware identifiers (MAC address, CPU ID)
   - System configuration hash
   - Installation timestamp
   - Geographic location (optional)

2. **Rate Limiting**:
   - Maximum requests per IP per hour
   - Maximum tokens per system per day
   - Cooldown periods between claims

3. **Behavioral Analysis**:
   - Attack pattern recognition
   - Timing analysis (too regular = suspicious)
   - Source diversity requirements

4. **On-Chain Validation**:
   - Smart contract checks fingerprint uniqueness
   - Rejects duplicate or suspicious patterns

**Anti-Farming Flow**:
```
Attack Log → Fingerprint Check → Rate Limit Check → Pattern Analysis
                ↓                      ↓                    ↓
            Unique?              Within Limits?        Natural Pattern?
                ↓                      ↓                    ↓
                └──────────────────────┴────────────────────┘
                                       ↓
                              Valid or Rejected
```

### 6. Configuration Management

**Key Files**:
- `src/deceptgold/configuration/` - Config management
- `src/deceptgold/resources/config/` - Config templates

**Configuration Hierarchy**:
```
System Defaults
    ↓
User Configuration (~/.deceptgold/config.json)
    ↓
Environment Variables
    ↓
Command-Line Arguments
```

**Key Settings**:
- Blockchain network and RPC endpoint
- Honeypot services to enable
- Logging verbosity and retention
- Wallet configuration
- Telemetry preferences

## Data Flow

### End-to-End Attack Processing

```
┌─────────────┐
│   Attacker  │
└──────┬──────┘
       │ 1. Attack Attempt
       ▼
┌─────────────────────┐
│  Honeypot Service   │
│   (OpenCanary)      │
└──────┬──────────────┘
       │ 2. Log Attack
       ▼
┌─────────────────────┐
│   Attack Logger     │
│  (Custom Handler)   │
└──────┬──────────────┘
       │ 3. Create Log Entry
       ▼
┌─────────────────────┐
│ Fingerprint System  │
│  (Anti-Farming)     │
└──────┬──────────────┘
       │ 4. Add System ID
       ▼
┌─────────────────────┐
│  Signature Module   │
│      (ECDSA)        │
└──────┬──────────────┘
       │ 5. Sign Log
       ▼
┌─────────────────────┐
│   Local Storage     │
│  (Queue for TX)     │
└──────┬──────────────┘
       │ 6. Batch Ready
       ▼
┌─────────────────────┐
│  Blockchain Client  │
│      (Web3)         │
└──────┬──────────────┘
       │ 7. Submit Transaction
       ▼
┌─────────────────────┐
│  Smart Contract     │
│  (Validation)       │
└──────┬──────────────┘
       │ 8. Verify Signature
       ▼
┌─────────────────────┐
│  Smart Contract     │
│   (Minting)         │
└──────┬──────────────┘
       │ 9. Mint Tokens
       ▼
┌─────────────────────┐
│   User Wallet       │
│  (ERC-20 Tokens)    │
└─────────────────────┘
```

### Data Persistence

**Local Storage**:
- Attack logs: `/var/log/deceptgold/attacks.log`
- Configuration: `~/.deceptgold/config.json`
- Wallet keystore: `~/.deceptgold/keystore/`
- Pending transactions: `~/.deceptgold/queue/`

**Blockchain Storage**:
- Token balances: ERC-20 contract state
- Attack hashes: Validation contract storage
- Signature records: Immutable on-chain logs

## Smart Contract Architecture

### Dual Contract System

Deceptgold uses two smart contracts for security and modularity:

#### 1. Token Contract (ERC-20)

**Purpose**: Manage token supply and transfers

**Key Functions**:
```solidity
contract DeceptgoldToken is ERC20 {
    address public minter;
    
    function mint(address to, uint256 amount) external {
        require(msg.sender == minter, "Only minter");
        _mint(to, amount);
    }
    
    function burn(uint256 amount) external {
        _burn(msg.sender, amount);
    }
}
```

**Features**:
- Standard ERC-20 implementation
- Controlled minting (only validation contract can mint)
- Burnable for utility consumption
- Transfer restrictions (optional)

#### 2. Validation Contract

**Purpose**: Verify attack signatures and authorize minting

**Key Functions**:
```solidity
contract AttackValidator {
    address public authorizedSigner;
    mapping(bytes32 => bool) public processedAttacks;
    DeceptgoldToken public token;
    
    function validateAndMint(
        bytes32 attackHash,
        bytes memory signature,
        address recipient,
        uint256 reward
    ) external {
        // 1. Verify signature
        require(
            verifySignature(attackHash, signature),
            "Invalid signature"
        );
        
        // 2. Check not already processed
        require(
            !processedAttacks[attackHash],
            "Already processed"
        );
        
        // 3. Mark as processed
        processedAttacks[attackHash] = true;
        
        // 4. Mint tokens
        token.mint(recipient, reward);
        
        emit AttackTokenized(attackHash, recipient, reward);
    }
    
    function verifySignature(
        bytes32 messageHash,
        bytes memory signature
    ) internal view returns (bool) {
        address signer = ecrecover(messageHash, signature);
        return signer == authorizedSigner;
    }
}
```

**Security Features**:
- Signature verification (ecrecover)
- Replay protection (processedAttacks mapping)
- Single authorized signer
- Event logging for transparency

### Token Economics

**Reward Calculation**:
```
Token Reward = f(attack_type, requests_count, ip_diversity, service_value)

Example:
- SSH brute force (1000 requests) = 10 tokens
- DDoS attempt (1M requests) = 1000 tokens
- Multi-service attack = bonus multiplier
```

See [documentation/Rewards.md](documentation/Rewards.md) for details.

## Security Design

### Multi-Layer Security

1. **Code Obfuscation** (PyArmor)
   - Protects private key embedded in code
   - Prevents reverse engineering
   - Platform-specific compilation

2. **Cryptographic Signing** (ECDSA)
   - Every attack log is signed
   - Signatures verified on-chain
   - Keccak-256 hashing

3. **Anti-Farming Mechanisms**
   - System fingerprinting
   - Rate limiting
   - Behavioral analysis
   - On-chain duplicate detection

4. **Smart Contract Security**
   - Replay protection
   - Access control
   - Event logging
   - Upgradeable design (optional)

### Threat Model

**Protected Against**:
- ✅ Self-farming (fingerprinting + rate limits)
- ✅ Log tampering (cryptographic signatures)
- ✅ Replay attacks (on-chain tracking)
- ✅ Unauthorized minting (signature verification)
- ✅ Private key extraction (code obfuscation)

**Potential Risks**:
- ⚠️ Sophisticated reverse engineering (mitigated by obfuscation)
- ⚠️ Distributed self-farming (mitigated by behavioral analysis)
- ⚠️ Smart contract vulnerabilities (mitigated by audits)

## Technology Stack

### Core Technologies

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Language | Python 3.11+ | Core implementation |
| CLI Framework | Cyclopts | Command-line interface |
| Honeypot | OpenCanary | Attack detection |
| Blockchain | Web3.py | Ethereum interaction |
| Cryptography | ecdsa, eth-account | Signature generation |
| Packaging | Briefcase | Multi-platform builds |
| Obfuscation | PyArmor | Code protection |
| Dependency Mgmt | Poetry | Python packages |

### Key Dependencies

```toml
[tool.poetry.dependencies]
python = "^3.11"
cyclopts = "^3.11.1"        # CLI framework
opencanary = "^0.9.5"       # Honeypot system
web3 = "^7.11.1"            # Blockchain integration
ecdsa = "^0.19.1"           # Cryptographic signing
eth-account = "^0.13.7"     # Ethereum accounts
qrcode-terminal = "^0.8"    # QR code display
briefcase = "^0.3.22"       # Application packaging
pyarmor = "^9.1.6"          # Code obfuscation
```

## Deployment Architecture

### Deployment Models

#### 1. On-Premises Deployment
```
Enterprise Network
├── DMZ
│   └── Deceptgold Honeypots (multiple instances)
├── Internal Network
│   └── Deceptgold Management Server
└── Blockchain Connection
    └── RPC Node (self-hosted or provider)
```

#### 2. Cloud Deployment
```
Cloud Provider (AWS/GCP/Azure)
├── VPC
│   ├── Public Subnet
│   │   └── Honeypot Instances (auto-scaling)
│   └── Private Subnet
│       └── Management & Logging
└── Blockchain
    └── Managed RPC (Infura/Alchemy)
```

#### 3. Hybrid Deployment
```
On-Premises Honeypots ─┐
Cloud Honeypots ────────┼─→ Centralized Logging ─→ Blockchain
Edge Honeypots ─────────┘
```

### Scalability Considerations

**Horizontal Scaling**:
- Deploy multiple honeypot instances
- Each instance has unique fingerprint
- Centralized log aggregation
- Batch transaction submission

**Performance**:
- Async attack logging
- Transaction batching (reduce gas costs)
- Local queue for offline resilience
- Efficient signature generation

### Monitoring and Observability

**Metrics**:
- Attacks detected per hour
- Tokens minted per day
- Service uptime
- Blockchain transaction status

**Logging**:
- Attack logs (structured JSON)
- Application logs (errors, warnings)
- Blockchain transaction logs
- Telemetry data (optional)

**Alerts**:
- Service downtime
- Blockchain connection issues
- Suspicious farming patterns
- Low token balance (for gas)

## Future Architecture Enhancements

### Planned Improvements

1. **Distributed Architecture**
   - Peer-to-peer attack sharing
   - Decentralized validation
   - Cross-organization intelligence

2. **Advanced Analytics**
   - Machine learning for attack classification
   - Predictive threat modeling
   - Automated response recommendations

3. **Multi-Chain Support**
   - Layer 2 solutions (Arbitrum, Optimism)
   - Cross-chain bridges
   - Multi-token rewards

4. **Enhanced Privacy**
   - Zero-knowledge proofs for validation
   - Confidential transactions
   - Anonymous attack reporting

## References

- [Development.md](Development.md) - Development setup and workflow
- [Contributing.md](Contributing.md) - Contribution guidelines
- [documentation/Whitepaper.md](documentation/Whitepaper.md) - Project vision
- [ERC-20 Standard](https://eips.ethereum.org/EIPS/eip-20)
- [OpenCanary Documentation](https://github.com/thinkst/opencanary)

---

**Questions or suggestions?** Contact: jsmorais@pm.me
