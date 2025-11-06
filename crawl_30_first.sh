#!/bin/bash
# Cache 30 URLs đầu tiên từ important_links.json (để test)

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "Cache 30 URLs đầu tiên"
echo "=========================================="
echo ""

python3 auto_crawl_proxy.py \
  --json-file important_links.json \
  --json-start-index 0 \
  --json-end-index 30 \
  --follow-depth 3 \
  --concurrency 5 \
  --delay 0.3 \
  --max-retries 10 \
  --auto-pagination

echo ""
echo "✅ Hoàn thành!"

