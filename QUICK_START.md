# 🚀 Quick Start - Cache Important Links

## Bước 1: Chạy Proxy (Terminal 1)

```bash
cd /home/xuananh/work_1/anhnx/crawl-2
export LIVE_FALLBACK=true
python3 app.py
```

Giữ terminal này chạy!

---

## Bước 2: Chọn cách cache (Terminal 2)

### Option A: Test 30 URLs đầu tiên (⚡ Nhanh - 2 phút)

```bash
cd /home/xuananh/work_1/anhnx/crawl-2
./crawl_30_first.sh
```

### Option B: Cache FULL 16,304 URLs (🐌 Lâu - 8-15 giờ)

```bash
cd /home/xuananh/work_1/anhnx/crawl-2
./crawl_full.sh
```

### Option C: Cache một khoảng cụ thể

```bash
cd /home/xuananh/work_1/anhnx/crawl-2
./crawl_range.sh 0 100        # Cache URLs 0-100
./crawl_range.sh 1000 2000    # Cache URLs 1000-2000
```

---

## Bước 3: Theo dõi tiến trình

### Kiểm tra nhanh
```bash
./check_progress.sh
```

### Xem log realtime
```bash
tail -f cache_important_full.log
```

### Verify đã cache bao nhiêu important links
```bash
python3 verify_cached_links.py
```

---

## ⚡ Quick Commands

**Dừng crawl:**
```bash
pkill -f auto_crawl_proxy.py
```

**Kiểm tra process:**
```bash
ps aux | grep auto_crawl_proxy.py
```

**Đếm số URLs đã cache:**
```bash
find cache -name "*.bin" | wc -l
```

---

## 📊 Thông tin

- **File nguồn:** `important_links.json`
- **Tổng URLs:** 16,304
- **Follow depth:** 3 (tự động crawl links liên quan)
- **Auto pagination:** Có (tự động crawl tất cả các trang)
- **Concurrency:** 5 requests đồng thời
- **Delay:** 0.3s giữa các requests
- **Max retries:** 10 lần

---

## 🎯 Kết quả

Sau khi hoàn thành:
- ✅ Tất cả 16,304 important links được cache
- ✅ Tất cả links liên quan (với depth 3) được cache
- ✅ Website có thể browse offline hoàn toàn

**Tổng số URLs thực tế sẽ cao hơn nhiều (50,000-100,000+ URLs)**

