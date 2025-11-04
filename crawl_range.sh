#!/bin/bash
# Cache một khoảng URLs cụ thể từ important_links.json

if [ $# -lt 2 ]; then
    echo "Usage: $0 <start_index> <end_index>"
    echo ""
    echo "Example:"
    echo "  $0 0 100      # Cache URLs từ 0 đến 100"
    echo "  $0 1000 2000  # Cache URLs từ 1000 đến 2000"
    echo ""
    exit 1
fi

START=$1
END=$2

cd /home/xuananh/work_1/anhnx/crawl-2

echo "=========================================="
echo "Cache URLs từ $START đến $END"
echo "=========================================="
echo "Total URLs: $((END - START))"
echo "Log file: cache_range_${START}_${END}.log"
echo ""

nohup python3 auto_crawl_proxy.py \
  --json-file important_links.json \
  --json-start-index $START \
  --json-end-index $END \
  --follow-depth 3 \
  --concurrency 5 \
  --delay 0.3 \
  --max-retries 10 \
  --auto-pagination \
  > cache_range_${START}_${END}.log 2>&1 &

PID=$!
echo "✅ Process đã bắt đầu!"
echo "   PID: $PID"
echo ""
echo "📝 Xem log:"
echo "   tail -f cache_range_${START}_${END}.log"
echo ""

