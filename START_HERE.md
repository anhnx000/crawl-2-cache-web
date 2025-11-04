# 🎯 START HERE - Hướng dẫn nhanh nhất

## 🚀 Cách 1: ALL-IN-ONE (Đơn giản nhất! ⭐)

```bash
cd /home/xuananh/work_1/anhnx/crawl-2
./start_all.sh
```

Script này sẽ **TỰ ĐỘNG**:
- ✅ Dừng processes cũ (nếu có)
- ✅ Chạy proxy (online mode)
- ✅ Chạy crawler
- ✅ Hiển thị log realtime
- ✅ Nhấn Ctrl+C để dừng theo dõi (processes vẫn chạy)

**→ Chỉ 1 lệnh duy nhất, không cần mở nhiều terminal!**

---

## ⚡ Cách 2: Script hướng dẫn từng bước

```bash
cd /home/xuananh/work_1/anhnx/crawl-2
./START_CRAWL_FULL.sh
```

Script này sẽ:
- ✅ Kiểm tra proxy có chạy chưa
- ✅ Hướng dẫn chạy proxy nếu chưa có
- ✅ Bắt đầu crawl tự động
- ✅ Hiển thị log preview

---

## 🛠️ Cách 3: Thủ công từng bước

### Terminal 1: Chạy Proxy
```bash
cd /home/xuananh/work_1/anhnx/crawl-2
./start_online.sh
```
**Giữ terminal này chạy!**

### Terminal 2: Chạy Crawler
```bash
cd /home/xuananh/work_1/anhnx/crawl-2
./crawl_full.sh
```

### Terminal 3: Monitor
```bash
cd /home/xuananh/work_1/anhnx/crawl-2
tail -f cache_important_full.log
```

---

## 📊 Theo dõi tiến trình

```bash
# Quick check
./check_progress.sh

# Realtime log
tail -f cache_important_full.log

# Watch continuous
watch -n 10 './check_progress.sh'
```

---

## 🛑 Dừng crawl

```bash
pkill -f auto_crawl_proxy.py
```

---

## 🔌 Xem kết quả Offline

Sau khi crawl xong (hoặc đang crawl), bạn có thể browse offline:

### Terminal 1: Chạy proxy offline
```bash
./start_offline.sh
```

### Browser: Mở
```
http://localhost:5002
```

---

## ⏱️ Thời gian ước tính

- **30 URLs đầu** (test): 2-5 phút
- **Full 16,304 URLs**: 8-15 giờ
- **Tổng URLs thực tế**: 50,000-100,000+ (do depth=3 + pagination)

---

## 📚 Tài liệu đầy đủ

```bash
cat QUICK_START.md        # Quick start
cat OFFLINE_MODE.md       # Offline mode
cat QUICK_REFERENCE.md    # Command reference
cat PROJECT_STRUCTURE.md  # Project structure
```

---

## 💡 Lưu ý quan trọng

1. **Luôn chạy proxy TRƯỚC khi crawl**
   - `./start_online.sh` cho crawling
   - `./start_offline.sh` cho browse offline

2. **Proxy và Crawler là 2 process riêng**
   - Proxy: `app.py` (port 5002)
   - Crawler: `auto_crawl_proxy.py` (crawl qua proxy)

3. **Cache được chia sẻ**
   - Tất cả tools dùng chung thư mục `cache/`
   - Có thể dừng và resume bất cứ lúc nào

---

## 🎯 Workflow đầy đủ

```bash
# 1. Chạy proxy (Terminal 1)
./start_online.sh

# 2. Bắt đầu crawl (Terminal 2)
./START_CRAWL_FULL.sh

# 3. Monitor (Terminal 3)
tail -f cache_important_full.log

# 4. Sau khi xong, browse offline
# Ctrl+C ở Terminal 1, sau đó:
./start_offline.sh

# 5. Mở browser
# http://localhost:5002
```

---

## 🆘 Troubleshooting

### Lỗi "Connection refused"
→ Proxy chưa chạy, chạy `./start_online.sh`

### Crawler dừng đột ngột
→ Kiểm tra log: `cat cache_important_full.log`

### URLs không load (404)
→ Chưa cache, chạy lại với online mode

### Kiểm tra process đang chạy
```bash
ps aux | grep -E "(app.py|auto_crawl)"
```

---

**Bắt đầu ngay: `./START_CRAWL_FULL.sh`** 🚀

