#!/bin/bash
# ALL-IN-ONE: Tự động chạy cả proxy và crawler

cd /home/xuananh/work_1/anhnx/crawl-2

echo "╔════════════════════════════════════════════════════════════╗"
echo "║       🚀 ALL-IN-ONE: Proxy + Crawler + Monitor            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Hàm cleanup khi Ctrl+C
cleanup() {
    echo ""
    echo "🛑 Stopping all processes..."
    pkill -P $$ 2>/dev/null
    pkill -f "python3 app.py" 2>/dev/null
    pkill -f "auto_crawl_proxy.py" 2>/dev/null
    echo "✅ All stopped"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Bước 1: Kiểm tra và dừng process cũ
echo "📋 Step 1: Kiểm tra processes cũ..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if lsof -i :5002 > /dev/null 2>&1; then
    echo "   ⚠️  Port 5002 đang được sử dụng, dừng process cũ..."
    pkill -f "python3 app.py"
    sleep 2
fi

if pgrep -f "auto_crawl_proxy.py.*important_links" > /dev/null; then
    echo "   ⚠️  Crawler cũ đang chạy, dừng..."
    pkill -f "auto_crawl_proxy.py.*important_links"
    sleep 2
fi

echo "   ✅ Ready to start"
echo ""

# Bước 2: Start proxy
echo "📋 Step 2: Starting Proxy (Online Mode)..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

export LIVE_FALLBACK=true
export ORIGIN="https://kiagds.ru"
export LOCAL_BASE="http://localhost:5002"
export CACHE_DIR="cache"

# Chạy proxy trong background
nohup python3 app.py > proxy.log 2>&1 &
PROXY_PID=$!

echo "   🌐 Starting proxy (PID: $PROXY_PID)..."
sleep 3

# Kiểm tra proxy
if curl -s -o /dev/null -w "%{http_code}" "http://localhost:5002/_cache_stats" | grep -q "200"; then
    echo "   ✅ Proxy đã chạy tại http://localhost:5002"
    
    # Lấy stats
    STATS=$(curl -s "http://localhost:5002/_cache_stats" 2>/dev/null)
    CACHED=$(echo "$STATS" | python3 -c "import sys, json; print(json.load(sys.stdin).get('cached_responses', 'N/A'))" 2>/dev/null || echo "N/A")
    echo "   • Cached responses: $CACHED"
    echo ""
else
    echo "   ❌ Proxy không khởi động được!"
    echo "   📝 Xem log: cat proxy.log"
    exit 1
fi

# Bước 3: Start crawler
echo "📋 Step 3: Starting Crawler..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "   Total URLs: 16,304"
echo "   Follow depth: 3"
echo "   Concurrency: 5"
echo ""

# Chạy crawler trong background
nohup python3 auto_crawl_proxy.py \
  --json-file important_links.json \
  --follow-depth 3 \
  --concurrency 5 \
  --delay 0.3 \
  --max-retries 10 \
  --auto-pagination \
  > cache_important_full.log 2>&1 &

CRAWLER_PID=$!
echo "   🚀 Starting crawler (PID: $CRAWLER_PID)..."
sleep 3

# Kiểm tra crawler
if ps -p $CRAWLER_PID > /dev/null; then
    echo "   ✅ Crawler đã chạy!"
    echo ""
else
    echo "   ❌ Crawler không khởi động được!"
    echo "   📝 Xem log: cat cache_important_full.log"
    exit 1
fi

# Bước 4: Monitor
echo "╔════════════════════════════════════════════════════════════╗"
echo "║              ✅ ĐÃ CHẠY THÀNH CÔNG!                       ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "📊 Processes:"
echo "   • Proxy PID: $PROXY_PID (http://localhost:5002)"
echo "   • Crawler PID: $CRAWLER_PID"
echo ""
echo "📝 Logs:"
echo "   • Proxy: tail -f proxy.log"
echo "   • Crawler: tail -f cache_important_full.log"
echo ""
echo "📊 Monitor:"
echo "   • Quick check: ./check_progress.sh"
echo "   • Watch: watch -n 10 './check_progress.sh'"
echo ""
echo "🛑 Stop ALL:"
echo "   • Ctrl+C (trong terminal này)"
echo "   • pkill -f 'python3 app.py'"
echo "   • pkill -f 'auto_crawl_proxy.py'"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎯 Showing crawler log (realtime)..."
echo "   Press Ctrl+C to stop monitoring (processes continue)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Wait một chút để crawler bắt đầu
sleep 3

# Tail log realtime
tail -f cache_important_full.log

