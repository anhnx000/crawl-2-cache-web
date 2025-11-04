#!/usr/bin/env python3
"""
Verify which important links are already cached
"""

import json
import os
import hashlib

CACHE_DIR = "cache"

def cache_key(method: str, url: str) -> str:
    """Generate cache key (same as app.py)"""
    return hashlib.sha256(f"{method} {url}".encode("utf-8")).hexdigest()

def is_cached(url: str) -> bool:
    """Check if URL is cached"""
    method = "GET"
    key = cache_key(method, url)
    bin_path = os.path.join(CACHE_DIR, key + ".bin")
    meta_path = os.path.join(CACHE_DIR, key + ".json")
    return os.path.exists(bin_path) and os.path.exists(meta_path)

def main():
    print("=" * 80)
    print("VERIFY CACHED IMPORTANT LINKS")
    print("=" * 80)
    print()
    
    # Load important links
    print("📂 Loading important_links.json...")
    with open("important_links.json", "r", encoding="utf-8") as f:
        links = json.load(f)
    
    print(f"✅ Loaded {len(links)} important links")
    print()
    print("🔍 Checking cache status...")
    print()
    
    # Check each link
    cached = []
    not_cached = []
    
    for i, url in enumerate(links, 1):
        if is_cached(url):
            cached.append(url)
        else:
            not_cached.append(url)
        
        # Progress indicator
        if i % 1000 == 0 or i == len(links):
            print(f"  Checked {i}/{len(links)} links...", end="\r")
    
    print()  # New line after progress
    print()
    
    # Summary
    print("=" * 80)
    print("VERIFICATION RESULTS")
    print("=" * 80)
    print()
    print(f"✅ Cached:     {len(cached):>6} ({len(cached)*100//len(links):>3}%)")
    print(f"❌ Not cached: {len(not_cached):>6} ({len(not_cached)*100//len(links):>3}%)")
    print(f"📊 Total:      {len(links):>6}")
    print()
    
    # Save results
    if not_cached:
        output_file = "not_cached_links.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(not_cached, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Not cached links saved to: {output_file}")
        print()
        print("📝 First 10 not cached links:")
        for i, url in enumerate(not_cached[:10], 1):
            print(f"  {i}. {url}")
        
        if len(not_cached) > 10:
            print(f"  ... and {len(not_cached) - 10} more")
    else:
        print("🎉 All important links are already cached!")
    
    print()

if __name__ == "__main__":
    main()

