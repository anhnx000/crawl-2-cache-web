# 🔌 Offline Viewer - Port 5003

## 📖 Tổng quan

Proxy offline viewer ở **port 5003** cho phép bạn:
- ✅ Browse website offline trong khi crawl đang chạy ở port 5002
- ✅ **Không ảnh hưởng** đến quá trình crawl
- ✅ Dùng chung cache directory với crawl process
- ✅ Chỉ hiển thị URLs đã cache (offline only, read-only)
- ✅ URLs được rewrite về port 5003 tự động

## 🎯 Use Cases

1. **Browse trong khi crawl:** Xem kết quả đã cache trong khi crawl vẫn chạy
2. **Test offline:** Verify cache hoạt động đúng
3. **Development:** Test UI/UX mà không ảnh hưởng crawl
4. **Performance:** So sánh tốc độ offline vs online

## 🚀 Cách sử dụng

### Bước 1: Chạy offline viewer

```bash
cd /home/xuananh/work_1/anhnx/crawl-2
./start_offline_viewer.sh
```

### Bước 2: Mở browser

Truy cập: **http://localhost:5003**

### Bước 3: Test

```bash
./test_offline_viewer.sh
```

## 📊 So sánh Port 5002 vs 5003

| Feature | Port 5002 (Crawl) | Port 5003 (Viewer) |
|---------|-------------------|-------------------|
| **Mode** | Online | Offline |
| **LIVE_FALLBACK** | true | false (hardcode) |
| **Cache** | Read + Write | Read Only |
| **Internet** | Có (fetch khi cache miss) | Không (chỉ cache) |
| **Session** | Có (requests.Session) | Không |
| **Ảnh hưởng crawl** | Active crawling | Không ảnh hưởng |
| **URLs chưa cache** | Fetch từ internet | 404 |
| **URL Rewrite** | localhost:5002 | localhost:5003 |
| **Cache dir** | cache/ | cache/ (chung) |

## ⚠️ Lưu ý quan trọng

### Ở chế độ Offline Viewer (Port 5003):

1. **Read-only:** Chỉ đọc cache, không bao giờ ghi đè
2. **No internet:** Không fetch từ internet, không có session
3. **Cache miss:** URLs chưa cache sẽ hiển thị 404
4. **URL rewrite:** Tất cả URLs được rewrite về port 5003
5. **Không ảnh hưởng crawl:** Crawl process ở port 5002 vẫn chạy bình thường

### Kiểm tra xem URL đã cache chưa:

```bash
python3 verify_cached_links.py
```

## 🔍 Kiểm tra

### Cache stats:

```bash
# Port 5003
curl http://localhost:5003/_cache_stats | python3 -m json.tool

# Port 5002 (so sánh)
curl http://localhost:5002/_cache_stats | python3 -m json.tool
```

### Test URLs:

```bash
# Test cached URLs
curl http://localhost:5003/?mode=ETM&marke=KM

# Test uncached URLs (sẽ 404)
curl http://localhost:5003/?mode=ETM&marke=INVALID
```

### Đếm file cache:

```bash
find cache -name "*.bin" | wc -l
```

## 🛑 Dừng

```bash
pkill -f app_offline_viewer.py
```

## 💡 Workflow khuyến nghị

### 1. Crawl dữ liệu (Port 5002):

```bash
# Terminal 1: Chạy proxy online
./start_online.sh

# Terminal 2: Cache important links
./crawl_full.sh
```

### 2. Browse offline (Port 5003):

```bash
# Terminal 3: Chạy offline viewer (KHÔNG ảnh hưởng crawl)
./start_offline_viewer.sh

# Browser: http://localhost:5003
```

### 3. Monitor cả 2:

```bash
# Terminal 4: Monitor crawl
tail -f cache_important_full.log

# Terminal 5: Test viewer
./test_offline_viewer.sh
```

## 🔧 Technical Details

### Code Structure:

- **File:** `app_offline_viewer.py`
- **Port:** 5003 (hardcode)
- **LIVE_FALLBACK:** False (hardcode, không cho phép đổi)
- **Session:** Không có (vì không fetch từ internet)
- **Cache:** Read-only, dùng chung với crawl process

### URL Rewrite Logic:

1. `https://kiagds.ru/...` → `http://localhost:5003/...`
2. `//kiagds.ru/...` → `//localhost:5003/...`
3. `http://localhost:5002/...` → `http://localhost:5003/...` (nếu có trong cache)

### Cache Sharing:

- Cả 2 ports dùng chung `CACHE_DIR` (mặc định: `cache/`)
- Port 5002: Ghi cache mới khi crawl
- Port 5003: Chỉ đọc cache, không ghi

## 🆘 Troubleshooting

### URL không load được (404):

1. Kiểm tra URL đã cache chưa:
   ```bash
   python3 verify_cached_links.py
   ```

2. Xem log của viewer (terminal đang chạy)

3. Test bằng curl:
   ```bash
   curl -v http://localhost:5003/?mode=ETM&marke=KM
   ```

### Port 5003 không chạy:

```bash
# Check port
lsof -i :5003

# Kill process cũ
pkill -f app_offline_viewer.py

# Chạy lại
./start_offline_viewer.sh
```

### Cache không được share:

- Verify cả 2 ports dùng cùng `CACHE_DIR`
- Check environment variables:
  ```bash
  echo $CACHE_DIR
  ```

## 📈 Performance

### Tốc độ:

- **Offline viewer:** Rất nhanh (chỉ đọc từ disk)
- **Online proxy:** Chậm hơn (có thể fetch từ internet)

### Memory:

- **Port 5002:** Cần session, memory cao hơn
- **Port 5003:** Không session, memory thấp hơn

## ✅ Checklist

- [x] Port 5003 không conflict với 5002
- [x] Read-only (không ghi cache)
- [x] Dùng chung cache directory
- [x] URLs rewrite về port 5003
- [x] Không ảnh hưởng crawl process
- [x] Hardcode LIVE_FALLBACK=False
- [x] Không có session

## 📚 Tài liệu liên quan

- `OFFLINE_MODE.md` - Hướng dẫn offline mode (port 5002)
- `START_HERE.md` - Hướng dẫn crawl
- `QUICK_REFERENCE.md` - Command reference
- `PROJECT_STRUCTURE.md` - Cấu trúc project

---

**Bắt đầu ngay: `./start_offline_viewer.sh`** 🚀

