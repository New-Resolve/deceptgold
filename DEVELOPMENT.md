# Development Guide

This guide will help you set up your development environment and understand the development workflow for Deceptgold.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Development Workflow](#development-workflow)
- [Build and Compilation](#build-and-compilation)
- [Testing](#testing)
- [Debugging](#debugging)
- [Common Tasks](#common-tasks)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Software

- **Python 3.11+** (Python 3.12 recommended)
- **Poetry** - Python dependency management
- **Git** - Version control

### System Dependencies

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install python3.12 python3.12-dev python3-pip git
```

#### Fedora
```bash
sudo dnf install python3.12 python3.12-devel git
```

#### macOS
```bash
brew install python@3.12 poetry git
```

### Install Poetry

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

Add Poetry to your PATH (add to `~/.bashrc` or `~/.zshrc`):
```bash
export PATH="$HOME/.local/bin:$PATH"
```

### Python Version Management

Deceptgold requires **Python 3.11+** (3.12 recommended). If your system has an older version, use **pyenv** to manage multiple Python versions.

#### Install pyenv (if not installed)

**Linux/macOS:**
```bash
curl https://pyenv.run | bash
```

Add to your `~/.bashrc` or `~/.zshrc`:
```bash
export PATH="$HOME/.pyenv/bin:$PATH"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"
```

Reload shell:
```bash
source ~/.bashrc  # or ~/.zshrc
```

#### Install Python 3.12 with pyenv

```bash
# Install Python 3.12
pyenv install 3.12

# Set as local version for this project
cd deceptgold/deceptgold
pyenv local 3.12

# Verify
python --version  # Should show Python 3.12.x
```

#### Configure Poetry to use correct Python

```bash
# Tell Poetry to use the current Python (from pyenv)
poetry env use python

# Or specify the full path
poetry env use $(which python)

# Verify Poetry is using correct Python
poetry env info
```

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/new-resolve/deceptgold.git
cd deceptgold/deceptgold
```

### 2. Install Dependencies

```bash
# Ensure virtualenv creation is enabled (Poetry 2.0+)
poetry config virtualenvs.create true

# Configure Poetry to use correct Python version
poetry env use python

# Create virtual environment and install dependencies
poetry install
```

**For Poetry 2.0+**, you have three options to activate the environment:

**Option 1: Manual activation (Recommended)**
```bash
# Activate the virtual environment directly
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate  # Windows
```

**Option 2: Use `poetry run` (No activation needed)**
```bash
# Run commands through Poetry
poetry run python -m deceptgold
poetry run briefcase dev --
```

**Option 3: Install shell plugin (Optional)**
```bash
# Install the shell plugin to get `poetry shell` back
poetry self add poetry-plugin-shell

# Then you can use
poetry shell
```

### 3. Run in Development Mode

```bash
# Option 1: Using briefcase (recommended)
poetry run briefcase dev --

# Option 2: Using Python module (if environment is activated)
python -m deceptgold

# Option 3: Direct briefcase (if environment is activated)
briefcase dev --
```

### 4. Verify Installation

```bash
# Check version (use poetry run if not activated)
poetry run python -m deceptgold --version

# View help
poetry run python -m deceptgold --help
```

## Project Structure

```
deceptgold/
├── src/deceptgold/              # Main source code
│   ├── __main__.py              # Application entry point
│   ├── commands/                # CLI commands
│   │   ├── user.py              # User management commands
│   │   ├── service.py           # Service control commands
│   │   └── notify.py            # Notification commands
│   ├── configuration/           # Configuration management
│   │   └── log.py               # Logging configuration
│   ├── helper/                  # Helper modules
│   │   ├── blockchain/          # Blockchain integration
│   │   ├── opencanary/          # Honeypot system
│   │   ├── notify/              # Notification system
│   │   ├── signature.py         # Cryptographic signatures
│   │   ├── fingerprint.py       # System fingerprinting
│   │   └── helper.py            # Utility functions
│   ├── resources/               # Static resources
│   │   ├── config/              # Configuration templates
│   │   ├── images/              # Images and assets
│   │   └── templates/           # File templates
│   ├── CHANGELOG                # Auto-generated changelog
│   ├── LICENSE                  # License file
│   └── NOTICE                   # Legal notices
├── tests/                       # Test suite
│   ├── test_config_manager.py   # Configuration tests
│   └── test_signature.py        # Signature validation tests
├── utils/                       # Development utilities
│   ├── compile.sh               # Build script
│   ├── attack_simulate.py       # Attack simulation
│   ├── create_changelog.py      # Changelog generator
│   └── create_documentation.py  # Documentation generator
├── docs/                        # Documentation
├── pyproject.toml               # Project configuration
└── README.md                    # Project README
```

### Key Components

#### CLI Application (`__main__.py`)
- Entry point using **Cyclopts** framework
- Registers command groups (user, service, notify)
- Handles initialization and error handling

#### Commands (`commands/`)
- **user.py**: User account management, wallet operations
- **service.py**: Honeypot service control (start, stop, status)
- **notify.py**: Notification and telemetry management

#### Helpers (`helper/`)
- **blockchain/**: Web3 integration, smart contract interaction
- **opencanary/**: Honeypot implementation and logging
- **signature.py**: ECDSA signature generation and validation
- **fingerprint.py**: System identification and anti-farming

#### Configuration (`configuration/`)
- Manages application settings
- Logging configuration
- Environment-specific configs

## Development Workflow

### Setting Up Your Environment

1. **Configure pyproject.toml for local development:**

   ⚠️ **Important**: For local development, ensure this line in `pyproject.toml`:
   ```toml
   sources = ["src/deceptgold"]
   ```
   
   For production builds, the pipeline uses:
   ```toml
   sources = ["src_obf/deceptgold"]  # Obfuscated code
   ```

2. **Install development dependencies:**
   ```bash
   poetry install --with dev,docs
   ```

3. **Activate pre-commit hooks (optional):**
   ```bash
   poetry run pre-commit install
   ```

### Making Changes

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** in `src/deceptgold/`

3. **Test locally:**
   ```bash
   # Run in dev mode
   poetry run briefcase dev --
   
   # Run specific command
   poetry run briefcase dev -- service --help
   ```

4. **Run tests:**
   ```bash
   poetry run pytest
   ```

5. **Commit with semantic messages:**
   ```bash
   git commit -m "feat(blockchain): add Polygon network support"
   ```

### Code Style

Follow **PEP 8** conventions:

```bash
# Check code style
poetry run pydocstyle src/

# Format code (if using black)
poetry run black src/
```

## Build and Compilation

### Understanding the Build Process

Deceptgold uses a multi-step build process:

1. **Code Obfuscation** (PyArmor) - Protects proprietary logic
2. **Packaging** (Briefcase) - Creates platform-specific packages
3. **Distribution** - Generates `.deb`, `.rpm`, `.pkg`, etc.

### Local Build

```bash
# Run the build script
cd deceptgold
sh utils/compile.sh
```

**What the script does:**

1. Activates Poetry environment
2. Cleans previous builds
3. Obfuscates code with PyArmor
4. Copies resources (LICENSE, CHANGELOG, etc.)
5. Builds with Briefcase for target platform
6. Packages the application
7. Outputs to `dist/` directory

### Build for Specific Platforms

#### Debian/Ubuntu (.deb)
```bash
poetry run briefcase build --target debian --update
poetry run briefcase package --target debian
```

#### Fedora (.rpm)
```bash
poetry run briefcase build --target fedora:40 --update
poetry run briefcase package --target fedora:40
```

#### macOS (.pkg)
```bash
poetry run briefcase build macOS --update
poetry run briefcase package macOS
```

### Manual Obfuscation (for testing)

```bash
# Obfuscate code
poetry run pyarmor gen -O src_obf -r -i src/deceptgold --platform linux.x86_64

# Copy resources
cp -r src/deceptgold/resources src_obf/deceptgold/
cp src/deceptgold/{CHANGELOG,LICENSE,NOTICE} src_obf/deceptgold/

# Update pyproject.toml temporarily
# Change: sources = ["src_obf/deceptgold"]

# Build
poetry run briefcase build --target debian
```

## Testing

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=deceptgold

# Run specific test file
poetry run pytest tests/test_signature.py

# Run with verbose output
poetry run pytest -v
```

### Test Structure

```
tests/
├── __init__.py
├── test_config_manager.py    # Configuration tests
├── test_signature.py          # Cryptographic tests
└── deceptgold.py             # Test utilities
```

### Writing Tests

Example test:
```python
import pytest
from deceptgold.helper.signature import validate_signature

def test_signature_validation():
    """Test cryptographic signature validation."""
    message = "test_attack_log"
    # Test implementation
    assert validate_signature(message, signature, public_key)
```

### Simulating Attacks (for testing)

```bash
# Use the attack simulator
poetry run python utils/attack_simulate.py
```

See [docs/TESTING.md](docs/TESTING.md) for detailed testing guidelines.

## Debugging

### Debug Mode

Run with Python debugger:
```bash
python -m pdb -m deceptgold service start
```

### Logging

Enable verbose logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Logs are typically stored in:
- Linux: `/var/log/deceptgold/`
- macOS: `~/Library/Logs/deceptgold/`
- Development: `./logs/`

### Common Debug Tasks

**Check if you're in developer mode:**
```python
from deceptgold.helper.helper import my_self_developer
if my_self_developer():
    print("Developer mode active")
```

**Inspect configuration:**
```bash
poetry run briefcase dev -- user config --show
```

## Common Tasks

### Generate Changelog

```bash
poetry run generate-changelog
```

### Generate Documentation

```bash
poetry run generate-doc
```

### Update Dependencies

```bash
# Update all dependencies
poetry update

# Update specific package
poetry update web3

# Show outdated packages
poetry show --outdated
```

### Clean Build Artifacts

```bash
# Remove obfuscated code
rm -rf src_obf/

# Remove build directories
rm -rf build/ dist/

# Remove Python cache
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
```

## Troubleshooting

### Poetry Issues

**Problem**: `poetry: command not found`
```bash
# Ensure Poetry is in PATH
export PATH="$HOME/.local/bin:$PATH"
```

**Problem**: Virtual environment issues
```bash
# Remove and recreate
poetry env remove python
poetry install
```

**Problem**: `poetry shell` not available (Poetry 2.0+)
```bash
# Option 1: Activate manually (recommended)
source .venv/bin/activate  # Linux/macOS

# Option 2: Install shell plugin
poetry self add poetry-plugin-shell

# Option 3: Use poetry run for commands
poetry run python -m deceptgold
```

**Problem**: `virtualenvs.create = false` error
```bash
# Enable virtualenv creation
poetry config virtualenvs.create true

# Reinstall dependencies
poetry install
```

### Build Issues

**Problem**: `pyproject.toml` sources error
```bash
# For local dev, ensure:
sources = ["src/deceptgold"]

# NOT:
sources = ["src_obf/deceptgold"]
```

**Problem**: Briefcase build fails
```bash
# Clean and rebuild
rm -rf build/
poetry run briefcase build --update
```

### Runtime Issues

**Problem**: Permission denied on service start
```bash
# Check log directory permissions
sudo chown -R $USER:$USER /var/log/deceptgold/
```

**Problem**: Module import errors
```bash
# Ensure you're in Poetry shell
poetry shell

# Reinstall dependencies
poetry install
```

### Platform-Specific Issues

#### Linux
- Ensure `libpython3.12` is installed
- Check systemd service permissions

#### macOS
- May need to allow unsigned applications in Security settings
- Ensure Xcode Command Line Tools are installed

#### Windows
- Run as Administrator for service installation
- Check Windows Defender exclusions

## IDE Configuration

### VS Code

Recommended `.vscode/settings.json`:
```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black",
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["tests"]
}
```

### PyCharm

1. Set Python interpreter to Poetry virtual environment
2. Enable pytest as test runner
3. Configure code style to PEP 8

## Next Steps

- Read [ARCHITECTURE.md](ARCHITECTURE.md) for system design
- Check [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines
- Explore [docs/](docs/) for detailed technical documentation
- Review [documentation/whitepaper.md](documentation/whitepaper.md) for project vision

## Getting Help

- **Documentation**: Check `docs/` directory
- **Issues**: Open a GitHub issue
- **Contact**: contact@decept.gold

---

Happy coding! 🚀
