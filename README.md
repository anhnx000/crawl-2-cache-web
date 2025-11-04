
# kiagds_local_cache

Proxy + cache để duyệt và xem **kiagds.ru** trên **localhost:5002** (online lần đầu để cache, sau đó có thể offline). 
Kèm theo script **warm_ajax.py** để pre-warm các endpoint Ajax (`?mode=...&docId=...`) từ cây menu bạn cung cấp.

> ⚠️ Vui lòng chỉ dùng cho mục đích cá nhân/hợp pháp và tôn trọng robots.txt/ToS của website đích.

## Yêu cầu hệ thống
- **Ubuntu Linux** (không hỗ trợ Windows/macOS)
- **Conda** (Anaconda hoặc Miniconda)
- **uv** (package manager)

## Cấu trúc
```
kiagds_local_cache/
├─ app.py                   # Reverse-proxy + cache (cổng 5002)
├─ warm_ajax.py             # Pre-warm cache cho các endpoint Ajax (?docId=...)
├─ async_crawl.py           # (tuỳ chọn) Crawler async httpx + BeautifulSoup
├─ auto_crawl_proxy.py      # Auto crawler qua proxy, tự động extract và crawl links
├─ crawl_from_json.py        # Helper script để crawl từ file JSON
├─ capture_with_playwright.py # (tuỳ chọn) Ghi mọi GET khi bạn duyệt bằng Playwright
├─ pyproject.toml           # Cấu hình dependencies cho uv
├─ requirements.txt         # (giữ lại cho tương thích)
├─ setup.sh                 # Script tự động thiết lập môi trường
├─ Dockerfile               # (tuỳ chọn) chạy proxy qua Docker
├─ .gitignore
└─ README.md
```
Thư mục **cache/** sẽ được tạo tự động ở lần chạy đầu.

## Cài đặt (Ubuntu Linux với Conda và uv)

### 1. Cài đặt Conda (nếu chưa có)
```bash
# Tải và cài đặt Miniconda
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh
# Sau khi cài, khởi động lại terminal hoặc chạy:
source ~/.bashrc
```

### 2. Cài đặt uv
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc
```

### 3. Thiết lập môi trường Conda và cài đặt dependencies

**Cách 1: Sử dụng script tự động (khuyến nghị)**
```bash
chmod +x setup.sh
./setup.sh
```

**Cách 2: Thiết lập thủ công**
```bash
# Tạo hoặc kích hoạt môi trường conda tên "crawl"
conda create -n crawl python=3.11 -y
conda activate crawl

# Cài đặt dependencies bằng uv
uv pip install -r requirements.txt
# Hoặc sử dụng pyproject.toml:
uv pip install -e .
```

### 4. Kích hoạt môi trường để sử dụng
```bash
conda activate crawl
```

## Chạy proxy (lần đầu online để cache)
```bash
# Đảm bảo đã kích hoạt môi trường conda
conda activate crawl

export LIVE_FALLBACK=true
python app.py
# Mở trình duyệt: http://localhost:5002/
# Ví dụ URL gốc (giữ nguyên tham số):
# http://localhost:5002/?mode=ETM&marke=KM&year=2026&model=9193&mkb=447__29696&docId=435525
```

## Chạy OFFLINE
Sau khi đã cache đủ:
```bash
# Đảm bảo đã kích hoạt môi trường conda
conda activate crawl

export LIVE_FALLBACK=false
python app.py
```

## Pre-warm Ajax theo cây menu
1) Lưu HTML/đoạn menu có chứa `docId` vào **menu.txt** (ví dụ bạn đã gửi).
2) Chạy:
```bash
# Đảm bảo đã kích hoạt môi trường conda
conda activate crawl

# proxy đang chạy ở terminal khác (LIVE_FALLBACK=true)
python warm_ajax.py --html menu.txt   --marke KM --year 2026 --model 9193 --mkb 447__29696   --start-page 1 --end-page 1
```
Tăng `--end-page` nếu endpoint có phân trang `&page=`.

## Auto Crawler - Tự động crawl và cache toàn bộ trang web

Script `auto_crawl_proxy.py` tự động crawl qua proxy, extract các links từ HTML và crawl tiếp để tạo bản mirror đầy đủ.

### Yêu cầu:
- Proxy phải đang chạy với `LIVE_FALLBACK=true` (terminal khác)
- Script sẽ tự động kiểm tra proxy trước khi bắt đầu crawl

### Cách sử dụng:

**1. Crawl từ trang chủ và tự động follow tất cả links:**
```bash
conda activate crawl
python auto_crawl_proxy.py --follow-depth 3 --concurrency 4 --delay 0.5
```

**2. Crawl từ seed URL cụ thể với pagination:**
```bash
conda activate crawl
python auto_crawl_proxy.py \
  --seed "https://kiagds.ru/?mode=ETM&marke=KM&year=2026&model=9193&mkb=447__29696&docId=435525&page=" \
  --start-page 1 \
  --end-page 50 \
  --follow-depth 2 \
  --concurrency 4 \
  --delay 0.5
```

**3. Crawl với nhiều URL bổ sung:**
```bash
conda activate crawl
python auto_crawl_proxy.py \
  --extra-urls "https://kiagds.ru/page1" "https://kiagds.ru/page2" \
  --follow-depth 5 \
  --concurrency 6 \
  --delay 0.3 \
  --verbose
```

**4. Crawl từ file JSON (khuyến nghị cho số lượng lớn):**
```bash
conda activate crawl

# Cách 1: Sử dụng auto_crawl_proxy.py trực tiếp (đơn giản)
# Crawl tất cả URLs từ file JSON
python auto_crawl_proxy.py \
  --json-file full_urls_to_crawl.json \
  --follow-depth 2 \
  --concurrency 4 \
  --delay 0.5

# Crawl một phần URLs (từ index 0 đến 1000)
python auto_crawl_proxy.py \
  --json-file full_urls_to_crawl.json \
  --json-start-index 0 \
  --json-end-index 1000 \
  --follow-depth 2 \
  --concurrency 4 \
  --delay 0.5 \
  --verbose

# Cách 2: Sử dụng crawl_from_json.py (chia thành batches)
# Xem URLs sẽ crawl (dry-run)
python crawl_from_json.py full_urls_to_crawl.json --dry-run

# Crawl tất cả URLs (chia thành batches)
python crawl_from_json.py full_urls_to_crawl.json \
  --batch-size 100 \
  --follow-depth 2 \
  --concurrency 4 \
  --delay 0.5

# Crawl một phần URLs (từ index 0 đến 1000)
python crawl_from_json.py full_urls_to_crawl.json \
  --start-index 0 \
  --end-index 1000 \
  --batch-size 50 \
  --verbose
```

### Các tham số:

#### `auto_crawl_proxy.py`:
- `--seed`: URL seed có phần `&page=` để crawl nhiều trang
- `--start-page`, `--end-page`: Phạm vi trang để crawl (nếu seed có pagination)
- `--extra-urls`: Danh sách URL bổ sung để crawl
- `--json-file`: Đường dẫn file JSON chứa danh sách URLs để crawl (khuyến nghị cho số lượng lớn)
- `--json-start-index`: Chỉ số bắt đầu khi đọc từ JSON (mặc định: 0)
- `--json-end-index`: Chỉ số kết thúc khi đọc từ JSON (mặc định: tất cả)
- `--follow-depth`: Độ sâu crawl links (0 = chỉ seeds, >0 = tự động crawl links trong HTML, mặc định: 3)
- `--concurrency`: Số lượng request đồng thời (mặc định: 4)
- `--delay`: Giãn cách giữa các request - giây (mặc định: 0.5)
- `--verbose`: Hiển thị chi tiết (cached URLs và links found)
- `--auto-pagination`: Tự động phát hiện và crawl pagination (mặc định: True)
- `--proxy-base`: URL proxy base nếu khác mặc định (mặc định: http://localhost:5002)
- `--max-retries`: Số lần retry khi gặp lỗi network/timeout (mặc định: 10)

#### `crawl_from_json.py`:
- `json_file`: Đường dẫn file JSON chứa danh sách URLs (required)
- `--batch-size`: Số lượng URLs crawl mỗi lần (mặc định: 100)
- `--start-index`: Chỉ số bắt đầu (mặc định: 0)
- `--end-index`: Chỉ số kết thúc (mặc định: tất cả)
- `--follow-depth`: Độ sâu crawl links (mặc định: 2)
- `--concurrency`: Số lượng request đồng thời (mặc định: 4)
- `--delay`: Giãn cách giữa các request - giây (mặc định: 0.5)
- `--verbose`: Hiển thị chi tiết
- `--dry-run`: Chỉ hiển thị URLs sẽ crawl, không thực sự crawl

### Tính năng chính:

#### 🔍 Tự động phát hiện Pagination:
- **"Page X of Y"**: Tự động phát hiện pattern "Page 1 of 17" và crawl tất cả 17 trang
- **Pagination links**: Phát hiện các số trang trong onclick handlers (ví dụ: `ajaxHref('?page=1')`) và crawl tất cả
- Tự động giữ nguyên các query parameters khác khi tạo URLs pagination

#### 🔗 Extract Links thông minh:
- Extract từ HTML tags: `<a>`, `<link>`, `<script>`, `<img>`, `<iframe>`, `<form>`
- Extract từ JavaScript: Tìm URLs trong code JavaScript
- Extract từ onclick handlers: Phát hiện `ajaxHref()`, `location.href`, etc.
- Extract từ data-* attributes: Tìm URLs trong các thuộc tính data-*

#### ✨ Tự động làm sạch URL:
- Loại bỏ `&page=` rỗng ở cuối URL
- Chuẩn hóa query parameters
- Loại bỏ fragment (#)

#### 🛡️ Error Handling & Retry:
- Tự động kiểm tra proxy trước khi crawl
- Hiển thị thông tin proxy (cached responses, live_fallback)
- Dừng ngay nếu proxy không chạy với thông báo rõ ràng
- Bỏ qua URLs đã cache để tránh crawl lại
- **Auto retry với exponential backoff**: Tự động retry tối đa 10 lần (có thể tùy chỉnh) khi gặp lỗi network/timeout
- Exponential backoff: 1s, 2s, 4s, 8s, max 10s giữa các lần retry
- Không retry nếu proxy không chạy (fail fast)
- Log chi tiết quá trình retry để debug
- Xử lý lỗi tốt, không crash khi một số trang có vấn đề

#### 📊 Thống kê và Progress:
- Hiển thị số URLs đã cache sẵn
- Hiển thị số URLs mới crawl
- Hiển thị số lỗi
- Hiển thị tổng số URLs đã xử lý
- Thông báo khi phát hiện pagination

### Ví dụ Output:
```
🔍 Kiểm tra proxy http://localhost:5002...
✅ Proxy đang chạy
   - Cached responses: 97
   - Live fallback: true

📋 Seed URLs: 1
   - https://kiagds.ru/?mode=ETM&marke=KM&year=2026&model=9193&mkb=447__29696&docId=435662

✅ [200] https://kiagds.ru/?mode=ETM&marke=KM&year=2026&model=9193&mkb=447__29696&docId=435662 (depth=0)
  📄 Phát hiện pagination: page_of, max_page=17
  📄 Đã thêm 17 trang pagination vào queue
  🔗 Found 124 new links (total: 125)

✅ [200] https://kiagds.ru/?mode=ETM&marke=KM&year=2026&model=9193&mkb=447__29696&docId=435662&page=1 (depth=0)
...

============================================================
✅ Hoàn thành crawl!
   - Đã cache sẵn: 0 URLs
   - Mới crawl: 150 URLs
   - Lỗi: 0 URLs
   - Tổng URLs đã xử lý: 150 URLs
============================================================
```

## (Tuỳ chọn) Crawler async (crawl trực tiếp từ origin)
```bash
# Đảm bảo đã kích hoạt môi trường conda
conda activate crawl

python async_crawl.py   --seed "https://kiagds.ru/?mode=ETM&marke=KM&year=2026&model=9193&mkb=447__29696&docId=435525&page="   --start-page 1 --end-page 50 --follow-depth 0
```

## (Tuỳ chọn) Capture bằng Playwright
> Playwright **không** nằm trong requirements mặc định. Nếu muốn dùng:
```bash
# Đảm bảo đã kích hoạt môi trường conda
conda activate crawl

# Cài đặt playwright bằng uv
uv pip install playwright
playwright install
python capture_with_playwright.py "https://kiagds.ru/?mode=ETM&marke=KM&year=2026&model=9193&mkb=447__29696&docId=435525"
```

## Docker (tuỳ chọn, cho app.py)
> Dockerfile đã được cập nhật để sử dụng Ubuntu và conda/uv:
```bash
docker build -t kiagds-cache .
docker run --rm -p 5002:5002 -e LIVE_FALLBACK=true kiagds-cache
```

## Biến môi trường
- `LIVE_FALLBACK=true|false` — Cho phép proxy gọi origin khi cache miss (true) hay chỉ phục vụ offline (false). Mặc định **true**.

## Format File JSON cho crawl_from_json.py

File JSON có thể có các format sau:

**Format 1: Object với array urls**
```json
{
  "total_urls": 12484,
  "urls": [
    {"url": "https://kiagds.ru/?mode=ETM&..."},
    {"url": "https://kiagds.ru/?mode=ETM&..."}
  ]
}
```

**Format 2: Array trực tiếp**
```json
[
  {"url": "https://kiagds.ru/?mode=ETM&..."},
  {"url": "https://kiagds.ru/?mode=ETM&..."}
]
```

**Format 3: Array URLs đơn giản**
```json
[
  "https://kiagds.ru/?mode=ETM&...",
  "https://kiagds.ru/?mode=ETM&..."
]
```

## Troubleshooting

### Lỗi "Connection refused" hoặc "All connection attempts failed"
**Nguyên nhân**: Proxy không chạy hoặc không thể kết nối tới proxy.

**Giải pháp**:
1. Kiểm tra proxy có đang chạy:
   ```bash
   curl http://localhost:5002/_cache_stats
   ```
2. Nếu không chạy, khởi động proxy:
   ```bash
   conda activate crawl
   export LIVE_FALLBACK=true
   conda run -n crawl python app.py
   ```

### Lỗi "Proxy không thể kết nối"
**Nguyên nhân**: Proxy chưa được khởi động hoặc đang chạy ở cổng khác.

**Giải pháp**:
- Đảm bảo proxy đang chạy ở cổng 5002
- Nếu proxy chạy ở cổng khác, sử dụng `--proxy-base http://localhost:<PORT>`

### URLs có `&page=` rỗng bị lỗi
**Nguyên nhân**: URL có parameter `page` rỗng (ví dụ: `&page=`).

**Giải pháp**: Script tự động xử lý và loại bỏ parameter rỗng. Nếu vẫn lỗi, kiểm tra URL format.

### Crawl chậm hoặc bị timeout
**Giải pháp**:
- Tăng `--delay` để giảm tải (ví dụ: `--delay 1.0`)
- Giảm `--concurrency` (ví dụ: `--concurrency 2`)
- Kiểm tra kết nối mạng và tốc độ của origin server

### Pagination không được phát hiện
**Nguyên nhân**: Pagination có format khác hoặc không có trong HTML.

**Giải pháp**:
- Kiểm tra HTML của trang để xem format pagination
- Sử dụng `--verbose` để xem chi tiết
- Nếu cần, sử dụng `--seed` với `--start-page` và `--end-page` để crawl thủ công

## Best Practices

1. **Luôn chạy proxy với `LIVE_FALLBACK=true` khi crawl** để đảm bảo cache được tạo.

2. **Sử dụng delay hợp lý** (0.5-1.0 giây) để tránh quá tải server.

3. **Chia nhỏ khi crawl số lượng lớn URLs**:
   - Sử dụng `crawl_from_json.py` với `--batch-size`
   - Crawl từng phần với `--start-index` và `--end-index`

4. **Kiểm tra cache trước khi crawl lại**:
   - Script tự động bỏ qua URLs đã cache
   - Kiểm tra số lượng cached: `curl http://localhost:5002/_cache_stats`

5. **Sử dụng `--verbose` khi debug** để xem chi tiết quá trình crawl.

6. **Lưu ý về pagination**:
   - Auto pagination detection hoạt động tốt với format chuẩn
   - Nếu không phát hiện được, sử dụng `--seed` với `--start-page` và `--end-page`

## Lưu ý
- Chỉ **GET** được cache. Nếu trang có POST, đăng nhập, captcha… thì offline không tái tạo đầy đủ các phần đó.
- Proxy có **rewrite** URL tuyệt đối `https://kiagds.ru` và cả dạng `//kiagds.ru` về `http://localhost:5002` trong HTML/JS/CSS.
- Throttle/giãn cách khi warm để lịch sự với website đích.
- **Auto pagination** chỉ hoạt động khi phát hiện được pattern "Page X of Y" hoặc pagination links trong HTML.
- URLs có `&page=` rỗng sẽ được tự động làm sạch.
# crawl-2-cache-web
