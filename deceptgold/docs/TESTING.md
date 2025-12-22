# Testing Guide

Comprehensive testing guidelines for Deceptgold development.

## Table of Contents

- [Testing Philosophy](#testing-philosophy)
- [Test Structure](#test-structure)
- [Running Tests](#running-tests)
- [Writing Tests](#writing-tests)
- [Attack Simulation](#attack-simulation)
- [Integration Testing](#integration-testing)
- [Performance Testing](#performance-testing)
- [Coverage](#coverage)

## Testing Philosophy

Deceptgold testing focuses on:

1. **Cryptographic Integrity** - Signature generation and validation
2. **Configuration Management** - Config loading and updates
3. **Honeypot Functionality** - Attack detection and logging
4. **Blockchain Integration** - Web3 interactions and smart contracts
5. **Anti-Farming Mechanisms** - Fingerprinting and rate limiting

## Test Structure

```
tests/
├── __init__.py
├── deceptgold.py              # Test utilities and fixtures
├── test_config_manager.py     # Configuration tests
├── test_signature.py          # Cryptographic signature tests
└── (future tests)
    ├── test_blockchain.py     # Blockchain integration tests
    ├── test_honeypot.py       # Honeypot functionality tests
    └── test_fingerprint.py    # Anti-farming tests
```

## Running Tests

### Basic Test Execution

```bash
# Run all tests
poetry run pytest

# Run with verbose output
poetry run pytest -v

# Run specific test file
poetry run pytest tests/test_signature.py

# Run specific test function
poetry run pytest tests/test_signature.py::test_signature_validation

# Run with output (print statements)
poetry run pytest -s
```

### Test Options

```bash
# Stop on first failure
poetry run pytest -x

# Show local variables on failure
poetry run pytest -l

# Run last failed tests only
poetry run pytest --lf

# Run tests in parallel (requires pytest-xdist)
poetry run pytest -n auto
```

### Coverage

```bash
# Run with coverage
poetry run pytest --cov=deceptgold

# Generate HTML coverage report
poetry run pytest --cov=deceptgold --cov-report=html

# View coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### Watch Mode (for development)

```bash
# Install pytest-watch
poetry add --dev pytest-watch

# Run tests on file changes
poetry run ptw
```

## Writing Tests

### Test File Naming

- Test files: `test_*.py` or `*_test.py`
- Test functions: `test_*`
- Test classes: `Test*`

### Basic Test Structure

```python
import pytest
from deceptgold.helper.signature import generate_signature, validate_signature

def test_signature_generation():
    """Test that signatures are generated correctly."""
    message = "test_attack_log"
    signature = generate_signature(message)
    
    assert signature is not None
    assert len(signature) > 0
    assert isinstance(signature, str)

def test_signature_validation():
    """Test that valid signatures pass validation."""
    message = "test_attack_log"
    signature = generate_signature(message)
    
    result = validate_signature(message, signature)
    assert result is True

def test_invalid_signature_rejection():
    """Test that invalid signatures are rejected."""
    message = "test_attack_log"
    invalid_signature = "0x1234567890abcdef"
    
    result = validate_signature(message, invalid_signature)
    assert result is False
```

### Using Fixtures

```python
import pytest
from deceptgold.configuration.config_manager import ConfigManager

@pytest.fixture
def config_manager():
    """Provide a clean ConfigManager instance for testing."""
    manager = ConfigManager()
    yield manager
    # Cleanup after test
    manager.reset()

def test_config_update(config_manager):
    """Test configuration updates."""
    config_manager.update("user", "address", "0x123...")
    
    value = config_manager.get("user", "address")
    assert value == "0x123..."
```

### Parametrized Tests

```python
import pytest

@pytest.mark.parametrize("service,port", [
    ("ssh", 22),
    ("http", 80),
    ("ftp", 21),
    ("mysql", 3306),
])
def test_service_ports(service, port):
    """Test that services use correct default ports."""
    config = get_service_config(service)
    assert config['port'] == port
```

### Testing Exceptions

```python
import pytest

def test_invalid_wallet_address():
    """Test that invalid wallet addresses raise ValueError."""
    with pytest.raises(ValueError, match="Invalid wallet address"):
        validate_wallet_address("invalid_address")
```

### Mocking External Dependencies

```python
from unittest.mock import Mock, patch
import pytest

@patch('deceptgold.helper.blockchain.Web3')
def test_blockchain_connection(mock_web3):
    """Test blockchain connection without actual network call."""
    # Setup mock
    mock_web3.return_value.is_connected.return_value = True
    
    # Test
    from deceptgold.helper.blockchain import connect_to_network
    result = connect_to_network("https://rpc.example.com")
    
    assert result is True
    mock_web3.assert_called_once()
```

## Attack Simulation

### Using the Attack Simulator

Deceptgold includes a utility for simulating attacks during development:

```bash
# Run attack simulator
poetry run python utils/attack_simulate.py
```

### Manual Attack Simulation

#### SSH Brute Force Simulation

```bash
# Install hydra (attack tool)
sudo apt install hydra  # Ubuntu/Debian
sudo dnf install hydra  # Fedora

# Simulate SSH brute force
hydra -l admin -P /usr/share/wordlists/rockyou.txt localhost ssh -s 22 -t 4
```

#### HTTP Request Flood

```bash
# Using Apache Bench
ab -n 10000 -c 100 http://localhost:80/

# Using curl in loop
for i in {1..1000}; do
    curl http://localhost:80/ &
done
```

#### FTP Connection Attempts

```bash
# Using ftp command
for i in {1..100}; do
    echo "quit" | ftp localhost 21
done
```

### Programmatic Attack Simulation

```python
# tests/test_honeypot.py
import socket
import time

def test_ssh_attack_detection():
    """Test that SSH attacks are detected and logged."""
    # Connect to SSH honeypot
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('localhost', 22))
    
    # Send invalid SSH handshake (simulates attack)
    sock.send(b"SSH-2.0-AttackClient\r\n")
    
    # Wait for logging
    time.sleep(1)
    
    # Verify attack was logged
    logs = read_attack_logs()
    assert any('ssh' in log['service'] for log in logs)
    
    sock.close()
```

## Integration Testing

### Testing Full Attack Flow

```python
import pytest
import time
from deceptgold.helper.opencanary import start_honeypot
from deceptgold.helper.signature import validate_signature
from deceptgold.helper.blockchain import check_token_minted

@pytest.mark.integration
def test_end_to_end_attack_tokenization():
    """Test complete flow from attack to token minting."""
    # 1. Start honeypot
    honeypot = start_honeypot(services=['ssh'])
    
    # 2. Simulate attack
    simulate_ssh_attack('localhost', 22, attempts=100)
    
    # 3. Wait for processing
    time.sleep(5)
    
    # 4. Verify attack was logged
    logs = read_attack_logs()
    assert len(logs) > 0
    
    # 5. Verify signature
    latest_log = logs[-1]
    assert validate_signature(
        latest_log['message'],
        latest_log['signature']
    )
    
    # 6. Verify token was minted (requires testnet)
    # This would be tested on testnet in CI/CD
    # assert check_token_minted(latest_log['hash'])
    
    # Cleanup
    honeypot.stop()
```

### Testing Configuration Persistence

```python
def test_config_persistence():
    """Test that configuration persists across restarts."""
    # Set configuration
    update_config("user", "address", "0xTest123")
    
    # Simulate restart by creating new config instance
    new_config = ConfigManager()
    
    # Verify persistence
    assert new_config.get("user", "address") == "0xTest123"
```

### Testing Blockchain Integration

```python
@pytest.mark.blockchain
@pytest.mark.slow
def test_testnet_token_minting():
    """Test actual token minting on testnet."""
    # This test requires testnet connection
    # Should be run in CI/CD with testnet RPC
    
    attack_data = {
        "timestamp": "2025-12-22T20:00:00Z",
        "source_ip": "192.168.1.100",
        "service": "ssh",
        "requests": 1000
    }
    
    # Generate signature
    signature = sign_attack(attack_data)
    
    # Submit to testnet
    tx_hash = submit_to_blockchain(attack_data, signature)
    
    # Wait for confirmation
    receipt = wait_for_transaction(tx_hash, timeout=60)
    
    assert receipt['status'] == 1  # Success
    assert 'TokensMinted' in receipt['logs']
```

## Performance Testing

### Load Testing

```python
import time
import concurrent.futures

def test_concurrent_attack_handling():
    """Test system handles multiple concurrent attacks."""
    def simulate_attack(attack_id):
        # Simulate attack
        return perform_attack(f"attacker_{attack_id}")
    
    # Simulate 100 concurrent attacks
    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
        futures = [executor.submit(simulate_attack, i) for i in range(100)]
        results = [f.result() for f in futures]
    
    # Verify all attacks were processed
    assert len(results) == 100
    assert all(r['status'] == 'logged' for r in results)
```

### Memory Profiling

```python
from memory_profiler import profile

@profile
def test_memory_usage_during_attack_processing():
    """Profile memory usage during attack processing."""
    # Process 10000 attacks
    for i in range(10000):
        process_attack({
            "timestamp": "2025-12-22T20:00:00Z",
            "source_ip": f"192.168.1.{i % 255}",
            "service": "ssh",
            "requests": 100
        })
```

### Timing Tests

```python
import time

def test_signature_generation_performance():
    """Test that signature generation is fast enough."""
    message = "test_attack_log_" * 100  # Large message
    
    start = time.time()
    for _ in range(1000):
        generate_signature(message)
    duration = time.time() - start
    
    # Should generate 1000 signatures in under 1 second
    assert duration < 1.0
```

## Coverage

### Measuring Coverage

```bash
# Run tests with coverage
poetry run pytest --cov=deceptgold --cov-report=term-missing

# Generate detailed HTML report
poetry run pytest --cov=deceptgold --cov-report=html

# Show coverage for specific module
poetry run pytest --cov=deceptgold.helper.signature --cov-report=term
```

### Coverage Goals

- **Overall**: Aim for 80%+ coverage
- **Critical modules**: 90%+ coverage
  - `helper/signature.py`
  - `helper/blockchain/`
  - `configuration/`
- **Less critical**: 70%+ coverage
  - CLI commands
  - Utilities

### Coverage Report Example

```
Name                                    Stmts   Miss  Cover   Missing
---------------------------------------------------------------------
deceptgold/__init__.py                      2      0   100%
deceptgold/helper/signature.py             45      3    93%   78-80
deceptgold/helper/blockchain/web3.py       67     12    82%   45-48, 89-95
deceptgold/configuration/config.py         34      2    94%   67, 89
---------------------------------------------------------------------
TOTAL                                     148     17    89%
```

## Continuous Integration

### GitHub Actions Example

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      
      - name: Install Poetry
        run: curl -sSL https://install.python-poetry.org | python3 -
      
      - name: Install dependencies
        run: poetry install
      
      - name: Run tests
        run: poetry run pytest --cov=deceptgold --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Best Practices

### DO:
- ✅ Write tests for all new features
- ✅ Test edge cases and error conditions
- ✅ Use descriptive test names
- ✅ Keep tests independent and isolated
- ✅ Mock external dependencies
- ✅ Test both success and failure paths

### DON'T:
- ❌ Test implementation details
- ❌ Write tests that depend on external services (use mocks)
- ❌ Share state between tests
- ❌ Write tests that are flaky or non-deterministic
- ❌ Ignore failing tests

## Debugging Failed Tests

```bash
# Run with debugger on failure
poetry run pytest --pdb

# Show full diff on assertion failures
poetry run pytest -vv

# Run specific test with maximum verbosity
poetry run pytest tests/test_signature.py::test_validation -vvs
```

## See Also

- [GETTING_STARTED.md](GETTING_STARTED.md) - Quick start guide
- [DEVELOPMENT.md](../DEVELOPMENT.md) - Development workflow
- [API_REFERENCE.md](API_REFERENCE.md) - Command reference
- [CONTRIBUTING.md](../CONTRIBUTING.md) - Contribution guidelines

---

**Questions?** Contact: contact@decept.gold
