# Deceptgold - Cyber Deception and Resource Inversion 


[![Build](https://github.com/new-resolve/deceptgold/actions/workflows/build.yml/badge.svg)](https://github.com/new-resolve/deceptgold/actions/workflows/build.yml)
![Last Commit](https://img.shields.io/github/last-commit/new-resolve/deceptgold)
[![Docs](https://img.shields.io/badge/docs-available-success)](https://github.com/New-Resolve/deceptgold/tree/master/deceptgold/docs)
![Python](https://img.shields.io/badge/python-3.12-blue?logo=python)
[![License: DeceptGold](https://img.shields.io/badge/License-DeceptGold-blue)](deceptgold/src/deceptgold/LICENSE)

---

Deceptgold is a next-generation platform designed to manage deception strategies and reclaim value from cyber attacks. While most organizations focus only on detection, logging, and mitigation, Deceptgold takes a radically different approach: it transforms the computational effort of intrusion attempts into valuable digital assets.

In today's threat landscape, companies suffer not only from data breaches but also from a massive waste of computational power during attacks. Countless CPU cycles, network bandwidth, and system resources are consumed by malicious actors — and traditionally, all this energy is simply lost.

## Deceptgold solves this problem.

By deploying deceptive environments that interact with attackers in a controlled and intelligent way, the system is able to capture and redirect the power of attacks, converting what would otherwise be waste into tangible assets for the defending organization. This turns an inherently negative event — being targeted — into a source of intelligence, strategic advantage, and even economic value.

Deceptgold is ideal for cybersecurity teams, researchers, and critical infrastructure defenders who want more than just alerts. It is built for those who believe that every intrusion attempt is an opportunity — not just a threat.

## 📚 Documentation

- **[Whitepaper](documentation/whitepaper.md)** - Project vision and technical details
- **[Architecture](ARCHITECTURE.md)** - System design and components
- **[Getting Started](deceptgold/docs/GETTING_STARTED.md)** - Quick start for developers
- **[API Reference](deceptgold/docs/API_REFERENCE.md)** - Complete command reference

## 🚀 Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/new-resolve/deceptgold.git
cd deceptgold/deceptgold

# Install dependencies
poetry install
poetry shell

# Run application
poetry run briefcase dev --
```

### Basic Usage

```bash
# Configure wallet address
deceptgold user --my-address 0xYourWalletAddress

# Start honeypot service
deceptgold service start

# Check status
deceptgold service status

# View token balance
deceptgold user --show-balance
```

## 🛠️ For Developers

### Contributing

We welcome contributions! Please read our guidelines:

- **[Contributing Guide](CONTRIBUTING.md)** - How to contribute
- **[Development Guide](DEVELOPMENT.md)** - Setup and workflow
- **[Testing Guide](deceptgold/docs/TESTING.md)** - Testing procedures

### Development Setup

```bash
# Install development dependencies
poetry install --with dev,docs

# Run tests
poetry run pytest

# Build documentation
poetry run mkdocs serve
```

### Key Resources

- **[Architecture Overview](ARCHITECTURE.md)** - System design
- **[Blockchain Integration](deceptgold/docs/BLOCKCHAIN_INTEGRATION.md)** - Smart contracts and Web3
- **[Testing Guide](deceptgold/docs/TESTING.md)** - Test structure and examples

## 💡 How It Works

![attacks_revenue.png](documentation/assets/attacks_revenue.png)

<<<<<<< HEAD
Help fund the project with crowdfunding: `0x99eF54CDe7EaD64Ed49E78086fCF2ea98Ec4e102` .
=======
1. **Deploy Honeypots** - Attract attackers with realistic decoy services
2. **Capture Attacks** - Log and cryptographically sign attack attempts
3. **Verify On-Chain** - Smart contracts validate signatures
4. **Mint Tokens** - Receive ERC-20 tokens for verified attacks
5. **Gain Intelligence** - Use tokens to access threat intelligence

## 🌟 Features

- ✅ **Multi-Service Honeypots** - SSH, HTTP, FTP, MySQL, SMB, and more
- ✅ **Blockchain Tokenization** - ERC-20 tokens for verified attacks
- ✅ **Cryptographic Integrity** - ECDSA signatures ensure authenticity
- ✅ **Anti-Farming** - Sophisticated mechanisms prevent self-farming
- ✅ **Real-Time Notifications** - Telegram, Slack, Discord, webhooks
- ✅ **Cross-Platform** - Linux, Windows, macOS support
- ✅ **Threat Intelligence** - Convert tokens into actionable insights

## 📦 Installation Options

### From Source (Development)
```bash
poetry install
poetry run briefcase dev --
```

### From Package (Production)
```bash
# Debian/Ubuntu
sudo dpkg -i deceptgold.deb

# Fedora
sudo rpm -i deceptgold.rpm

# macOS
sudo installer -pkg deceptgold.pkg -target /
```

## 🤝 Support the Project
    
Help fund the project with crowdfunding: `0x99eF54CDe7EaD64Ed49E78086fCF2ea98Ec4e102` !

## 📄 License

This project is licensed under the Deceptgold License. See [LICENSE](deceptgold/src/deceptgold/LICENSE) for details.

## 📧 Contact

- **Email**: contact@decept.gold
- **Website**: https://decept.gold
- **GitHub**: https://github.com/new-resolve/deceptgold

---

**Transform threats into opportunities with Deceptgold.** 🛡️✨
>>>>>>> 49a4295 (doc: added others documentations)
