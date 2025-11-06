#!/bin/bash
# Chạy proxy ở chế độ ONLINE (dùng cache + fetch từ internet khi cần)

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "🌐 Starting Proxy in ONLINE Mode"
echo "=========================================="
echo ""
echo "Mode: ONLINE (cache + live fallback)"
echo "URL: http://localhost:5002"
echo ""
echo "✅ Sẽ fetch từ internet nếu cache miss"
echo ""
echo "Press Ctrl+C to stop"
echo ""
echo "=========================================="
echo ""

# Bật LIVE_FALLBACK để fetch khi cache miss
export LIVE_FALLBACK=true
export ORIGIN="https://kiagds.ru"
export LOCAL_BASE="http://localhost:5002"
export CACHE_DIR="cache"

python3 app.py

