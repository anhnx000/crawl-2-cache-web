#!/usr/bin/env python3
"""
Script kiểm tra URLs nào trong full_urls_to_crawl.json đã được cache
"""

import json
import os
import hashlib
import argparse

CACHE_DIR = os.getenv("CACHE_DIR", "cache")

def cache_key(method: str, url: str) -> str:
    """Tạo cache key giống với app.py"""
    return hashlib.sha256(f"{method} {url}".encode("utf-8")).hexdigest()

def is_cached(url: str) -> bool:
    """Kiểm tra URL đã được cache chưa"""
    key = cache_key("GET", url)
    bin_path = os.path.join(CACHE_DIR, key + ".bin")
    meta_path = os.path.join(CACHE_DIR, key + ".json")
    return os.path.exists(bin_path) and os.path.exists(meta_path)

def main():
    ap = argparse.ArgumentParser(
        description="Kiểm tra URLs nào trong file JSON đã được cache"
    )
    ap.add_argument("json_file", nargs="?", default="full_urls_to_crawl.json",
                    help="Đường dẫn file JSON chứa URLs (mặc định: full_urls_to_crawl.json)")
    ap.add_argument("--output-cached", type=str, default="cached_urls.json",
                    help="File output cho URLs đã cache (mặc định: cached_urls.json)")
    ap.add_argument("--output-uncached", type=str, default="uncached_urls.json",
                    help="File output cho URLs chưa cache (mặc định: uncached_urls.json)")
    ap.add_argument("--show-cached", action="store_true",
                    help="Hiển thị danh sách URLs đã cache")
    ap.add_argument("--show-uncached", action="store_true",
                    help="Hiển thị danh sách URLs chưa cache")
    ap.add_argument("--limit", type=int, default=10,
                    help="Số lượng URLs hiển thị (mặc định: 10)")
    args = ap.parse_args()
    
    # Đọc file JSON
    print(f"📖 Đang đọc file: {args.json_file}")
    try:
        with open(args.json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"❌ Không tìm thấy file: {args.json_file}")
        return
    except json.JSONDecodeError as e:
        print(f"❌ Lỗi parse JSON: {e}")
        return
    
    # Extract URLs
    urls_data = []
    if isinstance(data, dict):
        if 'urls' in data:
            urls_data = data['urls']
        elif 'url' in data:
            urls_data = [data]
    elif isinstance(data, list):
        urls_data = data
    
    total = len(urls_data)
    print(f"✅ Đã load {total} URLs\n")
    
    if total == 0:
        print("⚠️  Không có URLs nào trong file")
        return
    
    # Kiểm tra cache
    print("🔍 Đang kiểm tra cache...")
    cached_urls = []
    uncached_urls = []
    
    for i, item in enumerate(urls_data, 1):
        url = item.get("url") if isinstance(item, dict) else item
        if url:
            if is_cached(url):
                cached_urls.append(item)
            else:
                uncached_urls.append(item)
        
        # Progress
        if i % 1000 == 0:
            print(f"   Đã kiểm tra: {i}/{total} URLs...")
    
    # Thống kê
    print(f"\n{'='*60}")
    print(f"📊 Thống kê:")
    print(f"   - Tổng URLs: {total}")
    print(f"   - Đã cache: {len(cached_urls)} ({len(cached_urls)*100//total if total > 0 else 0}%)")
    print(f"   - Chưa cache: {len(uncached_urls)} ({len(uncached_urls)*100//total if total > 0 else 0}%)")
    print(f"{'='*60}\n")
    
    # Hiển thị URLs đã cache
    if cached_urls and args.show_cached:
        print(f"✅ URLs đã cache ({min(args.limit, len(cached_urls))} đầu tiên):")
        for item in cached_urls[:args.limit]:
            url = item.get("url") if isinstance(item, dict) else item
            print(f"   {url}")
        if len(cached_urls) > args.limit:
            print(f"   ... và {len(cached_urls) - args.limit} URLs khác")
        print()
    
    # Hiển thị URLs chưa cache
    if uncached_urls and args.show_uncached:
        print(f"⚠️  URLs chưa cache ({min(args.limit, len(uncached_urls))} đầu tiên):")
        for item in uncached_urls[:args.limit]:
            url = item.get("url") if isinstance(item, dict) else item
            print(f"   {url}")
        if len(uncached_urls) > args.limit:
            print(f"   ... và {len(uncached_urls) - args.limit} URLs khác")
        print()
    
    # Lưu danh sách URLs đã cache
    if cached_urls:
        with open(args.output_cached, "w", encoding="utf-8") as f:
            json.dump({
                "total_urls": len(cached_urls),
                "description": f"URLs đã cache từ {args.json_file}",
                "urls": cached_urls
            }, f, ensure_ascii=False, indent=2)
        print(f"💾 Đã lưu {len(cached_urls)} URLs đã cache vào: {args.output_cached}")
    
    # Lưu danh sách URLs chưa cache
    if uncached_urls:
        with open(args.output_uncached, "w", encoding="utf-8") as f:
            json.dump({
                "total_urls": len(uncached_urls),
                "description": f"URLs chưa cache từ {args.json_file}",
                "urls": uncached_urls
            }, f, ensure_ascii=False, indent=2)
        print(f"💾 Đã lưu {len(uncached_urls)} URLs chưa cache vào: {args.output_uncached}")
    
    # Gợi ý crawl URLs chưa cache
    if uncached_urls:
        print(f"\n💡 Để crawl {len(uncached_urls)} URLs chưa cache:")
        print(f"   python crawl_from_json.py {args.output_uncached} --follow-depth 2 --concurrency 4 --delay 0.5")

if __name__ == "__main__":
    main()


