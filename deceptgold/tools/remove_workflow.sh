#!/usr/bin/env bash
set -euo pipefail

KEEP="21356090750"

# Lista explícita dos workflows (IDs)
WORKFLOWS=(
  154593920   # Build and Release Deceptgold
  158657684   # Dependabot Updates
  218513724   # pages-build-deployment
)

while true; do
  FOUND=0

  for WF in "${WORKFLOWS[@]}"; do
    echo ">>> Processando workflow $WF"

    # Busca até 100 por vez
    RUNS=$(gh run list --workflow "$WF" --limit 100 --json databaseId -q '.[].databaseId')

    for run_id in $RUNS; do
      if [ "$run_id" != "$KEEP" ]; then
        FOUND=1
        echo "Deletando run $run_id (workflow $WF)"
        gh run delete "$run_id"
        sleep 0.3
      else
        echo "Mantendo run $run_id (KEEP)"
      fi
    done
  done

  if [ "$FOUND" -eq 0 ]; then
    echo "✅ Nenhuma run restante para deletar. Finalizado."
    break
  fi

  echo "🔁 Novo ciclo para pegar próxima página..."
  sleep 2
done
