# Cyber Deception and Resource Inversion 


[![Build](https://github.com/new-resolve/deceptgold/actions/workflows/build.yml/badge.svg)](https://github.com/new-resolve/deceptgold/actions/workflows/build.yml)
![Last Commit](https://img.shields.io/github/last-commit/new-resolve/deceptgold)
[![Docs](https://img.shields.io/badge/docs-available-success)](https://github.com/New-Resolve/deceptgold/tree/master/docs/content)
![Python](https://img.shields.io/badge/python-3.12-blue?logo=python)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache--2.0-blue)](LICENSE)

---

Deceptgold is a next-generation platform designed to manage deception strategies and reclaim value from cyber attacks. While most organizations focus only on detection, logging, and mitigation, Deceptgold takes a radically different approach: it transforms the computational effort of intrusion attempts into valuable digital assets.

In today's threat landscape, companies suffer not only from data breaches but also from a massive waste of computational power during attacks. Countless CPU cycles, network bandwidth, and system resources are consumed by malicious actors — and traditionally, all this energy is simply lost.

## Deceptgold solves this problem.

By deploying deceptive environments that interact with attackers in a controlled and intelligent way, the system is able to capture and redirect the power of attacks, converting what would otherwise be waste into tangible assets for the defending organization. This turns an inherently negative event — being targeted — into a source of intelligence, strategic advantage, and even economic value.

Deceptgold is ideal for cybersecurity teams, researchers, and critical infrastructure defenders who want more than just alerts. It is built for those who believe that every intrusion attempt is an opportunity — not just a threat.

## 🌟 Features

- ✅ **Hybrid Web2 + Web3 Honeypots** - Traditional (Web2) and decentralized (Web3) service simulation
- ✅ **Real-Time Notifications** - Telegram, Slack, Discord, webhooks
- ✅ **Cross-Platform** - Linux (all distros) and Windows versions
- ✅ **Blockchain Tokenization** - ERC-20 tokens for verified attacks
- ✅ **Cryptographic Integrity** - ECDSA signatures ensure authenticity
- ✅ **Anti-Farming** - Sophisticated mechanisms prevent self-farming
- ✅ **Threat Intelligence** - Convert tokens into actionable insights

## 📚 Documentation

- **[Whitepaper](docs/content/Whitepaper.md)** - Project vision and technical details
- **[Architecture](ARCHITECTURE.md)** - System design and components
- **[Getting Started](docs/content/Development.md)** - Quick start for developers
- **[API Reference](docs/content/Commands.md)** - Complete command reference

## 🚀 Quick Start

### Basic Usage

```bash
# Start honeypot service screen output
deceptgold service start daemon=false  

# Start a honeypot service without an attached portfolio.
deceptgold service start force-no-wallet=true

# Configure wallet address
deceptgold user --my-address 0xYourWalletAddress

# Check all services
deceptgold service list

# Check status
deceptgold service status

# View token balance
deceptgold user --show-balance

# See more
deceptgold -h
```

## 🛠️ For Developers

### Contributing

We welcome contributions! Please read our guidelines:

- **[Contributing Guide](CONTRIBUTING.md)** - How to contribute
- **[Development Guide](DEVELOPMENT.md)** - Setup and workflow
- **[Testing Guide](docs/content/Testing.md)** - Testing procedures

### Key Resources

- **[Architecture Overview](ARCHITECTURE.md)** - System design
- **[Blockchain Integration](docs/content/Blockchain.md)** - Smart contracts and Web3
- **[Testing Guide](docs/content/Testing.md)** - Test structure and examples

## 💡 How It Works

![attacks_revenue.png](docs/content/assets/attacks_revenue.png)

1. **Deploy Honeypots** - Attract attackers with realistic decoy services
2. **Capture Attacks** - Log and cryptographically sign attack attempts
3. **Verify On-Chain** - Smart contracts validate signatures
4. **Mint Tokens** - Receive ERC-20 tokens for verified attacks
5. **Gain Intelligence** - Use tokens to access threat intelligence


## 🤝 Support the Project
    
Help fund the project with crowdfunding: `0x99eF54CDe7EaD64Ed49E78086fCF2ea98Ec4e102` !

## 📄 License

This project is licensed under the Apache License 2.0. See [LICENSE](LICENSE) for details.

## 📧 Contact

- **Email**: jsmorais@pm.me
- **Website**: https://decept.gold
- **GitHub**: https://github.com/new-resolve/deceptgold
