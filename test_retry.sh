#!/bin/bash
# Script để test retry feature

echo "============================================"
echo "Test Retry Feature - auto_crawl_proxy.py"
echo "============================================"
echo ""

# Kiểm tra proxy có đang chạy không
echo "🔍 Checking proxy status..."
if curl -s http://localhost:5002/_cache_stats > /dev/null 2>&1; then
    echo "✅ Proxy is running"
    STATS=$(curl -s http://localhost:5002/_cache_stats)
    echo "   $STATS"
else
    echo "❌ Proxy is not running!"
    echo ""
    echo "Please start proxy first:"
    echo "  export LIVE_FALLBACK=true"
    echo "  conda activate crawl"
    echo "  python app.py"
    exit 1
fi

echo ""
echo "============================================"
echo "Test 1: Crawl page 13 (missing from cache)"
echo "============================================"
echo ""

# Test với 3 retries cho nhanh
conda run -n crawl python auto_crawl_proxy.py \
  --extra-urls "https://kiagds.ru/?mode=ETM&marke=KM&year=2026&model=9193&mkb=447__29696&docId=435571&page=13" \
  --follow-depth 0 \
  --max-retries 3 \
  --verbose

echo ""
echo "============================================"
echo "Verify cache status"
echo "============================================"
echo ""

# Kiểm tra page 13 đã được cache chưa
python3 -c "
import hashlib, os, json
url = 'https://kiagds.ru/?mode=ETM&marke=KM&year=2026&model=9193&mkb=447__29696&docId=435571&page=13'
key = hashlib.sha256(f'GET {url}'.encode('utf-8')).hexdigest()
bin_path = f'cache/{key}.bin'
meta_path = f'cache/{key}.json'

if os.path.exists(bin_path) and os.path.exists(meta_path):
    print('✅ Page 13 is NOW cached!')
    with open(meta_path, 'r') as f:
        meta = json.load(f)
    print(f'   Status: {meta.get(\"status\")}')
    print(f'   URL: {meta.get(\"url\")}')
else:
    print('❌ Page 13 is still NOT cached')
    print('   This may be because:')
    print('   - Proxy is running in offline mode (LIVE_FALLBACK=false)')
    print('   - Network error')
    print('   - Server returned error')
"

echo ""
echo "============================================"
echo "Test completed!"
echo "============================================"


