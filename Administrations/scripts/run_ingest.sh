#!/usr/bin/env bash
set -euo pipefail

# Required env vars:
#   SUBJECT="..."
#   URLS_FILE="path/to/sources.urls.txt"
#
# Optional:
#   TOPIC_CLUSTER="general" (default)
#   OUT_DIR="data"          (if your ingest supports it; safe to ignore)

: "${SUBJECT:?SUBJECT env var is required}"
: "${URLS_FILE:?URLS_FILE env var is required}"

TOPIC_CLUSTER="${TOPIC_CLUSTER:-general}"

echo "== ingest =="
echo "SUBJECT:       $SUBJECT"
echo "TOPIC_CLUSTER: $TOPIC_CLUSTER"
echo "URLS_FILE:     $URLS_FILE"
echo

python CORE/ingest_pipeline/url_list_ingest.py \
  --subject "$SUBJECT" \
  --topic_cluster "$TOPIC_CLUSTER" \
  --urls "$URLS_FILE"
