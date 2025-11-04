#!/usr/bin/env python3
"""
Monitor tiến trình auto_crawl_proxy.py thời gian thực
"""

import os
import time
import re
from datetime import datetime, timedelta
from collections import defaultdict

LOG_FILE = "cache_important_auto.log"
CACHE_DIR = "cache"

def count_cache_files():
    """Đếm số file cache"""
    try:
        return len([f for f in os.listdir(CACHE_DIR) if f.endswith(".bin")])
    except Exception:
        return 0

def parse_log_stats(log_file):
    """Parse log để lấy thống kê"""
    stats = {
        "total_processed": 0,
        "success": 0,
        "errors": 0,
        "by_status": defaultdict(int),
        "recent_urls": [],
        "error_urls": []
    }
    
    if not os.path.exists(log_file):
        return stats
    
    try:
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        # Parse từng dòng
        for line in lines:
            # Match pattern: ✅ [200] URL (depth=X)
            match = re.search(r'([✅⚠️❌])\s*\[(\d+)\]\s*(https?://[^\s]+)\s*\(depth=(\d+)\)', line)
            if match:
                icon, status, url, depth = match.groups()
                status = int(status)
                
                stats["total_processed"] += 1
                stats["by_status"][status] += 1
                
                if status == 200:
                    stats["success"] += 1
                else:
                    stats["errors"] += 1
                    if len(stats["error_urls"]) < 10:
                        stats["error_urls"].append((status, url))
                
                # Giữ 10 URLs gần nhất
                stats["recent_urls"].append(url)
                if len(stats["recent_urls"]) > 10:
                    stats["recent_urls"].pop(0)
        
        # Tìm dòng hoàn thành cuối cùng
        for line in reversed(lines):
            if "Hoàn thành crawl" in line or "Mới crawl:" in line:
                # Parse: - Mới crawl: 123 URLs
                match = re.search(r'Mới crawl:\s*(\d+)\s*URLs', line)
                if match:
                    stats["crawled_new"] = int(match.group(1))
                
                # Parse: - Đã cache sẵn: 123 URLs
                match = re.search(r'Đã cache sẵn:\s*(\d+)\s*URLs', line)
                if match:
                    stats["already_cached"] = int(match.group(1))
                
                break
    
    except Exception as e:
        print(f"Lỗi khi parse log: {e}")
    
    return stats

def format_duration(seconds):
    """Format duration thành giờ:phút:giây"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"

def main():
    print("=" * 80)
    print("AUTO CRAWL PROGRESS MONITOR")
    print("=" * 80)
    print()
    
    start_time = time.time()
    last_processed = 0
    
    while True:
        try:
            # Parse log
            stats = parse_log_stats(LOG_FILE)
            cache_files = count_cache_files()
            current_time = time.time()
            elapsed = current_time - start_time
            
            # Tính tốc độ
            processed_delta = stats["total_processed"] - last_processed
            rate = processed_delta / 10 if elapsed >= 10 else 0  # URLs/second
            last_processed = stats["total_processed"]
            
            # Clear screen
            os.system('clear' if os.name != 'nt' else 'cls')
            
            print("=" * 80)
            print("AUTO CRAWL PROGRESS MONITOR")
            print("=" * 80)
            print(f"\n⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"⏱️  Running for: {format_duration(elapsed)}")
            print()
            
            print(f"📊 Processing Statistics:")
            print(f"   Total processed:  {stats['total_processed']:,} URLs")
            print(f"   ✅ Success (200): {stats['success']:,} ({stats['success']*100//max(stats['total_processed'],1):>3}%)")
            print(f"   ❌ Errors:        {stats['errors']:,} ({stats['errors']*100//max(stats['total_processed'],1):>3}%)")
            print()
            
            # Status codes breakdown
            if stats['by_status']:
                print(f"📈 By Status Code:")
                for status_code in sorted(stats['by_status'].keys()):
                    count = stats['by_status'][status_code]
                    icon = "✅" if status_code == 200 else "⚠️"
                    print(f"   {icon} {status_code}: {count:,}")
                print()
            
            print(f"💾 Cache Directory:")
            print(f"   Total cache files: {cache_files:,}")
            print()
            
            print(f"🚀 Performance:")
            if rate > 0:
                print(f"   Current rate: ~{rate:.2f} URLs/sec (~{rate*60:.1f} URLs/min)")
                if stats['total_processed'] > 0:
                    avg_rate = stats['total_processed'] / elapsed
                    print(f"   Average rate: ~{avg_rate:.2f} URLs/sec (~{avg_rate*60:.1f} URLs/min)")
            else:
                print(f"   Calculating rate...")
            print()
            
            # Recent URLs
            if stats['recent_urls']:
                print(f"📝 Recent URLs (last 5):")
                for url in stats['recent_urls'][-5:]:
                    # Shorten URL for display
                    if len(url) > 70:
                        url_display = url[:67] + "..."
                    else:
                        url_display = url
                    print(f"   - {url_display}")
                print()
            
            # Errors
            if stats['error_urls']:
                print(f"⚠️  Recent Errors:")
                for status, url in stats['error_urls'][-5:]:
                    url_display = url[:65] + "..." if len(url) > 65 else url
                    print(f"   [{status}] {url_display}")
                print()
            
            print("=" * 80)
            print("Press Ctrl+C to exit monitor (crawling will continue in background)")
            print(f"Log file: {LOG_FILE}")
            print()
            
            # Wait
            time.sleep(10)
            
        except KeyboardInterrupt:
            print("\n\n✋ Monitor stopped")
            print(f"📊 Final stats: {stats['total_processed']} URLs processed")
            print(f"⏱️  Total time: {format_duration(time.time() - start_time)}")
            break
        except Exception as e:
            print(f"\n❌ Error in monitor: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()

