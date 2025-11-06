#!/bin/bash
# Test offline viewer tại port 5003

echo "╔════════════════════════════════════════════════════════════╗"
echo "║       🧪 Test Offline Viewer - Port 5003                   ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

PROXY="http://localhost:5003"

# Kiểm tra proxy có chạy không
echo "1. Checking if proxy is running..."
if curl -s -o /dev/null -w "%{http_code}" "${PROXY}/_cache_stats" | grep -q "200"; then
    echo "   ✅ Proxy is running at ${PROXY}"
    echo ""
    
    # Lấy stats
    echo "2. Cache statistics:"
    curl -s "${PROXY}/_cache_stats" | python3 -m json.tool
    echo ""
    
    # So sánh với port 5002 (nếu có)
    if curl -s -o /dev/null -w "%{http_code}" "http://localhost:5002/_cache_stats" | grep -q "200"; then
        echo "3. Comparison with port 5002 (crawl process):"
        echo "   Port 5002 stats:"
        curl -s "http://localhost:5002/_cache_stats" | python3 -m json.tool 2>/dev/null | head -5
        echo ""
    fi
else
    echo "   ❌ Proxy is NOT running!"
    echo ""
    echo "   Start proxy first:"
    echo "   ./start_offline_viewer.sh"
    echo ""
    exit 1
fi

# Test một vài URLs đã cache
echo "4. Testing cached URLs..."
echo ""

TEST_URLS=(
    "/?mode=ETM"
    "/?mode=ETM&marke=KM"
    "/?mode=ETM&marke=KM&year=2026"
)

for url in "${TEST_URLS[@]}"; do
    echo -n "   Testing: ${url}..."
    status=$(curl -s -o /dev/null -w "%{http_code}" "${PROXY}${url}")
    
    if [ "$status" = "200" ]; then
        echo " ✅ OK (200)"
    elif [ "$status" = "404" ]; then
        echo " ❌ Not cached (404)"
    else
        echo " ⚠️  Status: $status"
    fi
done

echo ""
echo "════════════════════════════════════════════════════════════"
echo "💡 Tips:"
echo "   Open browser: ${PROXY}"
echo "   Try URL: ${PROXY}/?mode=ETM&marke=KM"
echo ""
echo "📊 Compare:"
echo "   Port 5002: Crawl process (online mode, can fetch)"
echo "   Port 5003: Offline viewer (read-only, cache only)"
echo ""
echo "✅ Verify:"
echo "   - Port 5003 does NOT affect crawl at port 5002"
echo "   - Both ports share the same cache directory"
echo "   - Port 5003 URLs are rewritten to port 5003"
echo "════════════════════════════════════════════════════════════"

