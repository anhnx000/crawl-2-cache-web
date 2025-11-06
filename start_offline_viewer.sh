#!/bin/bash
# Chạy proxy offline viewer ở port 5003
# Read-only: Chỉ đọc cache, không ảnh hưởng đến crawl process ở port 5002

cd /home/xuananh/work_1/anhnx/crawl-2

echo "╔════════════════════════════════════════════════════════════╗"
echo "║       🔌 Offline Viewer - Port 5003                        ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Mode: OFFLINE ONLY (read-only)"
echo "Port: 5003"
echo "URL: http://localhost:5003"
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

# Kiểm tra port 5003
if lsof -i :5003 > /dev/null 2>&1; then
    echo "⚠️  Port 5003 đang được sử dụng!"
    echo "   Đang dừng process cũ..."
    pkill -f "app_offline_viewer.py"
    sleep 2
fi

# Set environment variables
export LIVE_FALLBACK=false  # OFFLINE ONLY (hardcode trong code, nhưng set để rõ ràng)
export ORIGIN="https://kiagds.ru"
export LOCAL_BASE="http://localhost:5003"  # Port 5003
export CACHE_DIR="cache"  # Dùng chung cache với crawl process

# Chạy proxy offline viewer
python3 app_offline_viewer.py

