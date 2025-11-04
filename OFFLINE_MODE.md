# 🔌 Offline Mode - Hướng dẫn sử dụng

## 📖 Tổng quan

Proxy hỗ trợ 2 chế độ:

### 🌐 Online Mode (LIVE_FALLBACK=true)
- Ưu tiên dùng cache
- Nếu cache miss → fetch từ internet và lưu cache
- **Dùng khi:** Đang crawl/cache dữ liệu

### 🔌 Offline Mode (LIVE_FALLBACK=false)
- **CHỈ** dùng cache
- Nếu cache miss → trả về lỗi 404
- **Dùng khi:** Browse offline, không cần internet

---

## 🚀 Cách sử dụng

### Option 1: Dùng scripts có sẵn (Khuyến nghị)

#### Chế độ Offline (chỉ cache):
```bash
./start_offline.sh
```

#### Chế độ Online (cache + internet):
```bash
./start_online.sh
```

---

### Option 2: Chạy thủ công

#### Chế độ Offline:
```bash
cd /home/xuananh/work_1/anhnx/crawl-2
export LIVE_FALLBACK=false
python3 app.py
```

#### Chế độ Online:
```bash
cd /home/xuananh/work_1/anhnx/crawl-2
export LIVE_FALLBACK=true
python3 app.py
```

---

## 🧪 Test Offline Mode

### Kiểm tra proxy có đang chạy:
```bash
curl http://localhost:5002/_cache_stats
```

### Test URLs đã cache:
```bash
./test_offline.sh
```

hoặc thủ công:
```bash
curl http://localhost:5002/?mode=ETM&marke=KM
```

---

## 🌐 Browse trong Browser

### Mở browser và truy cập:
```
http://localhost:5002
```

### Một số URLs để thử:
```
http://localhost:5002/?mode=ETM
http://localhost:5002/?mode=ETM&marke=KM
http://localhost:5002/?mode=ETM&marke=KM&year=2026
http://localhost:5002/?mode=ETM&marke=KM&year=2026&model=9923
http://localhost:5002/?mode=ETM&marke=KM&year=2026&model=9923&mkb=445__29519
```

---

## 📊 Kiểm tra Cache Stats

### Xem số lượng URLs đã cache:
```bash
curl -s http://localhost:5002/_cache_stats | python3 -m json.tool
```

Output mẫu:
```json
{
  "cached_responses": 98987,
  "live_fallback": false,
  "origin": "https://kiagds.ru"
}
```

### Đếm file cache:
```bash
find cache -name "*.bin" | wc -l
```

---

## ⚠️ Lưu ý quan trọng

### Ở chế độ Offline:
- ✅ URLs đã cache → Hoạt động bình thường
- ❌ URLs chưa cache → Lỗi 404 "Offline cache miss"
- ✅ Tất cả links, CSS, JS, images đều được rewrite về localhost:5002
- ✅ Browse như trang web bình thường (nếu đã cache đủ)

### Kiểm tra xem URL đã cache chưa:
```bash
python3 verify_cached_links.py
```

---

## 🎯 Workflow khuyến nghị

### 1. Cache dữ liệu (Online Mode):
```bash
# Terminal 1: Chạy proxy online
./start_online.sh

# Terminal 2: Cache important links
./crawl_full.sh

# Đợi crawl hoàn thành (8-15 giờ)
```

### 2. Browse offline:
```bash
# Dừng proxy online (Ctrl+C)

# Chạy proxy offline
./start_offline.sh

# Mở browser: http://localhost:5002
```

---

## 🔍 Debug

### URL không load được:
1. Kiểm tra URL đã cache chưa:
   ```bash
   python3 verify_cached_links.py
   ```

2. Xem log của proxy (terminal đang chạy app.py)

3. Test bằng curl:
   ```bash
   curl -v http://localhost:5002/?mode=ETM&marke=KM
   ```

### Cache miss:
- **Giải pháp 1:** Chạy lại ở online mode để cache URL đó
- **Giải pháp 2:** Crawl lại với depth cao hơn để cache đủ links

---

## 📈 Monitoring

### Xem realtime requests:
- Log hiển thị ở terminal đang chạy `app.py`
- Format: `[GET] URL -> status`

### Check cache size:
```bash
du -sh cache/
```

### Count cached URLs:
```bash
echo "Total cached responses: $(find cache -name '*.bin' | wc -l)"
```

---

## 💡 Tips

1. **Cache đầy đủ trước khi dùng offline:**
   - Chạy `./crawl_full.sh` với depth=3
   - Verify với `python3 verify_cached_links.py`

2. **Tách máy chạy crawl và browse:**
   - Máy A: Chạy online mode + crawl
   - Máy B: Copy cache folder → chạy offline mode

3. **Backup cache:**
   ```bash
   tar -czf cache_backup.tar.gz cache/
   ```

4. **Restore cache:**
   ```bash
   tar -xzf cache_backup.tar.gz
   ```

---

## 🎉 Kết quả

Sau khi cache đầy đủ, bạn có thể:
- ✅ Browse toàn bộ website offline
- ✅ Không cần internet
- ✅ Tốc độ load nhanh (từ cache local)
- ✅ Tất cả links, navigation hoạt động bình thường

