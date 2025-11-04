#!/bin/bash
# Demo offline mode - Hướng dẫn từng bước

echo "╔════════════════════════════════════════════════════════════╗"
echo "║       🔌 DEMO OFFLINE MODE - Hướng dẫn từng bước          ║"
echo "╔════════════════════════════════════════════════════════════╗"
echo ""

cd /home/xuananh/work_1/anhnx/crawl-2

echo "📊 Step 1: Kiểm tra cache hiện tại"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
CACHE_COUNT=$(find cache -name "*.bin" 2>/dev/null | wc -l)
echo "   Cached responses: $CACHE_COUNT files"
echo ""

if [ $CACHE_COUNT -lt 100 ]; then
    echo "   ⚠️  Warning: Số lượng cache ít (< 100 files)"
    echo "   💡 Khuyến nghị: Chạy ./crawl_full.sh trước để cache đầy đủ"
    echo ""
fi

echo "🔍 Step 2: Kiểm tra important links đã cache"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ -f "important_links.json" ]; then
    echo "   Running: python3 verify_cached_links.py"
    python3 verify_cached_links.py 2>/dev/null | grep -E "(Cached:|Not cached:|Total:)" | sed 's/^/   /'
else
    echo "   ⚠️  File important_links.json not found"
fi
echo ""

echo "🚀 Step 3: Chạy proxy ở chế độ OFFLINE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "   Mở terminal mới và chạy:"
echo ""
echo "   cd /home/xuananh/work_1/anhnx/crawl-2"
echo "   ./start_offline.sh"
echo ""
echo "   (Giữ terminal đó chạy)"
echo ""
read -p "   Nhấn ENTER khi đã chạy proxy offline... " dummy
echo ""

echo "🧪 Step 4: Test proxy offline"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
./test_offline.sh
echo ""

echo "🌐 Step 5: Browse trong browser"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "   Mở browser và truy cập:"
echo ""
echo "   🔗 http://localhost:5002"
echo ""
echo "   Hoặc thử các URLs sau:"
echo "   • http://localhost:5002/?mode=ETM"
echo "   • http://localhost:5002/?mode=ETM&marke=KM"
echo "   • http://localhost:5002/?mode=ETM&marke=KM&year=2026"
echo ""

read -p "   Nhấn ENTER để mở browser tự động (nếu có xdg-open)... " dummy

# Try to open browser
if command -v xdg-open > /dev/null; then
    echo "   🌐 Opening browser..."
    xdg-open "http://localhost:5002/?mode=ETM&marke=KM" 2>/dev/null &
elif command -v open > /dev/null; then
    echo "   🌐 Opening browser..."
    open "http://localhost:5002/?mode=ETM&marke=KM" 2>/dev/null &
else
    echo "   ℹ️  Vui lòng mở browser thủ công"
fi

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                    ✅ DEMO HOÀN TẤT                        ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "📚 Tài liệu chi tiết:"
echo "   cat OFFLINE_MODE.md"
echo ""
echo "🛑 Dừng proxy:"
echo "   Nhấn Ctrl+C ở terminal đang chạy proxy"
echo ""
echo "💡 Tips:"
echo "   • Chạy ./start_offline.sh để chỉ dùng cache"
echo "   • Chạy ./start_online.sh để cache + fetch từ internet"
echo "   • Chạy ./check_progress.sh để xem tiến trình crawl"
echo ""

