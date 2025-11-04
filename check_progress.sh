#!/bin/bash
# Quick progress check script

LOG_FILE="cache_important_auto.log"

echo "=================================="
echo "AUTO CRAWL PROGRESS CHECK"
echo "=================================="
echo ""

# Check if process is running
if pgrep -f "auto_crawl_proxy.py" > /dev/null; then
    echo "✅ Process is RUNNING"
    PID=$(pgrep -f "auto_crawl_proxy.py")
    echo "   PID: $PID"
else
    echo "❌ Process is NOT running"
fi

echo ""

# Parse log file
if [ -f "$LOG_FILE" ]; then
    TOTAL_LINES=$(wc -l < "$LOG_FILE")
    SUCCESS=$(grep -c "✅ \[200\]" "$LOG_FILE" || echo 0)
    ERRORS=$(grep -cE "(⚠️|❌) \[" "$LOG_FILE" || echo 0)
    
    echo "📊 Statistics from log:"
    echo "   Total log lines: $TOTAL_LINES"
    echo "   ✅ Success (200): $SUCCESS"
    echo "   ❌ Errors: $ERRORS"
    echo ""
    
    # Show last 5 processed URLs
    echo "📝 Last 5 processed URLs:"
    grep -E "(✅|⚠️|❌) \[" "$LOG_FILE" | tail -5 | sed 's/^/   /'
    echo ""
else
    echo "⚠️  Log file not found: $LOG_FILE"
    echo ""
fi

# Cache directory stats
if [ -d "cache" ]; then
    CACHE_COUNT=$(find cache -name "*.bin" | wc -l)
    echo "💾 Cache directory:"
    echo "   Total cached files: $CACHE_COUNT"
else
    echo "⚠️  Cache directory not found"
fi

echo ""
echo "=================================="
echo "To watch in real-time, run:"
echo "  tail -f $LOG_FILE"
echo "=================================="

