#!/bin/bash

set -euo pipefail

API_KEY="${VIRUSTOTAL_API_KEY:-}"

if [ -z "$API_KEY" ]; then
  echo "❌ VirusTotal API key not set. Set the VIRUSTOTAL_API_KEY environment variable."
  exit 1
fi

ARTIFACTS=$(find deceptgold/dist -type f)

for ARTIFACT in $ARTIFACTS; do
  echo "🔎 Checking $ARTIFACT with VirusTotal"

  SHA256_HASH=$(sha256sum "$ARTIFACT" | cut -d ' ' -f1)
  RESPONSE=$(curl -s --request GET "https://www.virustotal.com/api/v3/files/$SHA256_HASH" \
    --header "x-apikey: $API_KEY")

  if echo "$RESPONSE" | jq -e '.data' >/dev/null 2>&1; then
    echo "📦 Hash found. Checking status..."
  else
    echo "📤 Hash not found. Sending $ARTIFACT pfor scanning..."
    UPLOAD_RESPONSE=$(curl -s --request POST "https://www.virustotal.com/api/v3/files" \
      --header "x-apikey: $API_KEY" \
      --form "file=@$ARTIFACT")

    if echo "$UPLOAD_RESPONSE" | jq . >/dev/null 2>&1; then
      ANALYSIS_ID=$(echo "$UPLOAD_RESPONSE" | jq -r '.data.id')
    else
      echo "❌ Invalid JSON response from VirusTotal:"
      echo "$UPLOAD_RESPONSE"
      exit 1
    fi

    if [ "$ANALYSIS_ID" = "null" ]; then
      echo "❌ Error uploading file to VirusTotal."
      echo "$UPLOAD_RESPONSE"
      exit 1
    fi

    echo "⏳ Waiting for analysis to complete..."
    while true; do
      ANALYSIS_RESPONSE=$(curl -s --request GET "https://www.virustotal.com/api/v3/analyses/$ANALYSIS_ID" \
        --header "x-apikey: $API_KEY")

      STATUS=$(echo "$ANALYSIS_RESPONSE" | jq -r '.data.attributes.status')
      if [ "$STATUS" == "completed" ]; then
        echo "✅ Analysis complete!"
        break
      fi
      sleep 5
    done

    RESPONSE=$(curl -s --request GET "https://www.virustotal.com/api/v3/files/$SHA256_HASH" \
      --header "x-apikey: $API_KEY")
  fi

  DETECTIONS=$(echo "$RESPONSE" | jq '.data.attributes.last_analysis_stats.malicious // 0')

  if [[ "$DETECTIONS" -gt 0 ]]; then
    echo "❌ WARNING: $DETECTIONS mechanisms identified $ARTIFACT as malicious."
    exit 1
  else
    echo "✅ $ARTIFACT passed clean ($DETECTIONS detections)."
  fi
done
