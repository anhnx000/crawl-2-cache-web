# ⚡ Quick Reference Card

## 🚀 Start Proxy

```bash
./start_offline.sh    # 🔌 Offline mode (cache only)
./start_online.sh     # 🌐 Online mode (cache + internet)
```

## 📦 Cache Important Links

```bash
./crawl_30_first.sh   # ⚡ Test 30 URLs (2-5 min)
./crawl_full.sh       # 🚀 Full 16,304 URLs (8-15 hours)
./crawl_range.sh 0 100 # 📊 Range (e.g. 0-100)
```

## 🔍 Monitor & Check

```bash
./check_progress.sh           # Quick progress check
./test_offline.sh            # Test offline proxy
python3 verify_cached_links.py # Verify cached links
tail -f cache_important_full.log # Watch log realtime
```

## 🌐 Browse

**Open browser:**
```
http://localhost:5002
```

**Example URLs:**
```
http://localhost:5002/?mode=ETM
http://localhost:5002/?mode=ETM&marke=KM
http://localhost:5002/?mode=ETM&marke=KM&year=2026
```

## 📊 Cache Stats

```bash
# View cache stats
curl http://localhost:5002/_cache_stats | python3 -m json.tool

# Count cached files
find cache -name "*.bin" | wc -l

# Cache size
du -sh cache/
```

## 🛑 Stop & Control

```bash
pkill -f app.py              # Stop proxy
pkill -f auto_crawl_proxy.py # Stop crawler
ps aux | grep -E "(app.py|auto_crawl)" # Check processes
```

## 📚 Documentation

```bash
cat QUICK_START.md           # Quick start guide
cat OFFLINE_MODE.md          # Offline mode guide
cat CRAWL_IMPORTANT_LINKS.md # Crawl guide
cat PROJECT_STRUCTURE.md     # Project structure
./DEMO_OFFLINE.sh            # Interactive demo
```

## 🎯 Typical Workflow

### 1️⃣ Setup & Cache
```bash
# Terminal 1: Start proxy online
./start_online.sh

# Terminal 2: Cache data
./crawl_full.sh
```

### 2️⃣ Browse Offline
```bash
# Terminal 1: Stop online proxy (Ctrl+C), start offline
./start_offline.sh

# Browser: http://localhost:5002
```

## ⚙️ Configuration

**Environment variables:**
- `LIVE_FALLBACK=true/false` - Online/Offline mode
- `ORIGIN=https://kiagds.ru` - Origin URL
- `LOCAL_BASE=http://localhost:5002` - Local proxy URL
- `CACHE_DIR=cache` - Cache directory

## 💡 Pro Tips

- **Test first:** `./crawl_30_first.sh` before full crawl
- **Monitor:** Use `./check_progress.sh` during crawl
- **Backup:** `tar -czf cache_backup.tar.gz cache/`
- **Resume:** Use `--json-start-index` if interrupted
- **Depth:** depth=3 recommended for full site

## 🆘 Troubleshooting

**Proxy not running:**
```bash
ps aux | grep app.py  # Check if running
./start_offline.sh    # Start proxy
```

**Cache miss (404):**
```bash
./start_online.sh     # Switch to online mode
# Or crawl that URL
```

**Check if URL cached:**
```bash
python3 verify_cached_links.py
```

---

**Need help?** Check detailed docs in `*.md` files

