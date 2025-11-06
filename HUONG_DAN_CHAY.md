# 📖 Hướng Dẫn Chạy Project - Cache và View Web

## 🎯 Mục đích
- **Cache** toàn bộ website kiagds.ru vào local
- **View** website đã cache ở `http://localhost:5002`
- Hoạt động **offline** sau khi cache xong

---

## 🚀 QUY TRÌNH CHẠY (3 bước đơn giản)

### BƯỚC 1: Khởi động Proxy (Terminal 1)

```bash
cd /home/xuananh/work_1/anhnx/crawl-2
./start_online.sh
```

**Giữ terminal này chạy!** Proxy sẽ chạy tại `http://localhost:5002`

✅ Proxy đang chạy khi thấy:
```
🌐 Starting Proxy in ONLINE Mode
Mode: ONLINE (cache + live fallback)
URL: http://localhost:5002
```

---

### BƯỚC 2: Cache dữ liệu (Terminal 2 - MỚI)

Mở terminal mới và chọn một trong các cách:

#### ⚡ Option A: Test nhanh (30 URLs đầu - ~2 phút)
```bash
cd /home/xuananh/work_1/anhnx/crawl-2
./crawl_30_first.sh
```

#### 🐌 Option B: Cache TOÀN BỘ (16,304 URLs - 8-15 giờ)
```bash
cd /home/xuananh/work_1/anhnx/crawl-2
./START_CRAWL_FULL.sh
```

#### 📊 Option C: Cache một khoảng cụ thể
```bash
cd /home/xuananh/work_1/anhnx/crawl-2
./crawl_range.sh 0 100        # Cache URLs 0-100
./crawl_range.sh 1000 2000    # Cache URLs 1000-2000
```

---

### BƯỚC 3: View Web trong Browser

Mở browser và truy cập:

```
http://localhost:5002
```

**Ví dụ các URLs để test:**
- `http://localhost:5002/?mode=ETM`
- `http://localhost:5002/?mode=ETM&marke=KM`
- `http://localhost:5002/?mode=ETM&marke=KM&year=2026`
- `http://localhost:5002/?mode=ETM&marke=KM&year=2026&model=9923`

---

## 📊 Theo dõi tiến trình

### Xem log realtime:
```bash
tail -f cache_important_full.log
```

### Kiểm tra tiến trình:
```bash
./check_progress.sh
```

### Đếm số URLs đã cache:
```bash
find cache -name "*.bin" | wc -l
```

### Kiểm tra proxy stats:
```bash
curl -s http://localhost:5002/_cache_stats | python3 -m json.tool
```

---

## 🔌 Chuyển sang OFFLINE Mode

Sau khi cache xong (hoặc muốn test offline):

1. **Dừng proxy online** (Terminal 1): Nhấn `Ctrl+C`

2. **Chạy offline mode:**
```bash
./start_offline.sh
```

Bây giờ bạn có thể **tắt internet** và vẫn browse được!

---

## ⚙️ Các lệnh hữu ích

### Dừng crawl:
```bash
pkill -f auto_crawl_proxy.py
```

### Kiểm tra process đang chạy:
```bash
ps aux | grep auto_crawl_proxy.py
```

### Xem cache stats:
```bash
curl http://localhost:5002/_cache_stats
```

### Test một URL cụ thể:
```bash
curl "http://localhost:5002/?mode=ETM&marke=KM" | head -50
```

---

## ❓ Troubleshooting

### Proxy không chạy?
```bash
# Kiểm tra port 5002 đã được dùng chưa
lsof -i :5002

# Nếu có process khác, kill nó
kill -9 <PID>
```

### Crawl bị lỗi?
```bash
# Xem log chi tiết
cat cache_important_full.log | tail -50

# Kiểm tra proxy có đang chạy không
curl http://localhost:5002/_cache_stats
```

### Cache không đầy đủ?
- Đảm bảo proxy đang chạy ở **online mode** (`LIVE_FALLBACK=true`)
- Kiểm tra kết nối internet
- Xem log để tìm lỗi cụ thể

---

## 📝 Lưu ý

1. **Luôn giữ proxy chạy** khi đang crawl
2. **Không dừng proxy** đột ngột (dùng Ctrl+C)
3. **Cache sẽ mất** nếu xóa thư mục `cache/`
4. **Menu sẽ tự động generate** từ `tree_title.json` khi offline

---

## ✅ Checklist

- [ ] Proxy đang chạy (Terminal 1)
- [ ] Crawler đang chạy (Terminal 2)
- [ ] Có thể truy cập `http://localhost:5002`
- [ ] Cache đang tăng dần (check bằng `find cache -name "*.bin" | wc -l`)

---

## 🎉 Kết quả mong đợi

Sau khi cache xong:
- ✅ Tất cả important links được cache
- ✅ Menu hoạt động offline (từ tree_title.json)
- ✅ Có thể browse toàn bộ website offline
- ✅ Không cần internet để xem

**Tổng số URLs thực tế: 50,000-100,000+ URLs** (bao gồm links liên quan)

