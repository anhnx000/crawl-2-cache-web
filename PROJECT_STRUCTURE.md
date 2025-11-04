# 📁 Project Structure

Cấu trúc project sau khi clean up (updated: 2025-11-04)

## 🎯 Core Scripts

### Proxy Server
- **`app.py`** - Proxy server chính (chạy ở localhost:5002)
  - Cache responses tự động
  - Rewrite URLs để browse offline
  - Live fallback khi cache miss

### Auto Crawler
- **`auto_crawl_proxy.py`** - Auto crawler chính (async, với retry logic)
  - Crawl qua proxy để cache tự động
  - Extract links từ HTML, JavaScript, onclick handlers
  - Auto pagination detection
  - Follow depth configurable
  - Retry với exponential backoff

### Data Extraction
- **`extract_important_link_to_crawl.py`** - Extract important links từ tree_title.json
  - Tạo ra: `important_links.json` (16,304 URLs)
  - Theo hierarchy: mode → marke → year → model → mkb

## 🛠️ Utility Scripts

### Crawling Scripts (Bash)
- **`crawl_30_first.sh`** - Cache 30 URLs đầu tiên (để test)
- **`crawl_full.sh`** - Cache toàn bộ important_links.json
- **`crawl_range.sh`** - Cache một khoảng URLs cụ thể

### Monitoring & Verification
- **`check_progress.sh`** - Quick check tiến trình crawl
- **`monitor_auto_crawl.py`** - Monitor chi tiết realtime
- **`verify_cached_links.py`** - Verify links nào đã cache
- **`check_cached_urls.py`** - Check cached URLs

## 📊 Data Files

### Input Data
- **`tree_title.json`** (157K lines) - Tree structure từ website
- **`full_urls_to_crawl.json`** (149K lines) - Toàn bộ URLs
- **`cached_urls.json`** (2.8K lines) - Metadata của cached URLs

### Generated Data
- **`important_links.json`** (16,304 URLs) - Important navigation links
- **`important_links.txt`** (16,305 lines) - Plain text version

## 📖 Documentation

- **`QUICK_START.md`** - Hướng dẫn nhanh bắt đầu
- **`CRAWL_IMPORTANT_LINKS.md`** - Hướng dẫn chi tiết cache important links
- **`RETRY_FEATURE.md`** - Chi tiết về retry feature
- **`README.md`** - README chính của project
- **`PROJECT_STRUCTURE.md`** (file này) - Cấu trúc project

## 📂 Directories

- **`cache/`** - Thư mục chứa cached responses
  - `*.bin` - Binary content của response
  - `*.json` - Metadata (headers, status, url)

## 🗑️ Files Removed (Outdated)

Các file đã bị xóa vì outdate:
- ❌ `cache_important_links.py` - Script cũ
- ❌ `monitor_cache_progress.py` - Monitor cũ
- ❌ `async_crawl.py` - Script cũ
- ❌ `crawl_from_json.py` - Script cũ
- ❌ `test_crawl.py` - Test cũ
- ❌ `warm_ajax.py` - Script cũ
- ❌ `capture_with_playwright.py` - Script cũ
- ❌ `crawl_tree_title.py` - Script cũ
- ❌ `extract_full_link_to_crawl.py` - Script cũ
- ❌ `*.log` files - Log files cũ
- ❌ `not_cached_links.json` - File trung gian
- ❌ `cache_stats.json` - Stats cũ

## 🚀 Typical Workflow

1. **Start Proxy Server:**
   ```bash
   export LIVE_FALLBACK=true
   python3 app.py
   ```

2. **Extract Important Links:**
   ```bash
   python3 extract_important_link_to_crawl.py
   # Generates: important_links.json
   ```

3. **Cache Important Links:**
   ```bash
   ./crawl_30_first.sh    # Test 30 URLs
   # hoặc
   ./crawl_full.sh        # Cache toàn bộ
   ```

4. **Monitor Progress:**
   ```bash
   ./check_progress.sh
   # hoặc
   tail -f cache_important_full.log
   ```

5. **Verify:**
   ```bash
   python3 verify_cached_links.py
   ```

## 📊 Statistics

- **Important Links:** 16,304 URLs
- **Full URLs:** 149,814 URLs
- **Cache Directory:** 98,000+ cached responses
- **Follow Depth:** 3 levels
- **Concurrency:** 5 simultaneous requests
- **Auto Pagination:** Enabled

## 🔧 Configuration

Các biến môi trường:
- `ORIGIN` - Origin URL (default: https://kiagds.ru)
- `LOCAL_BASE` - Local proxy URL (default: http://localhost:5002)
- `CACHE_DIR` - Cache directory (default: cache)
- `LIVE_FALLBACK` - Enable live fallback (default: true)

## 📝 Notes

- Tất cả scripts đều có retry logic với exponential backoff
- Auto crawl có thể extract links từ nhiều nguồn (HTML, JS, onclick, etc.)
- Pagination được detect và crawl tự động
- Cache được shared giữa tất cả các tools

