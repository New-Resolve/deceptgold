# Getting Started with Deceptgold Development

Welcome to Deceptgold! This guide will help you get up and running with development in under 10 minutes.

## Prerequisites

- **Python 3.11+** installed
- **Poetry** for dependency management
- **Git** for version control
- Basic knowledge of Python and command-line tools

## Quick Setup (5 minutes)

### 1. Clone and Navigate

```bash
git clone https://github.com/new-resolve/deceptgold.git
cd deceptgold/deceptgold
```

### 2. Install Dependencies

```bash
# Install Poetry if you haven't already
curl -sSL https://install.python-poetry.org | python3 -

# Add Poetry to PATH
export PATH="$HOME/.local/bin:$PATH"

# If you need Python 3.12 (using pyenv)
pyenv install 3.12
pyenv local 3.12

# Configure Poetry
poetry config virtualenvs.create true
poetry env use python

# Install project dependencies
poetry install
```

**For Poetry 2.0+**, activate the environment:

```bash
# Option 1: Manual activation (recommended)
source .venv/bin/activate

# Option 2: Use poetry run (no activation needed)
poetry run python -m deceptgold --version

# Option 3: Install shell plugin
poetry self add poetry-plugin-shell
poetry shell
```

### 3. Run Your First Command

```bash
# Check version
poetry run briefcase dev -- --version

# View help
poetry run briefcase dev -- --help

# View available commands
poetry run briefcase dev -- user --help
```

## Understanding the Basics

### What is Deceptgold?

Deceptgold transforms cyber attacks into digital assets (tokens) through:

1. **Honeypots** - Fake services that attract attackers
2. **Cryptographic Signing** - Each attack is signed to prove authenticity
3. **Blockchain Tokenization** - Verified attacks generate ERC-20 tokens
4. **Intelligence** - Tokens unlock threat intelligence data

### Core Concepts

**Honeypot**: A decoy system designed to attract and log cyber attacks.

**Attack Log**: A cryptographically signed record of an attack attempt.

**Token**: An ERC-20 token minted for each verified attack.

**Fingerprint**: A unique system identifier to prevent self-farming.

**Smart Contract**: On-chain code that validates attacks and mints tokens.

## Your First Development Task

### Example: View System Configuration

```bash
# Run the application
poetry run briefcase dev -- user config --show
```

### Example: Simulate an Attack (for testing)

```bash
# Use the attack simulator
poetry run python utils/attack_simulate.py
```

### Example: Run Tests

```bash
# Run all tests
poetry run pytest

# Run specific test
poetry run pytest tests/test_signature.py -v
```

## Project Structure Quick Reference

```
deceptgold/
├── src/deceptgold/           # Main source code
│   ├── __main__.py           # Entry point
│   ├── commands/             # CLI commands
│   ├── helper/               # Core functionality
│   │   ├── blockchain/       # Web3 integration
│   │   ├── opencanary/       # Honeypot system
│   │   └── signature.py      # Crypto signing
│   └── resources/            # Config & assets
├── tests/                    # Test suite
├── utils/                    # Dev utilities
└── pyproject.toml            # Project config
```

## Common Development Commands

### Running the Application

```bash
# Development mode (recommended)
poetry run briefcase dev --

# With specific command
poetry run briefcase dev -- service start

# Direct Python module
python -m deceptgold --help
```

### Testing

```bash
# All tests
poetry run pytest

# With coverage
poetry run pytest --cov=deceptgold

# Specific test file
poetry run pytest tests/test_config_manager.py
```

### Building

```bash
# Full build (includes obfuscation)
sh utils/compile.sh

# Quick build (no obfuscation)
poetry run briefcase build --target debian
```

## Making Your First Change

### 1. Create a Feature Branch

```bash
git checkout -b feature/my-first-feature
```

### 2. Make Changes

Edit files in `src/deceptgold/`. For example, add a new helper function:

```python
# src/deceptgold/helper/helper.py

def my_new_function():
    """My first contribution to Deceptgold!"""
    return "Hello, Deceptgold!"
```

### 3. Test Your Changes

```bash
# Run tests
poetry run pytest

# Test manually
poetry run briefcase dev --
```

### 4. Commit with Semantic Message

```bash
git add .
git commit -m "feat(helper): add my_new_function"
```

## Understanding the Development Workflow

### Development Mode vs Production

**Development Mode** (`sources = ["src/deceptgold"]`):
- Unobfuscated code
- Fast iteration
- Full debugging
- Local testing

**Production Mode** (`sources = ["src_obf/deceptgold"]`):
- Obfuscated code (PyArmor)
- Secure distribution
- Platform-specific builds
- Used in CI/CD pipeline

⚠️ **Important**: Always use `src/deceptgold` for local development!

### Key Files to Know

| File | Purpose |
|------|---------|
| `pyproject.toml` | Project configuration, dependencies |
| `__main__.py` | Application entry point |
| `commands/service.py` | Service control commands |
| `helper/signature.py` | Cryptographic signing |
| `helper/blockchain/` | Web3 integration |
| `utils/compile.sh` | Build script |

## Debugging Tips

### Enable Verbose Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check if in Developer Mode

```python
from deceptgold.helper.helper import my_self_developer

if my_self_developer():
    print("Running in developer mode")
```

### Inspect Configuration

```bash
# View current config
poetry run briefcase dev -- user config --show

# Check logs
tail -f /var/log/deceptgold/attacks.log
```

## Next Steps

Now that you're set up, explore:

1. **[DEVELOPMENT.md](../DEVELOPMENT.md)** - Detailed development guide
2. **[ARCHITECTURE.md](../ARCHITECTURE.md)** - System architecture
3. **[CONTRIBUTING.md](../CONTRIBUTING.md)** - Contribution guidelines
4. **[API_REFERENCE.md](API_REFERENCE.md)** - Command reference
5. **[TESTING.md](TESTING.md)** - Testing guidelines

## Common Issues

### Poetry Not Found

```bash
# Add to PATH
export PATH="$HOME/.local/bin:$PATH"
```

### Virtual Environment Issues

```bash
# Remove and recreate
poetry env remove python
poetry install
```

### Python Version Error

```bash
# If you get "Current Python version (3.10.x) is not allowed"
# Install Python 3.12 with pyenv
pyenv install 3.12
pyenv local 3.12

# Tell Poetry to use it
poetry env use python
poetry install
```

### Poetry Shell Not Available (Poetry 2.0+)

```bash
# Option 1: Activate manually
source .venv/bin/activate

# Option 2: Install shell plugin
poetry self add poetry-plugin-shell

# Option 3: Use poetry run
poetry run python -m deceptgold --help
```

### Permission Errors

```bash
# Fix log directory permissions
sudo chown -R $USER:$USER /var/log/deceptgold/
```

## Getting Help

- **Documentation**: Check `docs/` directory
- **Issues**: [GitHub Issues](https://github.com/new-resolve/deceptgold/issues)
- **Email**: contact@decept.gold

## Quick Reference Card

```bash
# Setup
poetry install && poetry shell

# Run
poetry run briefcase dev --

# Test
poetry run pytest

# Build
sh utils/compile.sh

# Commit
git commit -m "feat: description"
```

---

**Ready to contribute?** Check out [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines! 🚀
