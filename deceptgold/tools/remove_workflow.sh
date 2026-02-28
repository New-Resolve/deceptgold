#!/usr/bin/env bash
set -euo pipefail

KEEP="22520731003"

# Explicit list of workflows (IDs)
WORKFLOWS=(
  154593920   # Build and Release Deceptgold
  158657684   # Dependabot Updates
  218513724   # pages-build-deployment
)

while true; do
  FOUND=0

  for WF in "${WORKFLOWS[@]}"; do
    echo ">>> Processing workflow $WF"

    # Fetch up to 100 at a time
    RUNS=$(gh run list --workflow "$WF" --limit 100 --json databaseId -q '.[].databaseId')

    for run_id in $RUNS; do
      if [ "$run_id" != "$KEEP" ]; then
        FOUND=1
        echo "Deleting run $run_id (workflow $WF)"
        gh run delete "$run_id"
        sleep 0.3
      else
        echo "Keeping run $run_id (KEEP)"
      fi
    done
  done

  if [ "$FOUND" -eq 0 ]; then
    echo "No remaining runs to delete. Finished."
    break
  fi

  echo "New cycle to fetch next page..."
  sleep 2
done