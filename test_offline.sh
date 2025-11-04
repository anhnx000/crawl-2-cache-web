#!/bin/bash
# Test xem proxy offline có hoạt động không với các URLs đã cache

PROXY="http://localhost:5002"

echo "=========================================="
echo "🧪 Testing Offline Proxy"
echo "=========================================="
echo ""

# Kiểm tra proxy có đang chạy không
echo "1. Checking if proxy is running..."
if curl -s -o /dev/null -w "%{http_code}" "${PROXY}/_cache_stats" | grep -q "200"; then
    echo "   ✅ Proxy is running at ${PROXY}"
    echo ""
    
    # Lấy stats
    echo "2. Cache statistics:"
    curl -s "${PROXY}/_cache_stats" | python3 -m json.tool
    echo ""
else
    echo "   ❌ Proxy is NOT running!"
    echo ""
    echo "   Start proxy first:"
    echo "   ./start_offline.sh   (offline mode)"
    echo "   ./start_online.sh    (online mode)"
    echo ""
    exit 1
fi

# Test một vài URLs đã cache
echo "3. Testing cached URLs..."
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
echo "=========================================="
echo "💡 Tip:"
echo "   Open browser: ${PROXY}"
echo "   Try URL: ${PROXY}/?mode=ETM&marke=KM"
echo "=========================================="

