#!/usr/bin/env python3
"""
Auto crawler qua proxy để cache toàn bộ trang web
Tự động extract và crawl các links trong HTML
"""

import asyncio
import os
import json
import sys
import hashlib
import argparse
import re
from typing import Set
from urllib.parse import urlparse, urljoin, urlencode, parse_qs
import httpx
from bs4 import BeautifulSoup

# ================== CONFIG ==================
PROXY_BASE = os.getenv("LOCAL_BASE", "http://localhost:5002")  # Proxy đang chạy
ORIGIN = os.getenv("ORIGIN", "https://kiagds.ru")
CACHE_DIR = os.getenv("CACHE_DIR", "cache")
IMPORTANT_LINKS_FILE = "important_links.json"
UA = "AutoCrawler/1.0 (+respectful; via-proxy)"
os.makedirs(CACHE_DIR, exist_ok=True)
# ============================================

def cache_key(method: str, url: str) -> str:
    """Tạo cache key giống với app.py"""
    return hashlib.sha256(f"{method} {url}".encode("utf-8")).hexdigest()

def cache_paths(method: str, url: str):
    """Tạo đường dẫn cache file giống với app.py"""
    key = cache_key(method, url)
    return os.path.join(CACHE_DIR, key + ".bin"), os.path.join(CACHE_DIR, key + ".json")

def is_cached(url: str) -> bool:
    """Kiểm tra URL đã được cache chưa"""
    bin_path, meta_path = cache_paths("GET", url)
    return os.path.exists(bin_path) and os.path.exists(meta_path)

def has_docid_and_page(url: str) -> bool:
    """Kiểm tra URL có chứa docId và page không"""
    try:
        parsed = urlparse(url)
        query = parsed.query
        return 'docId=' in query and 'page=' in query
    except Exception:
        return False

def extract_docids_from_html(base_url: str, html: str) -> Set[str]:
    """
    Extract tất cả docId từ HTML (từ ajaxHref, href, docid attribute)
    Returns: Set of docId values (strings)
    """
    soup = BeautifulSoup(html, "html.parser")
    docids = set()
    
    # Extract từ docid attribute (lowercase)
    for el in soup.find_all(attrs={"docid": True}):
        docid = el.get("docid")
        if docid and docid.isdigit():
            docids.add(docid)
    
    # Extract từ docId trong ajaxHref và onclick
    for el in soup.find_all():
        onclick = el.get("onclick", "")
        href = el.get("href", "")
        
        # Tìm docId trong ajaxHref('...')
        for text in [onclick, href]:
            if not text:
                continue
            
            # Pattern: ajaxHref('?...&docId=123...')
            ajax_matches = re.findall(r"ajaxHref\s*\(\s*['\"]([^'\"]*docId=(\d+)[^'\"]*)['\"]", text, re.IGNORECASE)
            for full_match, docid in ajax_matches:
                if docid.isdigit():
                    docids.add(docid)
            
            # Pattern: docId=123 trong query string
            docid_matches = re.findall(r'[?&]docId=(\d+)', text, re.IGNORECASE)
            for docid in docid_matches:
                if docid.isdigit():
                    docids.add(docid)
    
    return docids

def build_docid_page_urls(base_url: str, docids: Set[str], max_page: int = 10) -> Set[str]:
    """
    Tạo các URLs với docId và page từ base URL
    Args:
        base_url: URL gốc (ví dụ: https://kiagds.ru/?mode=ETM&marke=KM&year=2026&model=9923&mkb=445__29519)
        docids: Set các docId
        max_page: Số trang tối đa để tạo (mặc định: 10)
    Returns: Set of URLs
    """
    urls = set()
    
    try:
        parsed = urlparse(base_url)
        base_params = parse_qs(parsed.query, keep_blank_values=False)
        
        # Xóa docId và page nếu có trong base_params
        base_params.pop("docId", None)
        base_params.pop("docid", None)
        base_params.pop("page", None)
        
        # Build base URL không có docId và page
        base_query = urlencode({k: v[0] if isinstance(v, list) and len(v) == 1 else v 
                               for k, v in base_params.items()}, doseq=True)
        base_url_clean = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        if base_query:
            base_url_clean = f"{base_url_clean}?{base_query}"
        
        # Tạo URLs cho mỗi docId với các page
        for docid in docids:
            for page in range(1, max_page + 1):
                # Build URL với docId và page
                params = {k: (v[0] if isinstance(v, list) and len(v) == 1 else v) 
                         for k, v in base_params.items()}
                params["docId"] = docid
                params["page"] = str(page)
                
                url = f"{base_url_clean}?{urlencode(params)}"
                urls.add(normalize_url(url))
    
    except Exception as e:
        print(f"  ⚠️  Lỗi khi build docId page URLs: {e}")
    
    return urls

def in_domain(u: str) -> bool:
    """Kiểm tra URL có thuộc domain kiagds.ru không"""
    try:
        parsed = urlparse(u)
        netloc = parsed.netloc.lower().split(":")[0]
        return netloc.endswith("kiagds.ru")
    except Exception:
        return False

def normalize_url(url: str) -> str:
    """Chuẩn hóa URL: loại bỏ fragment, chuẩn hóa và xử lý parameters rỗng"""
    try:
        parsed = urlparse(url)
        # Loại bỏ fragment (#)
        base_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        
        if parsed.query:
            # Parse và làm sạch query parameters
            params = parse_qs(parsed.query, keep_blank_values=False)
            # Loại bỏ các parameters có giá trị rỗng hoặc chỉ có '='
            cleaned_params = {}
            for key, values in params.items():
                # Chỉ giữ lại các values không rỗng
                non_empty_values = [v for v in values if v and v.strip()]
                if non_empty_values:
                    cleaned_params[key] = non_empty_values[0] if len(non_empty_values) == 1 else non_empty_values
            
            # Xử lý trường hợp đặc biệt: page= ở cuối URL
            if 'page' in cleaned_params:
                page_val = cleaned_params['page']
                # Nếu page là chuỗi rỗng hoặc chỉ có '=', xóa nó
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
        # Fallback: loại bỏ fragment và parameters rỗng ở cuối
        url_no_fragment = url.split('#')[0]
        # Xóa &page= hoặc ?page= ở cuối
        url_cleaned = url_no_fragment.rstrip('=&?')
        if url_cleaned.endswith('&page') or url_cleaned.endswith('?page'):
            url_cleaned = url_cleaned[:-5]
        return url_cleaned.rstrip('&?')

def extract_pagination_info(base_url: str, html: str):
    """
    Extract thông tin pagination từ HTML
    Returns: (max_page, pagination_type)
    - max_page: số trang tối đa (None nếu không tìm thấy)
    - pagination_type: 'page_of' hoặc 'numbered' hoặc None
    """
    soup = BeautifulSoup(html, "html.parser")
    max_page = None
    pagination_type = None
    
    # Cách 1: Tìm "Page X of Y" pattern trong HTML và text content
    page_of_pattern = re.search(r'Page\s+(\d+)\s+of\s+(\d+)', html, re.IGNORECASE)
    if not page_of_pattern:
        # Tìm trong text content của soup
        text_content = soup.get_text()
        page_of_pattern = re.search(r'Page\s+(\d+)\s+of\s+(\d+)', text_content, re.IGNORECASE)
    
    if page_of_pattern:
        current_page = int(page_of_pattern.group(1))
        max_page = int(page_of_pattern.group(2))
        pagination_type = 'page_of'
        return max_page, pagination_type
    
    # Cách 2: Tìm pagination links (liệt kê số trang)
    page_numbers = set()
    
    # Tìm trong onclick handlers
    for el in soup.find_all(attrs=lambda x: x and isinstance(x, dict) and 'onclick' in x):
        onclick = el.get('onclick', '')
        if 'page=' in onclick:
            matches = re.findall(r'[&?]page=(\d+)', onclick)
            page_numbers.update(int(m) for m in matches if m.isdigit())
    
    # Tìm trong href attributes
    for el in soup.find_all(['a', 'link']):
        href = el.get('href', '')
        if href and 'page=' in href:
            matches = re.findall(r'[&?]page=(\d+)', href)
            page_numbers.update(int(m) for m in matches if m.isdigit())
    
    # Tìm trong text content có chứa « và » (pagination navigation)
    pagination_text = soup.find(string=re.compile(r'[«»]', re.I))
    if pagination_text:
        # Tìm các số trong pagination container
        parent = pagination_text.parent
        if parent:
            container_text = parent.get_text()
            # Tìm các số trong context pagination
            text_numbers = re.findall(r'\b(\d+)\b', container_text)
            # Lọc các số có thể là số trang (thường là số nhỏ hoặc trong context pagination)
            for num_str in text_numbers:
                num = int(num_str)
                if 1 <= num <= 1000:  # Giới hạn hợp lý cho số trang
                    page_numbers.add(num)
    
    # Tìm các element có text là số và có onclick/href với page=
    for el in soup.find_all(['a', 'span', 'div', 'li', 'button']):
        text = el.get_text(strip=True)
        if text.isdigit():
            onclick = el.get('onclick', '')
            href = el.get('href', '')
            if 'page=' in onclick or 'page=' in href:
                try:
                    page_num = int(text)
                    if 1 <= page_num <= 1000:
                        page_numbers.add(page_num)
                except ValueError:
                    pass
    
    if page_numbers:
        max_page = max(page_numbers)
        pagination_type = 'numbered'
        return max_page, pagination_type
    
    return None, None

def extract_links(base_url: str, html: str):
    """Extract tất cả links từ HTML"""
    soup = BeautifulSoup(html, "html.parser")
    urls = set()
    
    # Extract từ các thẻ HTML
    for tag, attr in (
        ("a", "href"), 
        ("link", "href"), 
        ("script", "src"), 
        ("img", "src"), 
        ("source", "src"), 
        ("iframe", "src"),
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
                    urls.add(u)
            except Exception:
                continue
    
    # Extract từ JavaScript (tìm các URL trong JS)
    for script in soup.find_all("script"):
        if script.string:
            # Tìm các URL kiagds.ru trong JavaScript
            js_urls = re.findall(r'https?://kiagds\.ru[^\s"\'<>)]+', script.string)
            for u in js_urls:
                try:
                    u = normalize_url(u)
                    if in_domain(u):
                        urls.add(u)
                except Exception:
                    continue
    
    # Extract từ các thuộc tính data-* và onclick handlers
    try:
        for el in soup.find_all():
            try:
                if not hasattr(el, 'attrs') or not el.attrs:
                    continue
                # BeautifulSoup có thể trả về attrs là dict hoặc list
                attrs = el.attrs
                if not isinstance(attrs, dict):
                    continue
                
                for attr_name, attr_value in attrs.items():
                    if not isinstance(attr_value, str):
                        continue
                    
                    # Extract từ data-* attributes có chứa URL
                    if attr_name.startswith('data-') and 'kiagds.ru' in attr_value:
                        js_urls = re.findall(r'https?://kiagds\.ru[^\s"\'<>)]+', attr_value)
                        for u in js_urls:
                            try:
                                u = normalize_url(u)
                                if in_domain(u):
                                    urls.add(u)
                            except Exception:
                                continue
                    
                    # Extract từ onclick handlers (ajaxHref, location.href, etc.)
                    if attr_name == 'onclick' and ('docId=' in attr_value or 'kiagds.ru' in attr_value):
                        # Tìm ajaxHref('...') hoặc các hàm tương tự
                        onclick_urls = re.findall(r"(?:ajaxHref|location\.href|window\.location)\s*[=\(]\s*['\"]([^'\"]+)['\"]", attr_value)
                        for match in onclick_urls:
                            try:
                                # Nếu là relative URL, join với base_url
                                if match.startswith('?'):
                                    u = urljoin(base_url, match)
                                elif match.startswith('/'):
                                    u = urljoin(base_url, match)
                                elif 'kiagds.ru' in match:
                                    u = match
                                else:
                                    u = urljoin(base_url, match)
                                
                                u = normalize_url(u)
                                if in_domain(u):
                                    urls.add(u)
                            except Exception:
                                continue
                        
                        # Cũng tìm các URL pattern trực tiếp trong onclick
                        direct_urls = re.findall(r'https?://kiagds\.ru[^\s"\'<>)]+', attr_value)
                        for u in direct_urls:
                            try:
                                u = normalize_url(u)
                                if in_domain(u):
                                    urls.add(u)
                            except Exception:
                                continue
                    
                    # Extract từ các attribute khác có chứa docId hoặc URL
                    if 'docId=' in attr_value or 'kiagds.ru' in attr_value:
                        # Tìm các query string pattern với docId
                        query_urls = re.findall(r'\?mode=[^\s"\'<>)]+docId=\d+', attr_value)
                        for qs in query_urls:
                            try:
                                u = urljoin(base_url, qs)
                                u = normalize_url(u)
                                if in_domain(u):
                                    urls.add(u)
                            except Exception:
                                continue
                        
                        # Tìm các URL đầy đủ
                        full_urls = re.findall(r'https?://kiagds\.ru[^\s"\'<>)]+', attr_value)
                        for u in full_urls:
                            try:
                                u = normalize_url(u)
                                if in_domain(u):
                                    urls.add(u)
                            except Exception:
                                continue
                                
            except (AttributeError, TypeError, ValueError):
                continue
    except Exception:
        pass  # Bỏ qua nếu có lỗi khi extract attributes
    
    return urls

async def fetch_via_proxy(client: httpx.AsyncClient, url: str, proxy_base: str):
    """Fetch URL qua proxy"""
    # Chuyển đổi URL origin sang proxy URL
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

async def fetch_via_proxy_with_retry(client: httpx.AsyncClient, url: str, proxy_base: str, max_retries: int = 10, verbose: bool = False):
    """Fetch URL qua proxy với retry logic"""
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            r = await fetch_via_proxy(client, url, proxy_base)
            
            # Nếu thành công ở lần retry thứ 2 trở đi, log ra
            if attempt > 0:
                print(f"  ✅ Retry thành công sau {attempt + 1} lần thử: {url}")
            
            return r
        except Exception as e:
            last_exception = e
            
            # Nếu là lỗi connection (proxy không chạy), không retry
            if "Không thể kết nối tới proxy" in str(e):
                raise
            
            # Log retry attempt
            if attempt < max_retries - 1:
                retry_delay = min(2 ** attempt, 10)  # Exponential backoff, max 10s
                if verbose or attempt > 2:  # Chỉ log từ lần thử thứ 3 hoặc khi verbose
                    print(f"  ⚠️  Lần thử {attempt + 1}/{max_retries} thất bại: {url}")
                    print(f"     Lỗi: {type(e).__name__}: {str(e)[:100]}")
                    print(f"     Đợi {retry_delay}s trước khi retry...")
                await asyncio.sleep(retry_delay)
            else:
                # Hết số lần retry
                print(f"  ❌ Đã retry {max_retries} lần nhưng vẫn thất bại: {url}")
    
    # Raise exception cuối cùng nếu tất cả lần retry đều thất bại
    raise last_exception

def load_important_links() -> set:
    """Load danh sách URLs từ important_links.json"""
    if not os.path.exists(IMPORTANT_LINKS_FILE):
        return set()
    
    try:
        with open(IMPORTANT_LINKS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        urls = set()
        if isinstance(data, list):
            urls = set(data)
        elif isinstance(data, dict) and 'urls' in data:
            urls = {item.get('url') if isinstance(item, dict) else item for item in data['urls']}
        
        return urls
    except Exception as e:
        print(f"⚠️  Lỗi khi đọc {IMPORTANT_LINKS_FILE}: {e}")
        return set()

def save_important_links(urls: list):
    """Lưu danh sách URLs vào important_links.json (thread-safe)"""
    try:
        # Sắp xếp để dễ đọc
        sorted_urls = sorted(urls)
        with open(IMPORTANT_LINKS_FILE, 'w', encoding='utf-8') as f:
            json.dump(sorted_urls, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️  Lỗi khi lưu {IMPORTANT_LINKS_FILE}: {e}")

async def append_to_important_links(new_urls: set, existing_urls: set, lock: asyncio.Lock):
    """Append URLs mới vào important_links.json (thread-safe)"""
    if not new_urls:
        return 0
    
    # Filter URLs mới (chưa có trong existing_urls)
    truly_new = {u for u in new_urls if u not in existing_urls}
    if not truly_new:
        return 0
    
    # Update existing_urls
    existing_urls.update(truly_new)
    
    # Lưu vào file (cần lock để tránh race condition)
    async with lock:
        # Load lại để đảm bảo không mất dữ liệu
        current = load_important_links()
        current.update(truly_new)
        save_important_links(list(current))
    
    return len(truly_new)

async def crawl(args, proxy_base: str):
    seen = set()
    q = asyncio.Queue()
    cached_count = 0
    new_count = 0
    error_count = 0
    
    # Load important_links.json để track URLs đã có
    important_links = load_important_links()
    print(f"📖 Đã load {len(important_links)} URLs từ {IMPORTANT_LINKS_FILE}")
    
    # Lock để đảm bảo thread-safe khi update important_links.json
    important_links_lock = asyncio.Lock()
    new_important_links_count = 0

    # Thêm seed URLs
    seeds = []
    if args.seed:
        for p in range(args.start_page, args.end_page + 1):
            seed_url = f"{args.seed}{p}"
            normalized = normalize_url(seed_url)
            seeds.append(normalized)
    
    if args.extra_urls:
        for u in args.extra_urls:
            normalized = normalize_url(u)
            seeds.append(normalized)
    
    if not seeds:
        # Default: trang chủ qua proxy
        seeds = [f"{proxy_base}/"]

    for u in seeds:
        normalized = normalize_url(u)
        if normalized not in seen:
            await q.put((normalized, 0))
            seen.add(normalized)

    if not seeds:
        print("❌ Không có seed URL nào!")
        return

    # Kiểm tra proxy có đang chạy không
    print(f"\n🔍 Kiểm tra proxy {proxy_base}...")
    proxy_ok = False
    try:
        test_client = httpx.Client(timeout=5.0)
        test_response = test_client.get(f"{proxy_base}/_cache_stats")
        if test_response.status_code == 200:
            print(f"✅ Proxy đang chạy")
            try:
                stats = test_response.json()
                print(f"   - Cached responses: {stats.get('cached_responses', 'N/A')}")
                print(f"   - Live fallback: {stats.get('live_fallback', 'N/A')}")
            except:
                pass
            proxy_ok = True
        else:
            print(f"⚠️  Proxy trả về status {test_response.status_code}")
        test_client.close()
    except Exception as e:
        print(f"❌ Proxy không thể kết nối: {e}")
        print(f"\n💡 Hãy chạy proxy trước trong terminal khác:")
        print(f"   conda activate crawl")
        print(f"   export LIVE_FALLBACK=true")
        print(f"   conda run -n crawl python app.py")
        print(f"\n⚠️  Không thể tiếp tục crawl nếu proxy không chạy!")
        return
    
    if not proxy_ok:
        print(f"\n⚠️  Proxy check không thành công. Dừng crawl để tránh lỗi.")
        return

    print(f"\n📋 Seed URLs: {len(seeds)}")
    for seed in seeds[:5]:  # Hiển thị 5 seed đầu
        print(f"   - {seed}")
    if len(seeds) > 5:
        print(f"   ... và {len(seeds) - 5} URL khác")

    limits = httpx.Limits(max_keepalive_connections=10, max_connections=args.concurrency)
    timeout = httpx.Timeout(30.0)
    
    async with httpx.AsyncClient(limits=limits, timeout=timeout) as client:
        sem = asyncio.Semaphore(args.concurrency)

        async def worker():
            nonlocal cached_count, new_count, error_count, new_important_links_count
            while True:
                try:
                    url, depth = await asyncio.wait_for(q.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    return
                
                # Kiểm tra đã cache chưa (chỉ để đếm, không skip)
                already_cached = is_cached(url)
                if already_cached:
                    cached_count += 1
                    if args.verbose:
                        print(f"[ALREADY_CACHED] {url} (crawl lại để tìm links mới)")

                try:
                    async with sem:
                        if args.delay > 0:
                            await asyncio.sleep(args.delay)
                        
                        r = await fetch_via_proxy_with_retry(client, url, proxy_base, max_retries=args.max_retries, verbose=args.verbose)
                        # Đếm là "mới crawl" nếu chưa có cache trước đó
                        if not already_cached:
                            new_count += 1
                        status_icon = "✅" if r.status_code == 200 else "⚠️"
                        cache_status = " [CACHED]" if already_cached else ""
                        print(f"{status_icon} [{r.status_code}]{cache_status} {url} (depth={depth})")
                        
                        # Extract links từ HTML
                        ctype = r.headers.get("Content-Type", "").lower()
                        if args.follow_depth > depth and ("text/html" in ctype or "application/xhtml" in ctype):
                            try:
                                enc = re.search(r"charset=([^;]+)", ctype, flags=re.I)
                                enc = enc.group(1).strip() if enc else "utf-8"
                                text = r.content.decode(enc, errors="replace")
                            except Exception:
                                try:
                                    text = r.text
                                except Exception:
                                    text = r.content.decode("utf-8", errors="replace")
                            
                            # Extract links với error handling
                            try:
                                links = extract_links(url, text)
                                added = 0
                                new_important_links = set()  # Track URLs có docId và page
                                
                                for link in links:
                                    try:
                                        normalized = normalize_url(link)
                                        if in_domain(normalized) and normalized not in seen:
                                            seen.add(normalized)
                                            await q.put((normalized, depth + 1))
                                            added += 1
                                            
                                            # Nếu URL có docId và page, thêm vào danh sách để update important_links.json
                                            if has_docid_and_page(normalized):
                                                new_important_links.add(normalized)
                                    except Exception:
                                        continue
                                
                                # Extract docIds từ HTML và tạo links với các page
                                try:
                                    docids = extract_docids_from_html(url, text)
                                    if docids:
                                        # Phát hiện max_page từ pagination
                                        max_page_info, pagination_type = extract_pagination_info(url, text)
                                        max_page = max_page_info if max_page_info else 10  # Default 10 nếu không tìm thấy
                                        
                                        # Tạo URLs với docId và page
                                        docid_page_urls = build_docid_page_urls(url, docids, max_page)
                                        
                                        # Thêm vào queue và track
                                        docid_links_added = 0
                                        for docid_url in docid_page_urls:
                                            if docid_url not in seen:
                                                seen.add(docid_url)
                                                await q.put((docid_url, depth + 1))
                                                docid_links_added += 1
                                                new_important_links.add(docid_url)
                                        
                                        if docid_links_added > 0:
                                            print(f"  🔗 Tìm thấy {len(docids)} docId, tạo {docid_links_added} links với page (max_page={max_page})")
                                except Exception as docid_error:
                                    if args.verbose:
                                        print(f"  ⚠️  Lỗi khi extract docIds: {docid_error}")
                                
                                # Tự động update important_links.json nếu có links mới có docId và page
                                if new_important_links:
                                    count = await append_to_important_links(new_important_links, important_links, important_links_lock)
                                    if count > 0:
                                        new_important_links_count += count
                                        print(f"  📝 Đã thêm {count} URLs có docId&page vào {IMPORTANT_LINKS_FILE} (tổng: {new_important_links_count} mới)")
                                
                                # Tự động phát hiện và crawl pagination
                                if args.auto_pagination:
                                    try:
                                        max_page, pagination_type = extract_pagination_info(url, text)
                                        if max_page and max_page > 1:
                                            print(f"  📄 Phát hiện pagination: {pagination_type}, max_page={max_page}")
                                            
                                            # Tạo base URL cho pagination
                                            parsed = urlparse(url)
                                            query_params = {}
                                            if parsed.query:
                                                query_params = {k: v[0] if len(v) == 1 else v for k, v in parse_qs(parsed.query).items()}
                                            
                                            # Xóa page parameter nếu có để tạo base URL
                                            base_url_for_pagination = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                                            
                                            # Thêm tất cả các trang vào queue
                                            pagination_added = 0
                                            new_pagination_important = set()
                                            
                                            for page_num in range(1, max_page + 1):
                                                query_params['page'] = str(page_num)
                                                pagination_url = f"{base_url_for_pagination}?{urlencode(query_params)}"
                                                normalized = normalize_url(pagination_url)
                                                
                                                if normalized not in seen:
                                                    seen.add(normalized)
                                                    await q.put((normalized, depth))
                                                    pagination_added += 1
                                                    
                                                    # Nếu pagination URL có docId và page, thêm vào important_links
                                                    if has_docid_and_page(normalized):
                                                        new_pagination_important.add(normalized)
                                            
                                            if pagination_added > 0:
                                                print(f"  📄 Đã thêm {pagination_added} trang pagination vào queue")
                                            
                                            # Update important_links.json cho pagination URLs
                                            if new_pagination_important:
                                                count = await append_to_important_links(new_pagination_important, important_links, important_links_lock)
                                                if count > 0:
                                                    new_important_links_count += count
                                                    print(f"  📝 Đã thêm {count} pagination URLs có docId&page vào {IMPORTANT_LINKS_FILE}")
                                    except Exception as pagination_error:
                                        if args.verbose:
                                            print(f"  ⚠️  Không thể extract pagination từ {url}: {pagination_error}")
                                
                                if args.verbose and added > 0:
                                    print(f"  🔗 Found {added} new links (total: {len(seen)})")
                            except Exception as extract_error:
                                # Log nhưng không crash nếu extract links fail
                                if args.verbose:
                                    print(f"  ⚠️  Không thể extract links từ {url}: {extract_error}")
                            
                except httpx.HTTPError as e:
                    error_count += 1
                    print(f"❌ [HTTP_ERROR] {url}: {e}")
                except Exception as e:
                    error_count += 1
                    print(f"❌ [ERROR] {url}: {e}")
                finally:
                    q.task_done()

        workers = [asyncio.create_task(worker()) for _ in range(args.concurrency)]
        await q.join()
        for w in workers:
            w.cancel()
        
        # Đợi tất cả các task save important_links.json hoàn thành
        await asyncio.sleep(1)  # Đợi các async save hoàn thành
        
        print(f"\n{'='*60}")
        print(f"✅ Hoàn thành crawl!")
        print(f"   - Đã cache sẵn: {cached_count} URLs")
        print(f"   - Mới crawl: {new_count} URLs")
        print(f"   - Lỗi: {error_count} URLs")
        print(f"   - Tổng URLs đã xử lý: {len(seen)} URLs")
        if new_important_links_count > 0:
            print(f"   - URLs có docId&page mới thêm vào {IMPORTANT_LINKS_FILE}: {new_important_links_count}")
        print(f"{'='*60}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(
        description="Auto crawler qua proxy để cache toàn bộ trang web kiagds.ru"
    )
    ap.add_argument("--seed", type=str, default="", 
                    help="Seed URL có phần &page= (vd: 'https://kiagds.ru/?...&page=')")
    ap.add_argument("--start-page", type=int, default=1,
                    help="Trang bắt đầu (nếu seed có pagination)")
    ap.add_argument("--end-page", type=int, default=1,
                    help="Trang kết thúc (nếu seed có pagination)")
    ap.add_argument("--extra-urls", nargs="*", help="Các URL bổ sung", default=[])
    ap.add_argument("--json-file", type=str, default="",
                    help="Đường dẫn file JSON chứa danh sách URLs để crawl")
    ap.add_argument("--json-start-index", type=int, default=0,
                    help="Chỉ số bắt đầu khi đọc từ JSON (mặc định: 0)")
    ap.add_argument("--json-end-index", type=int, default=None,
                    help="Chỉ số kết thúc khi đọc từ JSON (mặc định: tất cả)")
    ap.add_argument("--concurrency", type=int, default=4, 
                    help="Số lượng request đồng thời (mặc định: 4)")
    ap.add_argument("--delay", type=float, default=0.5, 
                    help="Giãn cách giữa các request - giây (mặc định: 0.5)")
    ap.add_argument("--follow-depth", type=int, default=3, 
                    help="Độ sâu crawl links (0 = chỉ seeds, >0 = tự động crawl links, mặc định: 3)")
    ap.add_argument("--verbose", action="store_true", 
                    help="Hiển thị chi tiết (cached URLs và links found)")
    ap.add_argument("--proxy-base", type=str, default="",
                    help="URL proxy base (mặc định: http://localhost:5002)")
    ap.add_argument("--auto-pagination", action="store_true", default=True,
                    help="Tự động phát hiện và crawl pagination (mặc định: True)")
    ap.add_argument("--max-retries", type=int, default=10,
                    help="Số lần retry khi gặp lỗi (mặc định: 10)")
    args = ap.parse_args()
    
    # Load URLs từ file JSON nếu được chỉ định
    if args.json_file:
        try:
            print(f"📖 Đang đọc URLs từ file: {args.json_file}")
            with open(args.json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            urls_from_json = []
            if isinstance(data, dict):
                if 'urls' in data:
                    # Format: {"urls": [{"url": "..."}, ...]}
                    for item in data['urls']:
                        url = item.get('url') if isinstance(item, dict) else item
                        if url and isinstance(url, str):
                            urls_from_json.append(url)
                elif 'url' in data:
                    # Single URL object
                    urls_from_json.append(data['url'])
            elif isinstance(data, list):
                # Format: [{"url": "..."}, ...] hoặc ["url1", "url2", ...]
                for item in data:
                    url = item.get('url') if isinstance(item, dict) else item
                    if url and isinstance(url, str):
                        urls_from_json.append(url)
            
            # Apply index range
            total_urls = len(urls_from_json)
            end_idx = args.json_end_index if args.json_end_index is not None else total_urls
            urls_from_json = urls_from_json[args.json_start_index:end_idx]
            
            print(f"✅ Đã load {len(urls_from_json)} URLs từ JSON")
            if total_urls > len(urls_from_json):
                print(f"   (từ index {args.json_start_index} đến {end_idx-1} trong tổng {total_urls} URLs)")
            if len(urls_from_json) > 1000:
                print(f"⚠️  Số lượng URLs lớn ({len(urls_from_json)}). Cân nhắc sử dụng --json-start-index và --json-end-index để chia nhỏ.")
            
            # Thêm vào extra_urls
            if args.extra_urls:
                args.extra_urls.extend(urls_from_json)
            else:
                args.extra_urls = urls_from_json
                
        except FileNotFoundError:
            print(f"❌ Không tìm thấy file: {args.json_file}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"❌ Lỗi parse JSON: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Lỗi khi đọc file JSON: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    
    # Override proxy base nếu được chỉ định
    proxy_base = PROXY_BASE
    if args.proxy_base:
        proxy_base = args.proxy_base
    
    print(f"{'='*60}")
    print(f"🚀 Auto Crawler qua Proxy")
    print(f"{'='*60}")
    print(f"   Proxy: {proxy_base}")
    print(f"   Origin: {ORIGIN}")
    print(f"   Cache dir: {CACHE_DIR}")
    print(f"   Follow depth: {args.follow_depth}")
    print(f"   Concurrency: {args.concurrency}")
    print(f"   Delay: {args.delay}s")
    print(f"   Max retries: {args.max_retries}")
    print(f"{'='*60}\n")
    
    asyncio.run(crawl(args, proxy_base))

