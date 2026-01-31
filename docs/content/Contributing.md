# Contributing to Deceptgold

First off, thank you for considering contributing to Deceptgold! It's people like you that make Deceptgold such a great tool for transforming cyber threats into valuable digital assets.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
  - [Reporting Bugs](#reporting-bugs)
  - [Suggesting Enhancements](#suggesting-enhancements)
  - [Pull Requests](#pull-requests)
- [Development Process](#development-process)
- [Style Guidelines](#style-guidelines)
  - [Git Commit Messages](#git-commit-messages)
  - [Python Style Guide](#python-style-guide)
- [Additional Resources](#additional-resources)

## Code of Conduct

This project and everyone participating in it is governed by our commitment to fostering an open and welcoming environment. We pledge to make participation in our project a harassment-free experience for everyone, regardless of age, body size, disability, ethnicity, gender identity and expression, level of experience, nationality, personal appearance, race, religion, or sexual identity and orientation.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the existing issues to avoid duplicates. When you create a bug report, include as many details as possible:

**Great Bug Reports** include:

- **Clear and descriptive title**
- **Exact steps to reproduce the problem**
- **Expected behavior vs. actual behavior**
- **Screenshots or terminal output** (if applicable)
- **Environment details:**
  - OS and version (e.g., Ubuntu 22.04, Fedora 40, macOS 14)
  - Python version (`python --version`)
  - Deceptgold version (`deceptgold --version`)
  - Installation method (Poetry, .deb, .rpm, etc.)

**Example Bug Report:**

```markdown
## Bug: Service fails to start on Fedora 40

**Steps to reproduce:**
1. Install deceptgold via RPM package
2. Run `deceptgold service start`
3. Service fails with error "Permission denied"

**Expected:** Service starts successfully
**Actual:** Permission error in /var/log/deceptgold/

**Environment:**
- OS: Fedora 40
- Python: 3.12.1
- Deceptgold: 0.2.0
- Installed via: RPM package
```

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, include:

- **Clear and descriptive title**
- **Detailed description** of the proposed functionality
- **Use cases** - why is this enhancement useful?
- **Possible implementation** (if you have ideas)
- **Alternatives considered**

### Pull Requests

We actively welcome your pull requests! Here's the process:

1. **Fork the repository** and create your branch from `master`
2. **Set up your development environment** (see [Development.md](Development.md))
3. **Make your changes:**
   - Add tests if you're adding functionality
   - Update documentation if needed
   - Follow our style guidelines
4. **Test your changes** thoroughly
5. **Commit your changes** using semantic commit messages
6. **Push to your fork** and submit a pull request

**Pull Request Guidelines:**

- Keep PRs focused on a single feature or bug fix
- Include tests for new functionality
- Update documentation (README, docs/, etc.)
- Ensure all tests pass
- Follow the existing code style
- Reference related issues (e.g., "Fixes #123")

## Development Process

### Getting Started

1. **Clone your fork:**
   ```bash
   git clone https://github.com/YOUR-USERNAME/deceptgold.git
   cd deceptgold/deceptgold
   ```

2. **Set up development environment:**
   ```bash
   poetry install
   poetry shell
   ```

3. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```

4. **Make your changes and test:**
   ```bash
   # Run in development mode
   poetry run briefcase dev --
   
   # Run tests
   poetry run pytest
   ```

5. **Commit and push:**
   ```bash
   git add .
   git commit -m "feat: add amazing feature"
   git push origin feature/your-feature-name
   ```

For detailed development instructions, see [Development.md](Development.md).

### Testing

Before submitting a PR, ensure:

- All existing tests pass: `poetry run pytest`
- New functionality has test coverage
- Manual testing has been performed
- No linting errors: `poetry run pydocstyle src/`

See [deceptgold/docs/Testing.md](deceptgold/docs/Testing.md) for detailed testing guidelines.

## Style Guidelines

### Git Commit Messages

We use **Semantic Commit Messages** for automatic changelog generation:

**Format:** `<type>(<scope>): <subject>`

**Types:**
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting, no logic change)
- `refactor:` Code refactoring
- `perf:` Performance improvements
- `test:` Adding or updating tests
- `chore:` Maintenance tasks, dependencies

**Examples:**
```bash
feat(blockchain): add support for Polygon network
fix(service): resolve permission issue on Fedora
docs(readme): update installation instructions
refactor(signature): improve cryptographic validation
test(honeypot): add integration tests for SSH module
```

**Scope** is optional but recommended. Use component names like:
- `blockchain`, `honeypot`, `signature`, `cli`, `service`, `config`

### Python Style Guide

We follow **PEP 8** with some project-specific conventions:

**Code Style:**
- Use 4 spaces for indentation (no tabs)
- Maximum line length: 120 characters
- Use descriptive variable names
- Add docstrings to all public functions and classes
- Type hints are encouraged

**Example:**
```python
def validate_signature(message: str, signature: str, public_key: str) -> bool:
    """
    Validate a cryptographic signature against a message.
    
    Args:
        message: The original message that was signed
        signature: The signature to validate
        public_key: The public key for verification
        
    Returns:
        True if signature is valid, False otherwise
        
    Raises:
        ValueError: If public_key format is invalid
    """
    # Implementation here
    pass
```

**Imports:**
- Group imports: standard library, third-party, local
- Use absolute imports
- Sort alphabetically within groups

**Example:**
```python
import logging
import time
from typing import Optional

from web3 import Web3
from ecdsa import SigningKey

from deceptgold.helper.signature import validate_signature
from deceptgold.configuration import config
```

### Documentation Style

- Use **Markdown** for all documentation
- Keep lines under 120 characters when possible
- Use code blocks with language specification
- Include examples for complex features
- Keep language clear and concise

## Additional Resources

- [Development.md](Development.md) - Detailed development setup and workflow
- [Architecture.md](Architecture.md) - System architecture overview
- [deceptgold/docs/](deceptgold/docs/) - Technical documentation
- [Whitepaper](documentation/Whitepaper.md) - Project vision and technical details

## Getting Help

If you have questions, feel free to:
- Open an issue
- Contact us at: jsmorais@pm.me
- Check existing documentation in the `docs/` directory

---

**Thank you for contributing to Deceptgold!** 🎉

Every contribution, no matter how small, helps us build a better cybersecurity ecosystem where threats become opportunities.
