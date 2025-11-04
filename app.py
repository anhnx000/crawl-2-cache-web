
import os, re, json, hashlib, urllib.parse
from flask import Flask, request, Response
import requests

# ================== CONFIG ==================
ORIGIN = os.getenv("ORIGIN", "https://kiagds.ru")
LOCAL_BASE = os.getenv("LOCAL_BASE", "http://localhost:5002")
CACHE_DIR = os.getenv("CACHE_DIR", "cache")
os.makedirs(CACHE_DIR, exist_ok=True)

LIVE_FALLBACK = os.getenv("LIVE_FALLBACK", "true").lower() == "true"
UA = "LocalCacheProxy/1.0 (+offline-archiver; respectful; contact=you@example.com)"
TIMEOUT = 25

ALLOWED_HOST = "kiagds.ru"  # chỉ proxy domain này để an toàn
# ============================================

app = Flask(__name__)
session = requests.Session()

def _cache_key(method: str, url: str) -> str:
    return hashlib.sha256(f"{method} {url}".encode("utf-8")).hexdigest()

def _paths(method: str, url: str):
    key = _cache_key(method, url)
    return os.path.join(CACHE_DIR, key + ".bin"), os.path.join(CACHE_DIR, key + ".json")

def _load_cache(method: str, url: str):
    bin_path, meta_path = _paths(method, url)
    if not (os.path.exists(bin_path) and os.path.exists(meta_path)):
        return None
    with open(bin_path, "rb") as f:
        body = f.read()
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
    return body, meta

def _save_cache(method: str, url: str, body: bytes, headers: dict, status: int):
    bin_path, meta_path = _paths(method, url)
    with open(bin_path, "wb") as f:
        f.write(body)
    meta = {"url": url, "status": status, "headers": dict(headers)}
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

def _is_type(content_type: str, needle: str) -> bool:
    ct = (content_type or "").lower()
    return needle in ct

def _is_html(content_type: str) -> bool:
    return _is_type(content_type, "text/html") or _is_type(content_type, "application/xhtml")

def _is_textual(content_type: str) -> bool:
    ct = (content_type or "").lower()
    # textual types we may safely rewrite absolute domain
    return (
        "text/" in ct
        or "javascript" in ct
        or ct.startswith("application/json")
        or ct.startswith("application/xml")
        or ct.startswith("application/xhtml")
    )

def _rewrite_text(s: str) -> str:
    # https://kiagds.ru/... -> http://localhost:5002/...
    s = re.sub(r"https?://kiagds\.ru", LOCAL_BASE, s, flags=re.I)
    # //kiagds.ru/...       -> //localhost:5002/...
    s = re.sub(r"(?<!:)//kiagds\.ru", "//localhost:5002", s, flags=re.I)
    return s

def _proxy_get(path: str):
    # Chỉ proxy cho domain cho phép
    target = urllib.parse.urljoin(ORIGIN, path)
    raw_qs = request.query_string.decode("utf-8")
    if raw_qs:
        target = f"{target}?{raw_qs}"

    # Kiểm tra domain an toàn
    parsed = urllib.parse.urlparse(target)
    if parsed.netloc.lower().split(":")[0].endswith(ALLOWED_HOST) is False:
        return Response("Forbidden host", status=403)

    method = "GET"
    cached = _load_cache(method, target)

    if cached:
        body, meta = cached
        headers = meta.get("headers", {})
        status = int(meta.get("status", 200))
    elif LIVE_FALLBACK:
        # Lấy mới từ origin & lưu cache
        resp = session.get(
            target,
            headers={"User-Agent": UA, "Accept-Encoding": "identity"},
            timeout=TIMEOUT,
            allow_redirects=True,
        )
        status = resp.status_code
        body = resp.content  # requests trả về đã giải nén nếu cần
        headers = dict(resp.headers)
        _save_cache(method, target, body, headers, status)
    else:
        return Response("Offline cache miss", status=404)

    content_type = headers.get("Content-Type", "application/octet-stream")

    # Tất cả textual (HTML/CSS/JS/JSON) => rewrite domain tuyệt đối về LOCAL_BASE
    if _is_textual(content_type):
        # lấy charset nếu có
        m = re.search(r"charset=([^;]+)", content_type, flags=re.I)
        enc = (m.group(1).strip() if m else "utf-8")
        try:
            text = body.decode(enc, errors="replace")
        except Exception:
            text = body.decode("utf-8", errors="replace")

        text = _rewrite_text(text)
        body_out = text.encode(enc, errors="replace")

        headers_out = {
            k: v for k, v in headers.items()
            if k.lower() not in ("content-length", "content-encoding", "transfer-encoding")
        }
        headers_out["Content-Length"] = str(len(body_out))
        headers_out["Content-Encoding"] = "identity"

        return Response(body_out, status=status, headers=headers_out, content_type=content_type)

    # Nhị phân (ảnh, font, pdf...): trả nguyên vẹn, bỏ content-encoding để tránh lệch
    headers_out = {
        k: v for k, v in headers.items()
        if k.lower() not in ("content-length", "content-encoding", "transfer-encoding")
    }
    headers_out["Content-Length"] = str(len(body))
    return Response(body, status=status, headers=headers_out, content_type=content_type)

@app.route("/_cache_stats")
def cache_stats():
    # Thống kê sơ bộ
    n = len([f for f in os.listdir(CACHE_DIR) if f.endswith(".bin")])
    return {"cached_responses": n, "live_fallback": LIVE_FALLBACK, "origin": ORIGIN}

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>", methods=["GET"])
def any_get(path):
    return _proxy_get("/" + path)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)
