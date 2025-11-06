#!/usr/bin/env python3
"""
Extract tất cả links có docId và page từ một URL bất kỳ
và append vào important_links.json, đồng thời tự động cache các URLs tìm được
"""

import asyncio
import os
import json
import sys
import re
import argparse
from urllib.parse import urlparse, urljoin, urlencode, parse_qs
import httpx
from bs4 import BeautifulSoup

# ================== CONFIG ==================
PROXY_BASE = os.getenv("LOCAL_BASE", "http://localhost:5002")
ORIGIN = os.getenv("ORIGIN", "https://kiagds.ru")
CACHE_DIR = os.getenv("CACHE_DIR", "cache")
IMPORTANT_LINKS_FILE = "important_links.json"
UA = "ExtractDocIdLinks/1.0 (+respectful; via-proxy)"
os.makedirs(CACHE_DIR, exist_ok=True)
# ============================================

def normalize_url(url: str) -> str:
    """Chuẩn hóa URL: loại bỏ fragment, chuẩn hóa và xử lý parameters rỗng"""
    try:
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        
        if parsed.query:
            params = parse_qs(parsed.query, keep_blank_values=False)
            cleaned_params = {}
            for key, values in params.items():
                non_empty_values = [v for v in values if v and v.strip()]
                if non_empty_values:
                    cleaned_params[key] = non_empty_values[0] if len(non_empty_values) == 1 else non_empty_values
            
            if 'page' in cleaned_params:
                page_val = cleaned_params['page']
                if isinstance(page_val, str) and (not page_val or page_val.strip() == ''):
                    del cleaned_params['page']
                elif isinstance(page_val, list) and all(not v or v.strip() == '' for v in page_val):
                    del cleaned_params['page']
            
            if cleaned_params:
                normalized = f"{base_url}?{urlencode(cleaned_params, doseq=True)}"
            else:
                normalized = base_url
        else:
            normalized = base_url
        
        return normalized
    except Exception:
        url_no_fragment = url.split('#')[0]
        url_cleaned = url_no_fragment.rstrip('=&?')
        if url_cleaned.endswith('&page') or url_cleaned.endswith('?page'):
            url_cleaned = url_cleaned[:-5]
        return url_cleaned.rstrip('&?')

def in_domain(u: str) -> bool:
    """Kiểm tra URL có thuộc domain kiagds.ru không"""
    try:
        parsed = urlparse(u)
        netloc = parsed.netloc.lower().split(":")[0]
        return netloc.endswith("kiagds.ru")
    except Exception:
        return False

def has_docid_and_page(url: str) -> bool:
    """Kiểm tra URL có chứa docId và page không"""
    try:
        parsed = urlparse(url)
        query = parsed.query
        return 'docId=' in query and 'page=' in query
    except Exception:
        return False

def extract_docid_page_links(base_url: str, html: str) -> set:
    """
    Extract tất cả links có docId và page từ HTML
    """
    soup = BeautifulSoup(html, "html.parser")
    urls = set()
    
    # Extract từ các thẻ HTML (a, link, etc.)
    for tag, attr in (
        ("a", "href"), 
        ("link", "href"), 
        ("form", "action")
    ):
        for el in soup.find_all(tag):
            href = el.get(attr)
            if not href:
                continue
            try:
                u = urljoin(base_url, href)
                if in_domain(u):
                    u = normalize_url(u)
                    if has_docid_and_page(u):
                        urls.add(u)
            except Exception:
                continue
    
    # Extract từ JavaScript (tìm các URL trong JS)
    for script in soup.find_all("script"):
        if script.string:
            # Tìm các URL kiagds.ru có docId và page
            js_urls = re.findall(r'https?://kiagds\.ru[^\s"\'<>)]+', script.string)
            for u in js_urls:
                try:
                    u = normalize_url(u)
                    if in_domain(u) and has_docid_and_page(u):
                        urls.add(u)
                except Exception:
                    continue
    
    # Extract từ các thuộc tính data-* và onclick handlers
    try:
        for el in soup.find_all():
            try:
                if not hasattr(el, 'attrs') or not el.attrs:
                    continue
                attrs = el.attrs
                if not isinstance(attrs, dict):
                    continue
                
                for attr_name, attr_value in attrs.items():
                    if not isinstance(attr_value, str):
                        continue
                    
                    # Extract từ data-* attributes
                    if attr_name.startswith('data-') and 'kiagds.ru' in attr_value:
                        js_urls = re.findall(r'https?://kiagds\.ru[^\s"\'<>)]+', attr_value)
                        for u in js_urls:
                            try:
                                u = normalize_url(u)
                                if in_domain(u) and has_docid_and_page(u):
                                    urls.add(u)
                            except Exception:
                                continue
                    
                    # Extract từ onclick handlers
                    if attr_name == 'onclick' and ('docId=' in attr_value or 'kiagds.ru' in attr_value):
                        # Tìm ajaxHref('...') hoặc các hàm tương tự
                        onclick_urls = re.findall(r"(?:ajaxHref|location\.href|window\.location)\s*[=\(]\s*['\"]([^'\"]+)['\"]", attr_value)
                        for match in onclick_urls:
                            try:
                                if match.startswith('?'):
                                    u = urljoin(base_url, match)
                                elif match.startswith('/'):
                                    u = urljoin(base_url, match)
                                elif 'kiagds.ru' in match:
                                    u = match
                                else:
                                    u = urljoin(base_url, match)
                                
                                u = normalize_url(u)
                                if in_domain(u) and has_docid_and_page(u):
                                    urls.add(u)
                            except Exception:
                                continue
                        
                        # Tìm URL pattern trực tiếp trong onclick
                        direct_urls = re.findall(r'https?://kiagds\.ru[^\s"\'<>)]+', attr_value)
                        for u in direct_urls:
                            try:
                                u = normalize_url(u)
                                if in_domain(u) and has_docid_and_page(u):
                                    urls.add(u)
                            except Exception:
                                continue
                    
                    # Extract từ các attribute khác có chứa docId và page
                    if 'docId=' in attr_value and 'page=' in attr_value:
                        # Tìm các query string pattern với docId và page
                        query_urls = re.findall(r'\?mode=[^\s"\'<>)]+docId=\d+[^\s"\'<>)]*page=\d+', attr_value)
                        for qs in query_urls:
                            try:
                                u = urljoin(base_url, qs)
                                u = normalize_url(u)
                                if in_domain(u) and has_docid_and_page(u):
                                    urls.add(u)
                            except Exception:
                                continue
                        
                        # Tìm các URL đầy đủ
                        full_urls = re.findall(r'https?://kiagds\.ru[^\s"\'<>)]+', attr_value)
                        for u in full_urls:
                            try:
                                u = normalize_url(u)
                                if in_domain(u) and has_docid_and_page(u):
                                    urls.add(u)
                            except Exception:
                                continue
                                
            except (AttributeError, TypeError, ValueError):
                continue
    except Exception:
        pass
    
    return urls

async def fetch_via_proxy(client: httpx.AsyncClient, url: str, proxy_base: str):
    """Fetch URL qua proxy"""
    proxy_url = url.replace(ORIGIN, proxy_base)
    
    try:
        r = await client.get(
            proxy_url, 
            headers={"User-Agent": UA, "Accept-Encoding": "identity"}, 
            timeout=30.0,
            follow_redirects=True
        )
        return r
    except httpx.ConnectError as e:
        error_msg = f"Không thể kết nối tới proxy {proxy_base}. Hãy đảm bảo proxy đang chạy!"
        print(f"[CONNECTION_ERROR] {url}: {error_msg}")
        raise Exception(error_msg) from e
    except httpx.HTTPError as e:
        print(f"[HTTP_ERROR] {url}: {e}")
        raise
    except Exception as e:
        print(f"[ERROR] {url}: {e}")
        raise

async def cache_urls(urls: list, proxy_base: str, concurrency: int = 10):
    """
    Tự động cache các URLs tìm được
    """
    if not urls:
        return
    
    print(f"\n📦 Bắt đầu cache {len(urls)} URLs...")
    
    async with httpx.AsyncClient() as client:
        sem = asyncio.Semaphore(concurrency)
        cached_count = 0
        error_count = 0
        
        async def cache_one(url):
            nonlocal cached_count, error_count
            async with sem:
                try:
                    r = await fetch_via_proxy(client, url, proxy_base)
                    if r.status_code == 200:
                        cached_count += 1
                        if cached_count % 10 == 0:
                            print(f"  ✅ Đã cache {cached_count}/{len(urls)} URLs...")
                    else:
                        error_count += 1
                        print(f"  ⚠️  [{r.status_code}] {url}")
                except Exception as e:
                    error_count += 1
                    print(f"  ❌ Lỗi khi cache {url}: {e}")
                await asyncio.sleep(0.3)  # Delay giữa các requests
        
        tasks = [cache_one(url) for url in urls]
        await asyncio.gather(*tasks)
        
        print(f"\n✅ Hoàn thành cache:")
        print(f"   - Thành công: {cached_count} URLs")
        print(f"   - Lỗi: {error_count} URLs")

def load_important_links() -> list:
    """Load danh sách URLs từ important_links.json"""
    if not os.path.exists(IMPORTANT_LINKS_FILE):
        return []
    
    try:
        with open(IMPORTANT_LINKS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and 'urls' in data:
            return [item.get('url') if isinstance(item, dict) else item for item in data['urls']]
        
        return []
    except Exception as e:
        print(f"⚠️  Lỗi khi đọc {IMPORTANT_LINKS_FILE}: {e}")
        return []

def save_important_links(urls: list):
    """Lưu danh sách URLs vào important_links.json"""
    try:
        # Lưu dạng list đơn giản
        with open(IMPORTANT_LINKS_FILE, 'w', encoding='utf-8') as f:
            json.dump(urls, f, ensure_ascii=False, indent=2)
        print(f"✅ Đã lưu {len(urls)} URLs vào {IMPORTANT_LINKS_FILE}")
    except Exception as e:
        print(f"❌ Lỗi khi lưu {IMPORTANT_LINKS_FILE}: {e}")
        raise

async def extract_and_save(url: str, proxy_base: str, auto_cache: bool = True, cache_concurrency: int = 10):
    """
    Extract docId và page links từ URL và append vào important_links.json
    """
    print(f"🔍 Đang extract links từ: {url}")
    print(f"   Proxy: {proxy_base}")
    print(f"   Auto cache: {auto_cache}")
    print("")
    
    # Fetch HTML qua proxy
    async with httpx.AsyncClient() as client:
        try:
            print("📥 Đang fetch HTML...")
            r = await fetch_via_proxy(client, url, proxy_base)
            
            if r.status_code != 200:
                print(f"❌ Không thể fetch URL: HTTP {r.status_code}")
                return
            
            # Decode HTML
            ctype = r.headers.get("Content-Type", "").lower()
            enc = re.search(r"charset=([^;]+)", ctype, flags=re.I)
            enc = enc.group(1).strip() if enc else "utf-8"
            
            try:
                html = r.content.decode(enc, errors="replace")
            except Exception:
                html = r.text
            
            print(f"✅ Đã fetch HTML ({len(html)} chars)")
            print("")
            
        except Exception as e:
            print(f"❌ Lỗi khi fetch URL: {e}")
            return
    
    # Extract links có docId và page
    print("🔍 Đang extract links có docId và page...")
    extracted_urls = extract_docid_page_links(url, html)
    
    if not extracted_urls:
        print("⚠️  Không tìm thấy links nào có docId và page")
        return
    
    print(f"✅ Tìm thấy {len(extracted_urls)} links có docId và page")
    print("")
    
    # Load existing URLs
    existing_urls = set(load_important_links())
    
    # Filter URLs mới (chưa có trong important_links.json)
    new_urls = []
    for u in extracted_urls:
        if u not in existing_urls:
            new_urls.append(u)
            existing_urls.add(u)
    
    if not new_urls:
        print("ℹ️  Tất cả links đã có trong important_links.json")
        return
    
    print(f"📝 Tìm thấy {len(new_urls)} links mới")
    print("")
    
    # Hiển thị một vài ví dụ
    print("📋 Ví dụ các links mới:")
    for i, u in enumerate(list(new_urls)[:5], 1):
        print(f"   {i}. {u}")
    if len(new_urls) > 5:
        print(f"   ... và {len(new_urls) - 5} links khác")
    print("")
    
    # Append vào important_links.json
    all_urls = list(existing_urls)
    all_urls.extend(new_urls)
    all_urls.sort()  # Sắp xếp để dễ đọc
    
    save_important_links(all_urls)
    
    # Tự động cache các URLs mới
    if auto_cache:
        await cache_urls(new_urls, proxy_base, cache_concurrency)
    
    print(f"\n{'='*60}")
    print(f"✅ Hoàn thành!")
    print(f"   - Tổng URLs trong {IMPORTANT_LINKS_FILE}: {len(all_urls)}")
    print(f"   - URLs mới thêm: {len(new_urls)}")
    print(f"{'='*60}")

def main():
    parser = argparse.ArgumentParser(
        description="Extract docId và page links từ URL và append vào important_links.json"
    )
    parser.add_argument("url", type=str, help="URL để extract links (ví dụ: https://kiagds.ru/?mode=ETM&marke=KM&year=2024&model=8353&mkb=129__25552&docId=434175&page=4)")
    parser.add_argument("--proxy-base", type=str, default=PROXY_BASE, 
                        help=f"Proxy base URL (mặc định: {PROXY_BASE})")
    parser.add_argument("--no-cache", action="store_true", 
                        help="Không tự động cache các URLs tìm được")
    parser.add_argument("--cache-concurrency", type=int, default=10,
                        help="Số lượng requests đồng thời khi cache (mặc định: 10)")
    
    args = parser.parse_args()
    
    # Normalize URL
    url = normalize_url(args.url)
    
    if not in_domain(url):
        print(f"❌ URL không thuộc domain kiagds.ru: {url}")
        sys.exit(1)
    
    # Chạy async
    asyncio.run(extract_and_save(
        url, 
        args.proxy_base, 
        auto_cache=not args.no_cache,
        cache_concurrency=args.cache_concurrency
    ))

if __name__ == "__main__":
    main()

