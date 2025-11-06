#!/bin/bash
# Script kiểm tra và hướng dẫn chạy crawl full

echo "╔════════════════════════════════════════════════════════════╗"
echo "║     🚀 START FULL CRAWL - 16,304 Important Links          ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

cd /home/xuananh/work_1/anhnx/crawl-2

# Bước 1: Kiểm tra proxy
echo "📋 Step 1: Kiểm tra proxy..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if curl -s -o /dev/null -w "%{http_code}" "http://localhost:5002/_cache_stats" | grep -q "200"; then
    echo "   ✅ Proxy đang chạy tại http://localhost:5002"
    
    # Lấy stats
    STATS=$(curl -s "http://localhost:5002/_cache_stats")
    CACHED=$(echo "$STATS" | python3 -c "import sys, json; print(json.load(sys.stdin).get('cached_responses', 'N/A'))" 2>/dev/null || echo "N/A")
    LIVE=$(echo "$STATS" | python3 -c "import sys, json; print(json.load(sys.stdin).get('live_fallback', 'N/A'))" 2>/dev/null || echo "N/A")
    
    echo "   • Cached responses: $CACHED"
    echo "   • Live fallback: $LIVE"
    echo ""
    
    PROXY_OK=true
else
    echo "   ❌ Proxy KHÔNG chạy!"
    echo ""
    echo "   💡 Hãy mở terminal mới và chạy:"
    echo ""
    echo "   cd /home/xuananh/work_1/anhnx/crawl-2"
    echo "   ./start_online.sh"
    echo ""
    echo "   (Giữ terminal đó chạy)"
    echo ""
    
    read -p "   Nhấn ENTER khi đã chạy proxy... " dummy
    
    # Kiểm tra lại
    if curl -s -o /dev/null -w "%{http_code}" "http://localhost:5002/_cache_stats" | grep -q "200"; then
        echo "   ✅ Proxy đã chạy!"
        echo ""
        PROXY_OK=true
    else
        echo "   ❌ Vẫn không kết nối được proxy"
        echo "   ⚠️  Không thể tiếp tục!"
        echo ""
        exit 1
    fi
fi

# Bước 2: Kiểm tra crawler đang chạy chưa
echo "📋 Step 2: Kiểm tra crawler..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if pgrep -f "auto_crawl_proxy.py.*important_links.json" > /dev/null; then
    echo "   ⚠️  Crawler đã đang chạy!"
    PID=$(pgrep -f "auto_crawl_proxy.py.*important_links.json")
    echo "   PID: $PID"
    echo ""
    
    read -p "   Bạn có muốn dừng và chạy lại? (y/n): " answer
    if [ "$answer" = "y" ] || [ "$answer" = "Y" ]; then
        pkill -f "auto_crawl_proxy.py.*important_links.json"
        echo "   ✅ Đã dừng crawler cũ"
        sleep 2
    else
        echo "   ℹ️  Giữ nguyên crawler đang chạy"
        echo ""
        echo "   📊 Xem tiến trình:"
        echo "      tail -f cache_important_full_depth50_concurrency10.log"
        echo ""
        exit 0
    fi
fi

# Bước 3: Bắt đầu crawl
echo ""
echo "📋 Step 3: Bắt đầu crawl FULL"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
TOTAL_URLS=$(python3 -c "import json; print(len(json.load(open('important_links.json'))))" 2>/dev/null || echo "16,304")
echo "   Total URLs: $TOTAL_URLS"
echo "   Follow depth: 50"
echo "   Concurrency: 10"
echo "   Delay: 0.3s"
echo "   Log file: cache_important_full_depth50_concurrency10.log"
echo ""

read -p "   Bắt đầu crawl? (y/n): " answer
if [ "$answer" != "y" ] && [ "$answer" != "Y" ]; then
    echo "   ⚠️  Đã hủy"
    exit 0
fi

echo ""
echo "   🚀 Starting crawler..."

nohup python3 auto_crawl_proxy.py \
  --json-file important_links.json \
  --follow-depth 50 \
  --concurrency 10 \
  --delay 0.3 \
  --max-retries 10 \
  --auto-pagination \
  > cache_important_full_depth50_concurrency10.log 2>&1 &

PID=$!
sleep 2

# Kiểm tra process có chạy không
if ps -p $PID > /dev/null; then
    echo "   ✅ Crawler đã bắt đầu!"
    echo "   PID: $PID"
    echo ""
else
    echo "   ❌ Crawler không khởi động được"
    echo "   Kiểm tra log: cat cache_important_full_depth50_concurrency10.log"
    echo ""
    exit 1
fi

# Bước 4: Hướng dẫn monitor
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                  ✅ CRAWL ĐÃ BẮT ĐẦU                       ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "📊 Monitor tiến trình:"
echo "   tail -f cache_important_full_depth50_concurrency10.log"
echo "   # hoặc"
echo "   watch -n 10 './check_progress.sh'"
echo ""
echo "🛑 Dừng crawl:"
echo "   pkill -f auto_crawl_proxy.py"
echo ""
echo "⏱️  Ước tính thời gian: 20-40 giờ"
echo "   (Với depth=50 và concurrency=10, sẽ crawl rất sâu và tìm nhiều links hơn)"
echo ""
echo "💡 Tip: Mở terminal mới để xem log realtime:"
echo "   tail -f cache_important_full_depth50_concurrency10.log"
echo ""

# Hiển thị vài dòng log đầu
sleep 3
echo "📝 Log preview (5 giây đầu):"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
tail -20 cache_important_full_depth50_concurrency10.log 2>/dev/null || echo "   (Đang khởi động...)"
echo ""

