#!/bin/bash

HOST="localhost"
USER="root"
PASS="admin"
TRIES=100000
PORT=2223
DELAY=0

echo "Testando rate limit contra SSH em $HOST com $TRIES tentativas..."

# Função para testar conexão SSH
test_ssh() {
    sshpass -p "$PASS" ssh -p "$PORT" -o StrictHostKeyChecking=no -o ConnectTimeout=3 -o PreferredAuthentications=password -o PubkeyAuthentication=no "$USER@$HOST" "exit" 2>&1 \
    | grep -E "Permission denied|Connection refused|Connection timed out|Too many authentication failures|broken|reset|denied"
}

# Rodando as tentativas em paralelo
for i in $(seq 1 $TRIES); do
    echo "Tentativa $i: "
    test_ssh &  # Coloca o processo em segundo plano
    sleep $DELAY
done

# Espera todos os processos terminarem antes de finalizar
wait

echo "Teste finalizado."
