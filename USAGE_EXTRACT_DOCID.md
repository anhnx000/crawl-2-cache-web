# 📖 Hướng Dẫn Sử Dụng extract_docid_and_page_link.py

## 🎯 Mục đích
Extract tất cả links có `docId` và `page` từ một URL bất kỳ và:
- Append vào `important_links.json`
- Tự động cache các URLs tìm được

## 📋 Yêu cầu
1. Proxy phải đang chạy (`./start_online.sh`)
2. URL phải thuộc domain `kiagds.ru`
3. URL phải có chứa `docId` và `page` (hoặc có thể extract từ HTML)

## 🚀 Cách sử dụng

### Cơ bản (tự động cache):
```bash
cd /home/xuananh/work_1/anhnx/crawl-2
python3 extract_docid_and_page_link.py "https://kiagds.ru/?mode=ETM&marke=KM&year=2024&model=8353&mkb=129__25552&docId=434175&page=4"
```

### Không tự động cache:
```bash
python3 extract_docid_and_page_link.py "https://kiagds.ru/?mode=ETM&marke=KM&year=2024&model=8353&mkb=129__25552&docId=434175&page=4" --no-cache
```

### Tùy chỉnh proxy và concurrency:
```bash
python3 extract_docid_and_page_link.py "https://kiagds.ru/?mode=ETM&marke=KM&year=2024&model=8353&mkb=129__25552&docId=434175&page=4" \
  --proxy-base http://localhost:5002 \
  --cache-concurrency 5
```

## 📊 Ví dụ output

```
🔍 Đang extract links từ: https://kiagds.ru/?mode=ETM&marke=KM&year=2024&model=8353&mkb=129__25552&docId=434175&page=4
   Proxy: http://localhost:5002
   Auto cache: True

📥 Đang fetch HTML...
✅ Đã fetch HTML (152345 chars)

🔍 Đang extract links có docId và page...
✅ Tìm thấy 25 links có docId và page

📝 Tìm thấy 15 links mới

📋 Ví dụ các links mới:
   1. https://kiagds.ru/?mode=ETM&marke=KM&year=2024&model=8353&mkb=129__25552&docId=434175&page=1
   2. https://kiagds.ru/?mode=ETM&marke=KM&year=2024&model=8353&mkb=129__25552&docId=434175&page=2
   3. https://kiagds.ru/?mode=ETM&marke=KM&year=2024&model=8353&mkb=129__25552&docId=434175&page=3
   4. https://kiagds.ru/?mode=ETM&marke=KM&year=2024&model=8353&mkb=129__25552&docId=490564&page=1
   5. https://kiagds.ru/?mode=ETM&marke=KM&year=2024&model=8353&mkb=129__25552&docId=490564&page=2
   ... và 10 links khác

✅ Đã lưu 16289 URLs vào important_links.json

📦 Bắt đầu cache 15 URLs...
  ✅ Đã cache 10/15 URLs...
  ✅ Đã cache 15/15 URLs...

✅ Hoàn thành cache:
   - Thành công: 15 URLs
   - Lỗi: 0 URLs

============================================================
✅ Hoàn thành!
   - Tổng URLs trong important_links.json: 16289
   - URLs mới thêm: 15
============================================================
```

## 🔍 Các tính năng

1. **Extract links từ nhiều nguồn:**
   - HTML tags (a, link, form)
   - JavaScript code
   - onclick handlers
   - data-* attributes
   - Inline scripts

2. **Filter thông minh:**
   - Chỉ lấy URLs có `docId` và `page`
   - Chỉ lấy URLs thuộc domain `kiagds.ru`
   - Normalize URLs (loại bỏ fragment, clean params)
   - Loại bỏ duplicates

3. **Tự động cache:**
   - Cache qua proxy (giữ nguyên cache cũ)
   - Concurrency control (10 requests đồng thời mặc định)
   - Progress tracking

4. **Append vào important_links.json:**
   - Chỉ append URLs mới (chưa có trong file)
   - Tự động sắp xếp
   - Format JSON dễ đọc

## ⚙️ Options

- `url`: URL để extract links (required)
- `--proxy-base`: Proxy base URL (mặc định: http://localhost:5002)
- `--no-cache`: Không tự động cache các URLs tìm được
- `--cache-concurrency`: Số lượng requests đồng thời khi cache (mặc định: 10)

## 💡 Tips

1. **Extract từ nhiều URLs:**
   ```bash
   for url in "url1" "url2" "url3"; do
     python3 extract_docid_and_page_link.py "$url"
   done
   ```

2. **Extract với concurrency thấp hơn (nếu server chậm):**
   ```bash
   python3 extract_docid_and_page_link.py "URL" --cache-concurrency 3
   ```

3. **Chỉ extract, không cache:**
   ```bash
   python3 extract_docid_and_page_link.py "URL" --no-cache
   ```

## ⚠️ Lưu ý

- Đảm bảo proxy đang chạy trước khi sử dụng
- Script sẽ tự động normalize và filter URLs
- URLs đã có trong `important_links.json` sẽ không được thêm lại
- Cache sẽ được lưu qua proxy (không ghi đè cache cũ)
