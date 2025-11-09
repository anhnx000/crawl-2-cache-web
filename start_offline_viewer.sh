#!/bin/bash
# Chạy proxy offline viewer ở port tùy chọn (mặc định 5003)
# Read-only: Chỉ đọc cache, không ảnh hưởng đến crawl process ở port 5002

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PORT="${1:-5003}"

echo "╔════════════════════════════════════════════════════════════╗"
echo "║       🔌 Offline Viewer - Port $PORT                        ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Mode: OFFLINE ONLY (read-only)"
echo "Port: $PORT"
echo "URL: http://localhost:$PORT"
echo ""
echo "✅ Dùng chung cache với crawl process (port 5002)"
echo "✅ Không ảnh hưởng đến quá trình crawl"
echo "✅ Chỉ hiển thị URLs đã cache"
echo ""
echo "⚠️  URLs chưa cache sẽ hiển thị 404"
echo ""
echo "Press Ctrl+C to stop"
echo ""
echo "════════════════════════════════════════════════════════════"
echo ""

# Kiểm tra port
if lsof -i :"$PORT" > /dev/null 2>&1; then
    echo "⚠️  Port $PORT đang được sử dụng!"
    echo "   Đang dừng process cũ..."
    pkill -f "app_offline_viewer.py"
    sleep 2
fi

# Set environment variables
export LIVE_FALLBACK=false  # OFFLINE ONLY (hardcode trong code, nhưng set để rõ ràng)
export ORIGIN="https://kiagds.ru"
export OFFLINE_PORT="$PORT"
export LOCAL_BASE="http://localhost:$PORT"  # Đồng bộ với OFFLINE_PORT
export CACHE_DIR="cache"  # Dùng chung cache với crawl process

# Chạy proxy offline viewer
python3 app_offline_viewer.py

