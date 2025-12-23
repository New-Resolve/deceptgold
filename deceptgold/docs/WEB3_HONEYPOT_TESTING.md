# Web3 Honeypot Testing Guide

Guia completo para testar os honeypots Web3 do Deceptgold.

## Índice

- [Configuração do Ambiente de Testes](#configuração-do-ambiente-de-testes)
- [Executando Testes Unitários](#executando-testes-unitários)
- [Simulando Ataques](#simulando-ataques)
- [Verificando Logs e Recompensas](#verificando-logs-e-recompensas)
- [Testes de Integração](#testes-de-integração)

## Configuração do Ambiente de Testes

### 1. Instalar Dependências de Teste

```bash
cd deceptgold/deceptgold

# Instalar dependências de teste
poetry install --with dev

# Verificar instalação
poetry run pytest --version
```

### 2. Configurar Honeypots Web3

```bash
# Habilitar serviços Web3 para teste
poetry run python -m deceptgold service enable web3.rpc_node
poetry run python -m deceptgold service enable web3.wallet_service
poetry run python -m deceptgold service enable web3.defi_protocol

# Configurar portas (opcional)
poetry run python -m deceptgold service set web3.rpc_node 8545
poetry run python -m deceptgold service set web3.wallet_service 8546
poetry run python -m deceptgold service set web3.defi_protocol 8548
```

## Executando Testes Unitários

### Todos os Testes

```bash
# Executar todos os testes Web3
poetry run pytest tests/test_web3_honeypots.py -v

# Com cobertura
poetry run pytest tests/test_web3_honeypots.py --cov=deceptgold.helper.web3honeypot --cov-report=html

# Ver relatório de cobertura
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### Testes Específicos por Serviço

#### RPC Node Honeypot

```bash
# Todos os testes do RPC node
poetry run pytest tests/test_web3_honeypots.py::TestRPCNodeHoneypot -v

# Teste específico
poetry run pytest tests/test_web3_honeypots.py::TestRPCNodeHoneypot::test_personal_unlockAccount_detected -v
```

**Testes Incluídos:**
- ✅ `test_initialization` - Verifica inicialização correta
- ✅ `test_eth_getBalance_returns_fake_balance` - Verifica balances falsos atrativos
- ✅ `test_personal_unlockAccount_detected` - Detecta tentativas de unlock (CRÍTICO)
- ✅ `test_eth_sendRawTransaction_malicious_detected` - Detecta transações maliciosas
- ✅ `test_eth_call_contract_exploit_detected` - Detecta exploração de contratos
- ✅ `test_multiple_getBalance_calls_detected_as_scanning` - Detecta varredura de endereços

#### Wallet Service Honeypot

```bash
# Todos os testes do wallet service
poetry run pytest tests/test_web3_honeypots.py::TestWalletServiceHoneypot -v
```

**Testes Incluídos:**
- ✅ `test_wallet_import_seed_phrase_phishing` - Detecta phishing de seed phrases (CRÍTICO)
- ✅ `test_wallet_export_private_key_attempt` - Detecta export de chaves privadas
- ✅ `test_malicious_transaction_signing` - Detecta assinatura de transações maliciosas
- ✅ `test_brute_force_password_detected` - Detecta força bruta em senhas

#### IPFS Gateway Honeypot

```bash
# Todos os testes do IPFS gateway
poetry run pytest tests/test_web3_honeypots.py::TestIPFSGatewayHoneypot -v
```

**Testes Incluídos:**
- ✅ `test_malicious_file_upload_detected` - Detecta uploads maliciosos
- ✅ `test_path_traversal_attempt_detected` - Detecta path traversal
- ✅ `test_dos_via_massive_uploads` - Detecta DoS via uploads massivos

#### DeFi Protocol Honeypot

```bash
# Todos os testes do DeFi protocol
poetry run pytest tests/test_web3_honeypots.py::TestDeFiProtocolHoneypot -v
```

**Testes Incluídos:**
- ✅ `test_flash_loan_attack_detected` - Detecta flash loan attacks (ALTO VALOR)
- ✅ `test_reentrancy_attempt_detected` - Detecta ataques de reentrancy
- ✅ `test_sandwich_attack_detected` - Detecta sandwich attacks (front-running)
- ✅ `test_price_manipulation_detected` - Detecta manipulação de oráculos de preço

#### NFT Marketplace Honeypot

```bash
# Todos os testes do NFT marketplace
poetry run pytest tests/test_web3_honeypots.py::TestNFTMarketplaceHoneypot -v
```

**Testes Incluídos:**
- ✅ `test_wash_trading_detected` - Detecta wash trading
- ✅ `test_floor_price_manipulation` - Detecta manipulação de floor price
- ✅ `test_malicious_approval_exploit` - Detecta exploits de aprovação

#### Blockchain Explorer API Honeypot

```bash
# Todos os testes do explorer API
poetry run pytest tests/test_web3_honeypots.py::TestBlockchainExplorerAPIHoneypot -v
```

**Testes Incluídos:**
- ✅ `test_api_scraping_detected` - Detecta scraping de API
- ✅ `test_rate_limit_exploitation` - Detecta exploração de rate limits
- ✅ `test_contract_vulnerability_search` - Detecta busca por contratos vulneráveis

### Testes de Integração

```bash
# Executar testes de integração
poetry run pytest tests/test_web3_honeypots.py::TestWeb3HoneypotIntegration -v
```

**Testes Incluídos:**
- ✅ `test_all_honeypots_can_start` - Verifica que todos os honeypots inicializam
- ✅ `test_reward_generation_for_all_attack_types` - Verifica geração de recompensas

## Simulando Ataques

### Usando o Simulador de Ataques

O simulador permite testar os honeypots com ataques realistas.

#### Executar Todos os Ataques

```bash
# Executar todas as simulações de ataque
poetry run python utils/web3_attack_simulator.py --attack all

# Contra honeypot remoto
poetry run python utils/web3_attack_simulator.py --host 192.168.1.100 --attack all
```

#### Ataques Individuais

**RPC Node Attacks:**

```bash
# Tentativa de unlock de conta (CRÍTICO - 100 DGLD)
poetry run python utils/web3_attack_simulator.py --attack rpc_unlock

# Varredura de balances (20 DGLD)
poetry run python utils/web3_attack_simulator.py --attack balance_scan

# Transação maliciosa (50 DGLD)
poetry run python utils/web3_attack_simulator.py --attack malicious_tx
```

**Wallet Service Attacks:**

```bash
# Phishing de seed phrase (CRÍTICO - 150 DGLD)
poetry run python utils/web3_attack_simulator.py --attack seed_phishing

# Export de chave privada (120 DGLD)
poetry run python utils/web3_attack_simulator.py --attack key_export
```

**IPFS Gateway Attacks:**

```bash
# Upload malicioso (30 DGLD)
poetry run python utils/web3_attack_simulator.py --attack ipfs_upload

# Path traversal (40 DGLD)
poetry run python utils/web3_attack_simulator.py --attack ipfs_traversal
```

**DeFi Protocol Attacks:**

```bash
# Flash loan attack (ALTO VALOR - 200 DGLD)
poetry run python utils/web3_attack_simulator.py --attack flash_loan

# Reentrancy attack (180 DGLD)
poetry run python utils/web3_attack_simulator.py --attack reentrancy

# Sandwich attack (100 DGLD)
poetry run python utils/web3_attack_simulator.py --attack sandwich
```

**NFT Marketplace Attacks:**

```bash
# Wash trading (40 DGLD)
poetry run python utils/web3_attack_simulator.py --attack wash_trading
```

**Blockchain Explorer Attacks:**

```bash
# API scraping (20 DGLD)
poetry run python utils/web3_attack_simulator.py --attack api_scraping
```

### Ataques Manuais com curl

#### RPC Node - Account Unlock

```bash
curl -X POST http://localhost:8545 \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "personal_unlockAccount",
    "params": ["0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb", "password123", 300],
    "id": 1
  }'
```

**Resultado Esperado:**
- ✅ Log gerado com `attack_type: rpc_account_unlock_attempt`
- ✅ Severidade: `critical`
- ✅ Recompensa: 100 DGLD

#### Wallet Service - Seed Phrase Phishing

```bash
curl -X POST http://localhost:8546/api/v1/wallet/import \
  -H "Content-Type: application/json" \
  -d '{
    "seed_phrase": "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon art"
  }'
```

**Resultado Esperado:**
- ✅ Log gerado com `attack_type: wallet_seed_phrase_phishing`
- ✅ Severidade: `critical`
- ✅ Recompensa: 150 DGLD
- ✅ Notificação enviada ao admin

#### DeFi Protocol - Flash Loan

```bash
curl -X POST http://localhost:8548/api/v1/flashloan \
  -H "Content-Type: application/json" \
  -d '{
    "token": "0x1234567890123456789012345678901234567890",
    "amount": "1000000000000000000000000",
    "callback_data": "0xaaaaaaaaaaaaaaaaaaaaaaaa"
  }'
```

**Resultado Esperado:**
- ✅ Log gerado com `attack_type: defi_flash_loan_attack`
- ✅ Severidade: `high`
- ✅ Recompensa: 200 DGLD (MUITO ALTO)

## Verificando Logs e Recompensas

### Verificar Logs de Ataque

```bash
# Ver logs em tempo real
tail -f /var/log/deceptgold/attacks.log

# Filtrar apenas ataques Web3
grep "logtype.*5000" /var/log/deceptgold/attacks.log

# Ver ataques críticos
grep "severity.*critical" /var/log/deceptgold/attacks.log
```

### Formato de Log Web3

```json
{
    "timestamp": "2025-12-22T21:00:00Z",
    "logtype": 5000,
    "service": "web3_rpc_node",
    "attack_type": "rpc_account_unlock_attempt",
    "src_host": "192.168.1.100",
    "details": {
        "method": "personal_unlockAccount",
        "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
        "duration": 300
    },
    "severity": "critical",
    "reward_tokens": 100
}
```

### Verificar Recompensas Geradas

```bash
# Ver balance de tokens
poetry run python -m deceptgold user --show-balance

# Ver histórico de recompensas
grep "reward_tokens" /var/log/deceptgold/attacks.log | jq '.reward_tokens' | awk '{sum+=$1} END {print "Total:", sum, "DGLD"}'
```

## Testes de Performance

### Teste de Carga - RPC Node

```bash
# Instalar Apache Bench
sudo apt install apache2-utils

# Teste de carga
ab -n 1000 -c 10 -p rpc_request.json -T application/json http://localhost:8545/
```

**Arquivo `rpc_request.json`:**
```json
{
    "jsonrpc": "2.0",
    "method": "eth_blockNumber",
    "params": [],
    "id": 1
}
```

### Teste de Carga - Wallet Service

```bash
# Teste de múltiplas requisições simultâneas
for i in {1..100}; do
    curl -X POST http://localhost:8546/api/v1/wallet/balance \
      -H "Content-Type: application/json" \
      -d '{"wallet_id": "wallet_'$i'"}' &
done
wait
```

## Troubleshooting

### Testes Falhando

```bash
# Limpar cache do pytest
poetry run pytest --cache-clear

# Executar com mais verbosidade
poetry run pytest tests/test_web3_honeypots.py -vv

# Ver output completo
poetry run pytest tests/test_web3_honeypots.py -s
```

### Honeypots Não Respondendo

```bash
# Verificar se serviços estão rodando
poetry run python -m deceptgold service status

# Verificar portas abertas
netstat -tuln | grep -E "8545|8546|8547|8548|8549"

# Reiniciar serviços
poetry run python -m deceptgold service restart
```

### Logs Não Sendo Gerados

```bash
# Verificar permissões do diretório de logs
ls -la /var/log/deceptgold/

# Criar diretório se não existir
sudo mkdir -p /var/log/deceptgold/
sudo chown -R $USER:$USER /var/log/deceptgold/

# Verificar configuração de logging
cat ~/.opencanary.conf | grep -A 5 "logger"
```

## Tabela de Recompensas Esperadas

| Tipo de Ataque | Severidade | Recompensa (DGLD) |
|----------------|------------|-------------------|
| Flash Loan Attack | High | 200 |
| Reentrancy Attack | High | 180 |
| Seed Phrase Phishing | Critical | 150 |
| Private Key Export | Critical | 120 |
| RPC Account Unlock | Critical | 100 |
| Sandwich Attack | Medium | 100 |
| NFT Approval Exploit | Medium | 80 |
| Malicious Transaction | Medium | 50 |
| NFT Wash Trading | Low | 40 |
| IPFS Path Traversal | Low | 40 |
| IPFS Malicious Upload | Low | 30 |
| API Scraping | Low | 20 |

## Exemplos de Saída de Testes

### Teste Bem-Sucedido

```
tests/test_web3_honeypots.py::TestRPCNodeHoneypot::test_personal_unlockAccount_detected PASSED [100%]

================================ 1 passed in 0.15s =================================
```

### Teste com Cobertura

```
---------- coverage: platform linux, python 3.12.11 -----------
Name                                              Stmts   Miss  Cover
---------------------------------------------------------------------
deceptgold/helper/web3honeypot/__init__.py            5      0   100%
deceptgold/helper/web3honeypot/rpc_node.py          120      8    93%
deceptgold/helper/web3honeypot/wallet_service.py     95      5    95%
deceptgold/helper/web3honeypot/defi_protocol.py     150     12    92%
---------------------------------------------------------------------
TOTAL                                               370     25    93%
```

## Próximos Passos

1. Execute todos os testes unitários
2. Simule ataques individuais
3. Verifique logs e recompensas
4. Execute testes de carga
5. Revise cobertura de testes

---

**Dúvidas?** Consulte a [documentação completa](../BLOCKCHAIN_INTEGRATION.md) ou abra uma issue no GitHub.
