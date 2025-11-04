# 🚀 Cache Important Links - Hướng dẫn đơn giản

## ⚡ Chạy ngay 1 lệnh:

```bash
cd /home/xuananh/work_1/anhnx/crawl-2
./start_all.sh
```

**Xong!** Script sẽ tự động:
1. Chạy proxy
2. Chạy crawler
3. Hiển thị log realtime

---

## 📊 Theo dõi tiến trình:

**Trong khi crawl, mở terminal mới:**

```bash
cd /home/xuananh/work_1/anhnx/crawl-2
./check_progress.sh
```

hoặc

```bash
tail -f cache_important_full.log
```

---

## 🛑 Dừng crawl:

```bash
pkill -f auto_crawl_proxy.py    # Dừng crawler
pkill -f "python3 app.py"       # Dừng proxy
```

hoặc **Ctrl+C** trong terminal đang chạy

---

## 🔌 Browse offline sau khi crawl:

```bash
./start_offline.sh
```

Mở browser: **http://localhost:5002**

---

## ⏱️ Thời gian:

- **16,304 URLs** cần khoảng **8-15 giờ**
- **Tổng thực tế:** ~50,000-100,000 URLs (do depth=3 + pagination)

---

## 💾 Kiểm tra cache:

```bash
# Đếm file cache
find cache -name "*.bin" | wc -l

# Verify important links
python3 verify_cached_links.py
```

---

## 📚 Đọc thêm:

- `START_HERE.md` - Chi tiết các cách chạy
- `OFFLINE_MODE.md` - Hướng dẫn offline mode
- `QUICK_REFERENCE.md` - Command reference

---

## 🆘 Troubleshooting:

**Lỗi "Connection refused":**
→ Proxy chưa chạy. Chạy `./start_all.sh`

**Crawler dừng:**
→ Xem log: `cat cache_important_full.log`

**Port 5002 bị chiếm:**
→ Dừng process cũ: `pkill -f "python3 app.py"`

---

**Bắt đầu ngay: `./start_all.sh`** 🚀

