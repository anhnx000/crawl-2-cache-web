#!/bin/bash
# Chạy proxy ở chế độ OFFLINE (chỉ dùng cache)

cd /home/xuananh/work_1/anhnx/crawl-2

echo "=========================================="
echo "🔌 Starting Proxy in OFFLINE Mode"
echo "=========================================="
echo ""
echo "Mode: OFFLINE (cache only, no internet)"
echo "URL: http://localhost:5002"
echo ""
echo "⚠️  Chỉ các URLs đã cache mới có thể truy cập!"
echo ""
echo "Press Ctrl+C to stop"
echo ""
echo "=========================================="
echo ""

# Tắt LIVE_FALLBACK để chỉ dùng cache
export LIVE_FALLBACK=false
export ORIGIN="https://kiagds.ru"
export LOCAL_BASE="http://localhost:5002"
export CACHE_DIR="cache"

python3 app.py

