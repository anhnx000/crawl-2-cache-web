#!/usr/bin/env python3
"""
Script để extract docId và page links từ một URL hoặc nhiều URLs
và append vào important_links_with_docid_and_page.json

Khi duyệt vào web, phát hiện ra links có docId và page thì append vào file này
"""

import asyncio
import os
import json
import sys
import re
import argparse
from typing import List, Set
from urllib.parse import urlparse, urljoin, urlencode, parse_qs
import httpx
from bs4 import BeautifulSoup

# ================== CONFIG ==================
PROXY_BASE = os.getenv("LOCAL_BASE", "http://localhost:5002")
ORIGIN = os.getenv("ORIGIN", "https://kiagds.ru")
IMPORTANT_LINKS_DOCID_PAGE_FILE = "important_links_with_docid_and_page.json"
UA = "ExtractDocIdPageLinks/1.0 (+respectful; via-proxy)"
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

def extract_pagination_info_from_html(html: str):
    """
    Extract thông tin pagination từ HTML
    Returns: (max_page, pagination_type)
    """
    soup = BeautifulSoup(html, "html.parser")
    max_page = None
    pagination_type = None
    
    # Cách 1: Tìm "Page X of Y" pattern
    page_of_pattern = re.search(r'Page\s+(\d+)\s+of\s+(\d+)', html, re.IGNORECASE)
    if not page_of_pattern:
        text_content = soup.get_text()
        page_of_pattern = re.search(r'Page\s+(\d+)\s+of\s+(\d+)', text_content, re.IGNORECASE)
    
    if page_of_pattern:
        max_page = int(page_of_pattern.group(2))
        pagination_type = 'page_of'
        return max_page, pagination_type
    
    # Cách 2: Tìm pagination links
    page_numbers = set()
    
    for el in soup.find_all(attrs=lambda x: x and isinstance(x, dict) and 'onclick' in x):
        onclick = el.get('onclick', '')
        if 'page=' in onclick:
            matches = re.findall(r'[&?]page=(\d+)', onclick)
            page_numbers.update(int(m) for m in matches if m.isdigit())
    
    for el in soup.find_all(['a', 'link']):
        href = el.get('href', '')
        if href and 'page=' in href:
            matches = re.findall(r'[&?]page=(\d+)', href)
            page_numbers.update(int(m) for m in matches if m.isdigit())
    
    # Tìm trong pagination navigation (số trang)
    pagination_links = soup.find_all('a', href=re.compile(r'page=\d+'))
    for link in pagination_links:
        text = link.get_text(strip=True)
        if text.isdigit():
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

def build_docid_page_urls(base_url: str, docids: Set[str], max_page: int = 10) -> Set[str]:
    """
    Tạo các URLs với docId và page từ base URL
    """
    urls = set()
    
    try:
        parsed = urlparse(base_url)
        base_params = parse_qs(parsed.query, keep_blank_values=False)
        
        # Xóa docId và page nếu có
        base_params.pop("docId", None)
        base_params.pop("docid", None)
        base_params.pop("page", None)
        
        # Build base URL
        base_query = urlencode({k: v[0] if isinstance(v, list) and len(v) == 1 else v 
                               for k, v in base_params.items()}, doseq=True)
        base_url_clean = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        if base_query:
            base_url_clean = f"{base_url_clean}?{base_query}"
        
        # Tạo URLs cho mỗi docId với các page
        for docid in docids:
            for page in range(1, max_page + 1):
                params = {k: (v[0] if isinstance(v, list) and len(v) == 1 else v) 
                         for k, v in base_params.items()}
                params["docId"] = docid
                params["page"] = str(page)
                
                url = f"{base_url_clean}?{urlencode(params)}"
                urls.add(normalize_url(url))
    
    except Exception as e:
        print(f"  ⚠️  Lỗi khi build docId page URLs: {e}")
    
    return urls

def extract_docid_page_links(base_url: str, html: str) -> Set[str]:
    """
    Extract tất cả links có docId và page từ HTML
    Bao gồm cả việc extract docIds và tạo links với các page
    """
    soup = BeautifulSoup(html, "html.parser")
    urls = set()
    
    # Extract từ các thẻ HTML (a, link, etc.) - links đã có sẵn docId và page
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
    
    # Extract từ JavaScript
    for script in soup.find_all("script"):
        if script.string:
            js_urls = re.findall(r'https?://kiagds\.ru[^\s"\'<>)]+', script.string)
            for u in js_urls:
                try:
                    u = normalize_url(u)
                    if in_domain(u) and has_docid_and_page(u):
                        urls.add(u)
                except Exception:
                    continue
    
    # Extract từ onclick handlers
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
                    
                    # Extract từ onclick với ajaxHref
                    if attr_name == 'onclick' and ('ajaxHref' in attr_value or 'docId=' in attr_value):
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
                                if in_domain(u):
                                    if has_docid_and_page(u):
                                        urls.add(u)
                            except Exception:
                                continue
                                
            except (AttributeError, TypeError, ValueError):
                continue
    except Exception:
        pass
    
    # QUAN TRỌNG: Extract docIds từ HTML và tạo links với các page
    try:
        docids = extract_docids_from_html(base_url, html)
        if docids:
            # Phát hiện max_page từ pagination
            max_page_info, pagination_type = extract_pagination_info_from_html(html)
            max_page = max_page_info if max_page_info else 10  # Default 10
            
            # Tạo URLs với docId và page
            docid_page_urls = build_docid_page_urls(base_url, docids, max_page)
            urls.update(docid_page_urls)
            
            print(f"  🔍 Tìm thấy {len(docids)} docId, tạo {len(docid_page_urls)} links với page (max_page={max_page})")
            
            # Hiển thị các docIds tìm được
            if len(docids) <= 10:
                print(f"  📋 DocIds: {', '.join(sorted(docids))}")
            else:
                docids_list = sorted(list(docids))
                print(f"  📋 DocIds (first 10): {', '.join(docids_list[:10])} ... và {len(docids) - 10} docIds khác")
    except Exception as e:
        print(f"  ⚠️  Lỗi khi extract docIds và tạo page links: {e}")
        import traceback
        traceback.print_exc()
    
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

def load_docid_page_links() -> Set[str]:
    """Load danh sách URLs từ important_links_with_docid_and_page.json"""
    if not os.path.exists(IMPORTANT_LINKS_DOCID_PAGE_FILE):
        return set()
    
    try:
        with open(IMPORTANT_LINKS_DOCID_PAGE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        urls = set()
        if isinstance(data, list):
            urls = set(data)
        elif isinstance(data, dict) and 'urls' in data:
            urls = {item.get('url') if isinstance(item, dict) else item for item in data['urls']}
        
        return urls
    except Exception as e:
        print(f"⚠️  Lỗi khi đọc {IMPORTANT_LINKS_DOCID_PAGE_FILE}: {e}")
        return set()

def save_docid_page_links(urls: List[str]):
    """Lưu danh sách URLs vào important_links_with_docid_and_page.json"""
    try:
        sorted_urls = sorted(urls)
        with open(IMPORTANT_LINKS_DOCID_PAGE_FILE, 'w', encoding='utf-8') as f:
            json.dump(sorted_urls, f, indent=2, ensure_ascii=False)
        print(f"✅ Đã lưu {len(sorted_urls)} URLs vào {IMPORTANT_LINKS_DOCID_PAGE_FILE}")
    except Exception as e:
        print(f"❌ Lỗi khi lưu {IMPORTANT_LINKS_DOCID_PAGE_FILE}: {e}")
        raise

async def extract_and_append_from_url(url: str, proxy_base: str) -> Set[str]:
    """
    Extract docId và page links từ một URL cụ thể
    """
    print(f"\n🔍 Đang extract docId & page links từ: {url}")
    print(f"   Proxy: {proxy_base}")
    print("")
    
    async with httpx.AsyncClient() as client:
        try:
            print("📥 Đang fetch HTML qua proxy...")
            r = await fetch_via_proxy(client, url, proxy_base)
            
            if r.status_code != 200:
                print(f"❌ Không thể fetch URL: HTTP {r.status_code}")
                return set()
            
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
            
            # Extract links có docId và page
            extracted_urls = extract_docid_page_links(url, html)
            
            if not extracted_urls:
                print("⚠️  Không tìm thấy links nào có docId và page")
                return set()
            
            print(f"✅ Tìm thấy {len(extracted_urls)} links có docId và page")
            print("")
            
            # Hiển thị một vài ví dụ
            print("📋 Ví dụ các links tìm được (first 10):")
            for i, u in enumerate(list(extracted_urls)[:10], 1):
                print(f"   {i}. {u}")
            if len(extracted_urls) > 10:
                print(f"   ... và {len(extracted_urls) - 10} links khác")
            print("")
            
            return extracted_urls
            
        except Exception as e:
            print(f"❌ Lỗi khi extract từ URL: {e}")
            import traceback
            traceback.print_exc()
            return set()

async def process_urls(urls: List[str], proxy_base: str, append: bool = True):
    """
    Process nhiều URLs và append vào important_links_with_docid_and_page.json
    """
    all_extracted = set()
    
    for i, url in enumerate(urls, 1):
        print(f"\n{'='*60}")
        print(f"Processing URL {i}/{len(urls)}")
        print(f"{'='*60}")
        
        # Normalize URL
        normalized_url = normalize_url(url)
        
        if not in_domain(normalized_url):
            print(f"⚠️  URL không thuộc domain kiagds.ru, bỏ qua: {url}")
            continue
        
        extracted = await extract_and_append_from_url(normalized_url, proxy_base)
        all_extracted.update(extracted)
        
        # Delay giữa các requests
        if i < len(urls):
            await asyncio.sleep(0.5)
    
    if not all_extracted:
        print("\n⚠️  Không có links nào để lưu")
        return
    
    # Load existing nếu append mode
    if append:
        existing = load_docid_page_links()
        new_links = {u for u in all_extracted if u not in existing}
        
        if new_links:
            print(f"\n📝 Tìm thấy {len(new_links)} links mới")
            print(f"   (Tổng: {len(existing)} + {len(new_links)} = {len(existing) + len(new_links)})")
            all_extracted = existing.union(new_links)
        else:
            print(f"\nℹ️  Tất cả links đã có trong {IMPORTANT_LINKS_DOCID_PAGE_FILE}")
            all_extracted = existing
    else:
        print(f"\n📝 Tìm thấy {len(all_extracted)} links (ghi đè file)")
    
    # Save to file
    save_docid_page_links(sorted(list(all_extracted)))
    
    # Also save as text file
    output_text_file = "important_links_with_docid_and_page.txt"
    with open(output_text_file, "w", encoding="utf-8") as f:
        for link in sorted(all_extracted):
            f.write(link + "\n")
    
    print(f"✅ Links cũng được lưu vào {output_text_file}")
    
    # Statistics
    print(f"\n{'='*60}")
    print("📊 Statistics")
    print(f"{'='*60}")
    print(f"   Tổng URLs có docId & page: {len(all_extracted)}")
    
    # Count by docId
    docid_counts = {}
    for url in all_extracted:
        try:
            parsed = urlparse(url)
            params = parse_qs(parsed.query)
            docid = params.get("docId", [None])[0] or params.get("docid", [None])[0]
            if docid:
                docid_counts[docid] = docid_counts.get(docid, 0) + 1
        except:
            pass
    
    if docid_counts:
        print(f"   Số docId unique: {len(docid_counts)}")
        print(f"   Top 10 docId (theo số pages):")
        sorted_docids = sorted(docid_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        for docid, count in sorted_docids:
            print(f"      - docId={docid}: {count} pages")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Extract docId và page links từ URL(s) và append vào important_links_with_docid_and_page.json"
    )
    parser.add_argument("urls", nargs="+", type=str,
                        help="URL(s) để extract (ví dụ: https://kiagds.ru/?mode=ETM&marke=KM&year=2026&model=9923&mkb=445__29519)")
    parser.add_argument("--proxy-base", type=str, default=PROXY_BASE,
                        help=f"Proxy base URL (mặc định: {PROXY_BASE})")
    parser.add_argument("--no-append", action="store_true",
                        help="Ghi đè file thay vì append")
    parser.add_argument("--json-file", type=str,
                        help="Đọc URLs từ file JSON (list of URLs)")
    
    args = parser.parse_args()
    
    # Load URLs từ file JSON nếu được chỉ định
    urls_to_process = list(args.urls)
    
    if args.json_file:
        try:
            print(f"📖 Đang đọc URLs từ file: {args.json_file}")
            with open(args.json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, list):
                urls_to_process.extend(data)
            elif isinstance(data, dict) and 'urls' in data:
                urls_to_process.extend([item.get('url') if isinstance(item, dict) else item for item in data['urls']])
            
            print(f"✅ Đã load {len(urls_to_process) - len(args.urls)} URLs từ JSON")
        except Exception as e:
            print(f"⚠️  Lỗi khi đọc file JSON: {e}")
    
    if not urls_to_process:
        print("❌ Không có URLs nào để process")
        sys.exit(1)
    
    # Remove duplicates
    unique_urls = list(dict.fromkeys(urls_to_process))
    print(f"\n📋 Tổng số URLs sẽ process: {len(unique_urls)}")
    
    # Process URLs
    asyncio.run(process_urls(unique_urls, args.proxy_base, append=not args.no_append))
    
    print(f"\n{'='*60}")
    print("✅ Hoàn thành!")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()


