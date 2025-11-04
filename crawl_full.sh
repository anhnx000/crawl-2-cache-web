#!/bin/bash
# Cache FULL toàn bộ important_links.json (16,304 URLs)

cd /home/xuananh/work_1/anhnx/crawl-2

echo "=========================================="
echo "Cache FULL important_links.json"
echo "=========================================="
echo "Total URLs: 16,304"
echo "Log file: cache_important_full.log"
echo ""
echo "Bắt đầu crawl trong background..."
echo ""

nohup python3 auto_crawl_proxy.py \
  --json-file important_links.json \
  --follow-depth 8 \
  --concurrency 18 \
  --delay 0.3 \
  --max-retries 10 \
  --auto-pagination \
  > cache_important_full.log 2>&1 &

PID=$!
echo "✅ Process đã bắt đầu!"
echo "   PID: $PID"
echo ""
echo "📊 Theo dõi tiến trình:"
echo "   ./check_progress.sh"
echo ""
echo "📝 Xem log realtime:"
echo "   tail -f cache_important_full.log"
echo ""
echo "🛑 Dừng crawl:"
echo "   pkill -f auto_crawl_proxy.py"
echo ""

