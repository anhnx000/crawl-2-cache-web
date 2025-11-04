# Hướng dẫn Cache Important Links

## 🎯 Tổng quan

File `important_links.json` chứa **16,304 important links** cần cache.

## 📋 Các bước thực hiện

### Bước 1: Đảm bảo Proxy đang chạy

Mở terminal mới và chạy proxy:

```bash
cd /home/xuananh/work_1/anhnx/crawl-2
export LIVE_FALLBACK=true
python3 app.py
```

Proxy sẽ chạy tại `http://localhost:5002`

---

### Bước 2A: Test với 30 URLs đầu tiên (Khuyến nghị)

**Chạy lệnh này để test trước:**

```bash
cd /home/xuananh/work_1/anhnx/crawl-2

python3 auto_crawl_proxy.py \
  --json-file important_links.json \
  --json-start-index 0 \
  --json-end-index 30 \
  --follow-depth 3 \
  --concurrency 5 \
  --delay 0.3 \
  --max-retries 10 \
  --auto-pagination \
  --verbose
```

**Giải thích tham số:**
- `--json-file important_links.json` - File chứa danh sách URLs
- `--json-start-index 0` - Bắt đầu từ URL thứ 0
- `--json-end-index 30` - Kết thúc tại URL thứ 30 (crawl 30 URLs đầu)
- `--follow-depth 3` - Tự động crawl links tìm được với độ sâu 3 tầng
- `--concurrency 5` - Crawl 5 URLs đồng thời
- `--delay 0.3` - Giãn cách 0.3s giữa các request
- `--max-retries 10` - Retry tối đa 10 lần nếu gặp lỗi
- `--auto-pagination` - Tự động phát hiện và crawl tất cả các trang
- `--verbose` - Hiển thị chi tiết

**Kết quả mong đợi:**
- Sẽ cache 30 important links ban đầu
- Tự động extract và cache thêm các links liên quan (depth 1, 2, 3)
- Tổng số URLs được cache có thể là 100-500+ URLs

---

### Bước 2B: Cache FULL toàn bộ 16,304 important links

**Sau khi test thành công, chạy lệnh này để cache toàn bộ:**

```bash
cd /home/xuananh/work_1/anhnx/crawl-2

nohup python3 auto_crawl_proxy.py \
  --json-file important_links.json \
  --follow-depth 3 \
  --concurrency 5 \
  --delay 0.3 \
  --max-retries 10 \
  --auto-pagination \
  > cache_important_full.log 2>&1 &
```

**Lưu ý:**
- Không có `--json-end-index` → crawl tất cả
- Chạy ở background với `nohup` và `&`
- Log được ghi vào `cache_important_full.log`

---

### Bước 3: Theo dõi tiến trình

**Kiểm tra nhanh:**
```bash
./check_progress.sh
```

**Xem log realtime:**
```bash
tail -f cache_important_full.log
```

**Kiểm tra process:**
```bash
ps aux | grep auto_crawl_proxy.py
```

**Đếm URLs đã cache:**
```bash
grep -c "✅ \[200\]" cache_important_full.log
```

---

## ⏱️ Ước tính thời gian

- **30 URLs đầu:** ~2-5 phút
- **Toàn bộ 16,304 URLs:** ~8-15 giờ (tùy độ sâu và số links tìm được)

Với depth=3 và auto-pagination, tổng số URLs thực tế sẽ cao hơn rất nhiều (có thể 50,000-100,000+ URLs).

---

## 🛠️ Các lệnh hữu ích

### Dừng crawling
```bash
pkill -f auto_crawl_proxy.py
```

### Resume từ index cụ thể (nếu bị gián đoạn)
```bash
# Ví dụ: tiếp tục từ URL thứ 1000
python3 auto_crawl_proxy.py \
  --json-file important_links.json \
  --json-start-index 1000 \
  --follow-depth 3 \
  --concurrency 5 \
  --delay 0.3
```

### Verify đã cache bao nhiêu important links
```bash
python3 verify_cached_links.py
```

---

## 📊 Hiểu về Follow Depth

**Depth = 0:** Chỉ cache các URLs trong important_links.json

**Depth = 1:** Cache important links + tất cả links tìm được từ trang đó

**Depth = 2:** Cache depth 1 + tất cả links từ các trang depth 1

**Depth = 3:** Cache depth 2 + tất cả links từ các trang depth 2

**Khuyến nghị:** Depth 3 để cache đầy đủ toàn bộ trang web

---

## 🎯 Kết quả cuối cùng

Sau khi hoàn thành, bạn sẽ có:
- ✅ Tất cả 16,304 important links được cache
- ✅ Tất cả links liên quan (documents, pagination, sub-pages) được cache
- ✅ Toàn bộ trang web có thể browse offline qua proxy

