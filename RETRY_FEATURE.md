# Retry Feature - Tự động retry khi gặp lỗi

## Tính năng đã thêm

Đã thêm tính năng **auto retry với exponential backoff** vào `auto_crawl_proxy.py` để tự động retry khi gặp lỗi network/timeout, tránh tình trạng thiếu cache do lỗi tạm thời.

## Các thay đổi

### 1. Function `fetch_via_proxy_with_retry()`

Thêm function mới để wrap `fetch_via_proxy()` với retry logic:

```python
async def fetch_via_proxy_with_retry(
    client: httpx.AsyncClient, 
    url: str, 
    proxy_base: str, 
    max_retries: int = 10, 
    verbose: bool = False
):
    """Fetch URL qua proxy với retry logic"""
```

**Tính năng:**
- ✅ Retry tối đa `max_retries` lần (mặc định: 10)
- ✅ Exponential backoff: 1s, 2s, 4s, 8s, max 10s
- ✅ Không retry nếu proxy không chạy (fail fast)
- ✅ Log chi tiết khi retry (từ lần thử thứ 3 hoặc khi verbose=True)
- ✅ Log thành công nếu retry thành công

### 2. Tham số CLI mới: `--max-retries`

```bash
--max-retries MAX_RETRIES
    Số lần retry khi gặp lỗi (mặc định: 10)
```

### 3. Cập nhật worker function

Worker function trong `crawl()` đã được cập nhật để sử dụng `fetch_via_proxy_with_retry()` thay vì `fetch_via_proxy()`.

## Cách sử dụng

### Sử dụng với giá trị mặc định (10 retries):

```bash
python auto_crawl_proxy.py --extra-urls "https://example.com/page"
```

### Tùy chỉnh số lần retry:

```bash
# Retry 5 lần
python auto_crawl_proxy.py --extra-urls "https://example.com/page" --max-retries 5

# Retry 20 lần (cho mạng không ổn định)
python auto_crawl_proxy.py --extra-urls "https://example.com/page" --max-retries 20

# Không retry (0 lần)
python auto_crawl_proxy.py --extra-urls "https://example.com/page" --max-retries 1
```

### Xem log chi tiết retry:

```bash
python auto_crawl_proxy.py --extra-urls "https://example.com/page" --verbose
```

## Ví dụ Output

### Khi retry thành công:

```
⚠️  Lần thử 1/10 thất bại: https://kiagds.ru/?mode=ETM&...
     Lỗi: TimeoutException: Request timeout
     Đợi 1s trước khi retry...
⚠️  Lần thử 2/10 thất bại: https://kiagds.ru/?mode=ETM&...
     Lỗi: TimeoutException: Request timeout
     Đợi 2s trước khi retry...
✅ Retry thành công sau 3 lần thử: https://kiagds.ru/?mode=ETM&...
✅ [200] https://kiagds.ru/?mode=ETM&... (depth=0)
```

### Khi hết retry:

```
⚠️  Lần thử 8/10 thất bại: https://kiagds.ru/?mode=ETM&...
     Lỗi: TimeoutException: Request timeout
     Đợi 8s trước khi retry...
⚠️  Lần thử 9/10 thất bại: https://kiagds.ru/?mode=ETM&...
     Lỗi: TimeoutException: Request timeout
     Đợi 10s trước khi retry...
❌ Đã retry 10 lần nhưng vẫn thất bại: https://kiagds.ru/?mode=ETM&...
❌ [ERROR] https://kiagds.ru/?mode=ETM&...: TimeoutException
```

## Exponential Backoff

Thời gian chờ giữa các lần retry:

| Lần thử | Delay  |
|---------|--------|
| 1       | 1s     |
| 2       | 2s     |
| 3       | 4s     |
| 4       | 8s     |
| 5+      | 10s    |

Formula: `min(2^attempt, 10)` seconds

## Lợi ích

✅ **Giảm thiểu cache miss**: Tự động retry khi gặp lỗi tạm thời
✅ **Xử lý timeout**: Không bỏ lỡ trang do timeout ngắn hạn
✅ **Giảm lỗi network**: Retry khi có vấn đề mạng tạm thời
✅ **Fail fast**: Không retry khi proxy không chạy (tiết kiệm thời gian)
✅ **Configurable**: Có thể tùy chỉnh số lần retry theo nhu cầu
✅ **Transparent**: Log rõ ràng quá trình retry

## Các trường hợp không retry

- ❌ Proxy không chạy (ConnectError với message "Không thể kết nối tới proxy")
- Trong trường hợp này, script sẽ fail fast để thông báo cho user

## Testing

### Test với page 13 bị thiếu cache:

```bash
# Đảm bảo proxy đang chạy với LIVE_FALLBACK=true
export LIVE_FALLBACK=true
python app.py

# Trong terminal khác, crawl page 13
python auto_crawl_proxy.py \
  --extra-urls "https://kiagds.ru/?mode=ETM&marke=KM&year=2026&model=9193&mkb=447__29696&docId=435571&page=13" \
  --follow-depth 0 \
  --max-retries 10 \
  --verbose
```

### Kiểm tra kết quả:

```bash
python check_cached_urls.py
```

## Best Practices

1. **Sử dụng giá trị mặc định (10 retries)** cho hầu hết trường hợp
2. **Tăng retries (15-20)** nếu mạng không ổn định
3. **Giảm retries (3-5)** khi test hoặc debug
4. **Bật --verbose** khi cần debug chi tiết
5. **Kết hợp với --delay** phù hợp để không overload server

## Tương thích

✅ Tương thích ngược với code cũ
✅ Không ảnh hưởng đến các tham số khác
✅ Có thể disable bằng cách set `--max-retries 1`

