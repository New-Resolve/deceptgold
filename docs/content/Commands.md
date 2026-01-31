# API Reference

Complete command-line interface reference for Deceptgold.

## Table of Contents

- [Global Options](#global-options)
- [User Commands](#user-commands)
- [Service Commands](#service-commands)
- [Notify Commands](#notify-commands)
- [Examples](#examples)

## Global Options

```bash
deceptgold [COMMAND] [OPTIONS]
```

### Version and Help

```bash
# Show version
deceptgold --version

# Show help
deceptgold --help

# Show help for specific command
deceptgold user --help
deceptgold service --help
deceptgold notify --help
```

## User Commands

Manage user accounts, wallets, and configuration.

### `user --my-address`

Register your wallet address to receive token rewards.

**Syntax:**
```bash
deceptgold user --my-address <WALLET_ADDRESS>
```

**Parameters:**
- `<WALLET_ADDRESS>` - Your ERC-20 compatible wallet address (e.g., `0x0105d8Ceab792bfece1b2994B71992Af56930081`)

**Example:**
```bash
deceptgold user --my-address 0x0105d8Ceab792bfece1b2994B71992Af56930081
```

**Notes:**
- This is **mandatory** before starting services to receive rewards
- Address is stored in configuration file
- Automatically configures blockchain network settings

---

### `user --show-balance`

Display your Deceptgold token balance.

**Syntax:**
```bash
deceptgold user --show-balance
```

**Output:**
```
Balance: 1250.5 DGLD
Balance (base units): 1250500000000000000000
Explorer: https://testnet.bscscan.com/address/0x...
```

**Prerequisites:**
- Wallet address must be configured with `--my-address`
- Internet connection to query blockchain

**Example:**
```bash
deceptgold user --show-balance
```

---

## Service Commands

Control honeypot services and configuration.

### `service start`

Start the honeypot service.

**Syntax:**
```bash
deceptgold service start [OPTIONS]
```

**Options:**
- `daemon=true|false` - Run in background (default: `true`)
- `force-no-wallet=true|false` - Skip wallet verification (default: `false`)
- `debug=true|false` - Enable debug mode (default: `false`)

**Examples:**
```bash
# Start in background (daemon mode)
deceptgold service start

# Start in foreground (see logs in terminal)
deceptgold service start daemon=false

# Start without wallet configured (testing only)
deceptgold service start force-no-wallet=true

# Start with debug output
deceptgold service start daemon=false debug=true
```

**Notes:**
- Requires wallet address unless `force-no-wallet=true`
- Creates PID file to track running process
- Logs to `/var/log/deceptgold/` or `~/.deceptgold/logs/`

---

### `service stop`

Stop the running honeypot service.

**Syntax:**
```bash
deceptgold service stop
```

**Example:**
```bash
deceptgold service stop
```

**Notes:**
- Gracefully terminates the service
- Removes PID file
- Waits up to 5 seconds for clean shutdown

---

### `service restart`

Restart the honeypot service (stop + start).

**Syntax:**
```bash
deceptgold service restart
```

**Example:**
```bash
deceptgold service restart
```

**Notes:**
- Equivalent to calling `stop` then `start`
- Inherits previous start configuration

---

### `service status`

Show status of enabled services and ports.

**Syntax:**
```bash
deceptgold service status
```

**Output:**
```
[Deceptgold System Daemon]
PID: 12345

Deceptgold Operational Status
Layer  Service  Port  Status
Web2   SSH      22    OPEN
Web2   HTTP     80    OPEN
Web2   FTP      21    CLOSED
```

**Example:**
```bash
deceptgold service status
```

---

### `service list`

List all available services (enabled and disabled).

**Syntax:**
```bash
deceptgold service list
```

**Output:**
```
[Deceptgold System Daemon]
PID: 12345

Deceptgold Service Inventory
Layer  Service  Port  Status  Configured
Web2   SSH      22    OPEN    YES
Web2   HTTP     80    OPEN    YES
Web3   RPC      8545  CLOSED  NO
```

**Example:**
```bash
deceptgold service list
```

---

### `service enable`

Enable a specific honeypot service.

**Syntax:**
```bash
deceptgold service enable <SERVICE_NAME>
```

**Parameters:**
- `<SERVICE_NAME>` - Name of service to enable (e.g., `ssh`, `http`, `ftp`)

**Examples:**
```bash
# Enable SSH honeypot
deceptgold service enable ssh

# Enable HTTP honeypot
deceptgold service enable http

# Enable MySQL honeypot
deceptgold service enable mysql
```

**Notes:**
- Changes take effect after service restart
- Service must be in available services list

---

### `service disable`

Disable a specific honeypot service.

**Syntax:**
```bash
deceptgold service disable <SERVICE_NAME>
```

**Parameters:**
- `<SERVICE_NAME>` - Name of service to disable

**Examples:**
```bash
# Disable SSH honeypot
deceptgold service disable ssh

# Disable FTP honeypot
deceptgold service disable ftp
```

**Notes:**
- Changes take effect after service restart
- Disabled services won't log attacks

---

### `service set`

Change the port of a specific service.

**Syntax:**
```bash
deceptgold service set <SERVICE_NAME> <PORT>
```

**Parameters:**
- `<SERVICE_NAME>` - Name of service
- `<PORT>` - New port number (1-65535)

**Examples:**
```bash
# Change SSH to port 2222
deceptgold service set ssh 2222

# Change HTTP to port 8080
deceptgold service set http 8080
```

**Notes:**
- Requires service restart to apply
- Ensure port is not already in use
- Some ports require root/admin privileges (< 1024)

---

## Notify Commands

Configure notification channels for attack alerts.

### `notify --telegram=true`

Enable Telegram notifications.

**Syntax:**
```bash
deceptgold notify --telegram=true
```

**Process:**
1. Command displays QR code in terminal
2. Scan QR code with Telegram app
3. Automatic synchronization
4. Receive attack notifications

**Example:**
```bash
deceptgold notify --telegram=true
```

---

### `notify --telegram=false`

Disable Telegram notifications.

**Syntax:**
```bash
deceptgold notify --telegram=false
```

**Example:**
```bash
deceptgold notify --telegram=false
```

---

### `notify webhook`

Configure webhook endpoints for notifications.

**Syntax:**
```bash
deceptgold notify webhook <TYPE>=<URL>
```

**Supported Types:**
- `custom` - Custom webhook endpoint
- `slack` - Slack webhook
- `discord` - Discord webhook
- `jira` - Jira webhook

**Examples:**
```bash
# Custom webhook
deceptgold notify webhook custom="https://example.com/webhook"

# Slack webhook
deceptgold notify webhook slack="https://hooks.slack.com/services/G1Z/BQA/71cKYc"

# Discord webhook
deceptgold notify webhook discord="https://discord.com/api/webhooks/1238/abRSTUVWX"

# Jira webhook
deceptgold notify webhook jira="https://api.yoursite.com/jira/webhook"
```

**Webhook Payload Format:**
```json
{
  "timestamp": "2025-12-22T19:58:22Z",
  "event": "attack_detected",
  "service": "ssh",
  "source_ip": "192.168.1.100",
  "attack_type": "brute_force",
  "requests_count": 1500,
  "node_id": "production-honeypot-01"
}
```

**Notes:**
- URL must be valid HTTPS endpoint
- Multiple webhooks can be configured
- Webhooks receive real-time attack notifications

---

## Examples

### Complete Setup Workflow

```bash
# 1. Configure wallet address
deceptgold user --my-address 0x0105d8Ceab792bfece1b2994B71992Af56930081

# 2. Enable desired services
deceptgold service enable ssh
deceptgold service enable http
deceptgold service enable ftp

# 3. Configure notifications
deceptgold notify --telegram=true
deceptgold notify webhook slack="https://hooks.slack.com/services/..."

# 4. Start the service
deceptgold service start

# 5. Check status
deceptgold service status

# 6. View balance (after some attacks)
deceptgold user --show-balance
```

### Testing Configuration

```bash
# Start in foreground to see logs
deceptgold service start daemon=false debug=true

# In another terminal, check status
deceptgold service status

# Stop when done testing
deceptgold service stop
```

### Production Deployment

```bash
# Configure wallet
deceptgold user --my-address 0xYourProductionWallet

# Set custom node identifier
deceptgold service --node_id "prod-dmz-honeypot-01"

# Enable all services
deceptgold service enable ssh
deceptgold service enable http
deceptgold service enable https
deceptgold service enable ftp
deceptgold service enable mysql

# Configure monitoring
deceptgold notify webhook custom="https://monitoring.company.com/webhook"

# Start in daemon mode
deceptgold service start

# Verify everything is running
deceptgold service status
```

### Troubleshooting

```bash
# Check if service is running
deceptgold service status

# View detailed status
deceptgold service list

# Restart service
deceptgold service restart

# Start with debug output
deceptgold service start daemon=false debug=true

# Check balance to verify blockchain connection
deceptgold user --show-balance
```

## Configuration Files

### User Configuration
- **Location**: `~/.deceptgold/config.json`
- **Contains**: Wallet address, blockchain settings

### Service Configuration
- **Location**: `~/.deceptgold/opencanary.conf`
- **Contains**: Enabled services, ports, banners

### Logs
- **Attack Logs**: `/var/log/deceptgold/attacks.log`
- **Application Logs**: `/var/log/deceptgold/deceptgold.log`
- **PID File**: `/tmp/deceptgold.pid` or `~/.deceptgold/deceptgold.pid`

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error (missing wallet, invalid arguments, etc.) |
| 2 | Service already running |
| 3 | Permission denied |

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DECEPTGOLD_CONFIG_DIR` | Configuration directory | `~/.deceptgold` |
| `DECEPTGOLD_LOG_LEVEL` | Logging verbosity | `INFO` |
| `DECEPTGOLD_RPC_URL` | Custom blockchain RPC endpoint | (uses config) |

## See Also

- [index.md](index.md) - Quick start guide
- [Development.md](Development.md) - Development guide
- [Testing.md](Testing.md) - Testing procedures
- [Blockchain.md](Blockchain.md) - Blockchain details

---

**Need help?** Contact: jsmorais@pm.me
