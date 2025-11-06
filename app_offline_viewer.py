import os, re, json, hashlib, urllib.parse
from flask import Flask, request, Response

# ================== CONFIG ==================
# OFFLINE VIEWER - Port 5003
# Read-only: Chỉ đọc cache, không fetch từ internet, không ảnh hưởng crawl process
ORIGIN = os.getenv("ORIGIN", "https://kiagds.ru")
LOCAL_BASE = os.getenv("LOCAL_BASE", "http://localhost:5003")  # Port 5003
CACHE_DIR = os.getenv("CACHE_DIR", "cache")  # Dùng chung cache với crawl process
os.makedirs(CACHE_DIR, exist_ok=True)

LIVE_FALLBACK = False  # OFFLINE ONLY - Hardcode, không cho phép đổi
# Không có session vì không fetch từ internet
# Không có UA, TIMEOUT vì không cần

ALLOWED_HOST = "kiagds.ru"  # chỉ proxy domain này để an toàn
# ============================================

app = Flask(__name__)
# Note: Không tạo session vì không fetch từ internet

def _cache_key(method: str, url: str) -> str:
    return hashlib.sha256(f"{method} {url}".encode("utf-8")).hexdigest()

def _paths(method: str, url: str):
    key = _cache_key(method, url)
    return os.path.join(CACHE_DIR, key + ".bin"), os.path.join(CACHE_DIR, key + ".json")

def _load_cache(method: str, url: str):
    """Load cache - READ ONLY, không ghi đè"""
    bin_path, meta_path = _paths(method, url)
    if not (os.path.exists(bin_path) and os.path.exists(meta_path)):
        return None
    with open(bin_path, "rb") as f:
        body = f.read()
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
    return body, meta

def _is_type(content_type: str, needle: str) -> bool:
    ct = (content_type or "").lower()
    return needle in ct

def _is_html(content_type: str) -> bool:
    return _is_type(content_type, "text/html") or _is_type(content_type, "application/xhtml")

def _is_textual(content_type: str) -> bool:
    ct = (content_type or "").lower()
    return (
        "text/" in ct
        or "javascript" in ct
        or ct.startswith("application/json")
        or ct.startswith("application/xml")
        or ct.startswith("application/xhtml")
    )

def _rewrite_text(s: str) -> str:
    """Rewrite URLs về LOCAL_BASE (port 5003)"""
    # https://kiagds.ru/... -> http://localhost:5003/...
    s = re.sub(r"https?://kiagds\.ru", LOCAL_BASE, s, flags=re.I)
    # //kiagds.ru/...       -> //localhost:5003/...
    s = re.sub(r"(?<!:)//kiagds\.ru", "//localhost:5003", s, flags=re.I)
    # Also rewrite localhost:5002 -> localhost:5003 (nếu có trong cache từ crawl process)
    s = re.sub(r"http://localhost:5002", LOCAL_BASE, s, flags=re.I)
    return s

def _proxy_get(path: str):
    """Proxy GET - OFFLINE ONLY, chỉ dùng cache, không fetch từ internet"""
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
    else:
        # OFFLINE ONLY - không fetch từ internet
        return Response("Offline cache miss - This URL is not cached yet. Please wait for crawler to cache it at port 5002.", status=404)

    content_type = headers.get("Content-Type", "application/octet-stream")

    # Tất cả textual (HTML/CSS/JS/JSON) => rewrite domain về LOCAL_BASE (5003)
    if _is_textual(content_type):
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

    # Nhị phân (ảnh, font, pdf...): trả nguyên vẹn
    headers_out = {
        k: v for k, v in headers.items()
        if k.lower() not in ("content-length", "content-encoding", "transfer-encoding")
    }
    headers_out["Content-Length"] = str(len(body))
    return Response(body, status=status, headers=headers_out, content_type=content_type)

# ================== MENU GENERATOR ==================
MENU_TREE_FILE = "tree_title.json"
_menu_tree_cache = None

def _load_menu_tree():
    """Load và cache menu tree từ tree_title.json"""
    global _menu_tree_cache
    if _menu_tree_cache is None:
        tree_path = os.path.join(os.path.dirname(__file__), MENU_TREE_FILE)
        if os.path.exists(tree_path):
            try:
                with open(tree_path, "r", encoding="utf-8") as f:
                    _menu_tree_cache = json.load(f)
            except Exception as e:
                print(f"Warning: Cannot load {MENU_TREE_FILE}: {e}")
                _menu_tree_cache = {}
        else:
            print(f"Warning: {MENU_TREE_FILE} not found at {tree_path}")
            _menu_tree_cache = {}
    return _menu_tree_cache

def _get_param_value(params, key):
    """Lấy giá trị parameter (hỗ trợ cả list và single value)"""
    val = params.get(key)
    if isinstance(val, list):
        result = val[0] if val else None
    else:
        result = val if val else None
    
    # Xử lý "null" string (từ AJAX requests) - treat như None
    if result == "null" or result == "":
        return None
    return result

def _build_menu_url(base_params, new_param_key=None, new_param_value=None):
    """Build URL với parameters - dùng LOCAL_BASE (5003)"""
    params = {}
    
    # Copy existing params (trừ param sẽ thay đổi)
    if new_param_key != "mode" and "mode" in base_params:
        mode_val = _get_param_value(base_params, "mode")
        if mode_val:
            params["mode"] = mode_val
    if new_param_key != "marke" and "marke" in base_params:
        marke_val = _get_param_value(base_params, "marke")
        if marke_val:
            params["marke"] = marke_val
    if new_param_key != "year" and "year" in base_params:
        year_val = _get_param_value(base_params, "year")
        if year_val:
            params["year"] = year_val
    if new_param_key != "model" and "model" in base_params:
        model_val = _get_param_value(base_params, "model")
        if model_val:
            params["model"] = model_val
    if new_param_key != "mkb" and "mkb" in base_params:
        mkb_val = _get_param_value(base_params, "mkb")
        if mkb_val:
            params["mkb"] = mkb_val
    
    # Set new param và clear dependent params
    if new_param_key and new_param_value and new_param_value != "null":
        params[new_param_key] = new_param_value
        if new_param_key == "mode":
            params.pop("marke", None)
            params.pop("year", None)
            params.pop("model", None)
            params.pop("mkb", None)
        elif new_param_key == "marke":
            params.pop("year", None)
            params.pop("model", None)
            params.pop("mkb", None)
        elif new_param_key == "year":
            params.pop("model", None)
            params.pop("mkb", None)
        elif new_param_key == "model":
            params.pop("mkb", None)
    
    # Build URL với LOCAL_BASE (5003)
    if not params:
        return LOCAL_BASE + "/"
    return LOCAL_BASE + "/?" + urllib.parse.urlencode(params)

def _generate_menu_html(params):
    """Generate menu HTML từ tree_title.json - menu leftMenu (accordion navigation)"""
    tree_data = _load_menu_tree()
    if not tree_data or "mode" not in tree_data:
        return "<div class='menu-error'>Menu data not available</div>"
    
    # Parse current parameters
    current_mode = _get_param_value(params, "mode")
    current_marke = _get_param_value(params, "marke")
    current_year = _get_param_value(params, "year")
    current_model = _get_param_value(params, "model")
    current_mkb = _get_param_value(params, "mkb")
    
    # Menu leftMenu chỉ hiển thị khi đã chọn đầy đủ tham số (hoặc gần đầy đủ)
    # Nếu chưa đủ, trả về empty hoặc menu đơn giản
    if not current_mode:
        return "<div class='menu-info'>Please select mode first</div>"
    
    # Tìm node trong tree
    mode_data = None
    for m in tree_data["mode"]:
        if m.get("value") == current_mode:
            mode_data = m
            break
    
    if not mode_data:
        return "<div class='menu-info'>Mode not found</div>"
    
    html_parts = []
    
    # Generate breadcrumb
    html_parts.append('<div id="crumb"><nav style="--bs-breadcrumb-divider: \'>\';" aria-label="breadcrumb">')
    html_parts.append('<ol class="breadcrumb">')
    html_parts.append('<li class="breadcrumb-item"><a href="javascript:setCrumb(\'car\')"><i class="bi bi-car-front-fill"></i></a></li>')
    html_parts.append('<li class="breadcrumb-item active"><i class="bi bi-list-ol"></i></li>')
    html_parts.append('</ol></nav></div>')
    
    # Generate accordion menu structure
    html_parts.append('<ul class="accordeon">')
    
    # Tạo menu items dựa trên hierarchy
    menu_items_added = False
    
    if current_marke and "children" in mode_data and "marke" in mode_data["children"]:
        marke_data = mode_data["children"]["marke"]
        for marke_option in marke_data.get("options", []):
            if marke_option.get("value") == current_marke:
                if current_year and "children" in marke_option and "year" in marke_option["children"]:
                    year_data = marke_option["children"]["year"]
                    for year_option in year_data.get("options", []):
                        if year_option.get("value") == current_year:
                            if current_model and "children" in year_option and "model" in year_option["children"]:
                                model_data = year_option["children"]["model"]
                                for model_option in model_data.get("options", []):
                                    if model_option.get("value") == current_model:
                                        # Tạo menu item cho model này
                                        html_parts.append(f'<li><div>{model_option.get("title", model_option["value"])}</div><ul>')
                                        menu_items_added = True
                                        
                                        if current_mkb and "children" in model_option and "mkb" in model_option["children"]:
                                            mkb_data = model_option["children"]["mkb"]
                                            for mkb_option in mkb_data.get("options", []):
                                                if mkb_option.get("value") == current_mkb:
                                                    # Tạo menu item cho mkb
                                                    html_parts.append(f'<li><div>{mkb_option.get("title", mkb_option["value"])}</div></li>')
                                        
                                        html_parts.append('</ul></li>')
                                        break
                            break
                break
    
    # Nếu không có menu items, thêm message (không để empty)
    if not menu_items_added:
        if current_marke and current_year and not current_model:
            html_parts.append('<li><div>Please select a model to view menu</div></li>')
        elif current_marke and not current_year:
            html_parts.append('<li><div>Please select a year to view menu</div></li>')
        elif not current_marke:
            html_parts.append('<li><div>Please select a make to view menu</div></li>')
    
    html_parts.append('</ul>')
    
    return "".join(html_parts)

def _generate_title_car(params):
    """Generate title car từ tree_title.json"""
    tree_data = _load_menu_tree()
    if not tree_data:
        return ""
    
    # Parse current parameters
    current_mode = _get_param_value(params, "mode")
    current_marke = _get_param_value(params, "marke")
    current_year = _get_param_value(params, "year")
    current_model = _get_param_value(params, "model")
    current_mkb = _get_param_value(params, "mkb")
    
    parts = []
    
    # Find và build title từ tree
    if current_mode:
        for mode_item in tree_data.get("mode", []):
            if mode_item.get("value") == current_mode:
                parts.append(mode_item.get("title", current_mode))
                
                if current_marke and "children" in mode_item and "marke" in mode_item["children"]:
                    for marke_option in mode_item["children"]["marke"].get("options", []):
                        if marke_option.get("value") == current_marke:
                            parts.append(marke_option.get("title", current_marke))
                            
                            if current_year and "children" in marke_option and "year" in marke_option["children"]:
                                for year_option in marke_option["children"]["year"].get("options", []):
                                    if year_option.get("value") == current_year:
                                        parts.append(year_option.get("title", current_year))
                                        
                                        if current_model and "children" in year_option and "model" in year_option["children"]:
                                            for model_option in year_option["children"]["model"].get("options", []):
                                                if model_option.get("value") == current_model:
                                                    parts.append(model_option.get("title", current_model))
                                                    
                                                    if current_mkb and "children" in model_option and "mkb" in model_option["children"]:
                                                        for mkb_option in model_option["children"]["mkb"].get("options", []):
                                                            if mkb_option.get("value") == current_mkb:
                                                                parts.append(mkb_option.get("title", current_mkb))
                                                                break
                                                    break
                                        break
                            break
                break
    
    return " / ".join(parts) if parts else ""

def _generate_select_options(params, select_type):
    """Generate options cho select dropdowns (get_marke, get_year, get_model, get_mkb)"""
    tree_data = _load_menu_tree()
    if not tree_data:
        return "<option value='null' selected>Not available</option>"
    
    current_mode = _get_param_value(params, "mode")
    current_marke = _get_param_value(params, "marke")
    current_year = _get_param_value(params, "year")
    current_model = _get_param_value(params, "model")
    
    html_parts = []
    
    if select_type == "marke":
        if current_mode:
            for mode_item in tree_data.get("mode", []):
                if mode_item.get("value") == current_mode:
                    if "children" in mode_item and "marke" in mode_item["children"]:
                        html_parts.append('<option value="null">Make</option>')
                        for marke_option in mode_item["children"]["marke"].get("options", []):
                            if marke_option.get("value") and not marke_option.get("placeholder"):
                                selected = ' selected' if marke_option["value"] == current_marke else ''
                                html_parts.append(f'<option value="{marke_option["value"]}"{selected}>{marke_option.get("title", marke_option["value"])}</option>')
                    break
    
    elif select_type == "year":
        if current_mode and current_marke:
            for mode_item in tree_data.get("mode", []):
                if mode_item.get("value") == current_mode:
                    if "children" in mode_item and "marke" in mode_item["children"]:
                        for marke_option in mode_item["children"]["marke"].get("options", []):
                            if marke_option.get("value") == current_marke:
                                if "children" in marke_option and "year" in marke_option["children"]:
                                    html_parts.append('<option selected>Year</option>')
                                    for year_option in marke_option["children"]["year"].get("options", []):
                                        if year_option.get("value") and not year_option.get("placeholder"):
                                            selected = ' selected' if year_option["value"] == current_year else ''
                                            html_parts.append(f'<option value="{year_option["value"]}"{selected}>{year_option.get("title", year_option["value"])}</option>')
                                break
                    break
    
    elif select_type == "model":
        if current_mode and current_marke and current_year:
            for mode_item in tree_data.get("mode", []):
                if mode_item.get("value") == current_mode:
                    if "children" in mode_item and "marke" in mode_item["children"]:
                        for marke_option in mode_item["children"]["marke"].get("options", []):
                            if marke_option.get("value") == current_marke:
                                if "children" in marke_option and "year" in marke_option["children"]:
                                    for year_option in marke_option["children"]["year"].get("options", []):
                                        if year_option.get("value") == current_year:
                                            if "children" in year_option and "model" in year_option["children"]:
                                                html_parts.append('<option value=\'null\' selected>Model</option>')
                                                for model_option in year_option["children"]["model"].get("options", []):
                                                    if model_option.get("value") and not model_option.get("placeholder"):
                                                        selected = ' selected' if model_option["value"] == current_model else ''
                                                        html_parts.append(f'<option value="{model_option["value"]}">{model_option.get("title", model_option["value"])}</option>')
                                            break
                                break
                    break
    
    elif select_type == "mkb":
        if current_mode and current_marke and current_year and current_model:
            for mode_item in tree_data.get("mode", []):
                if mode_item.get("value") == current_mode:
                    if "children" in mode_item and "marke" in mode_item["children"]:
                        for marke_option in mode_item["children"]["marke"].get("options", []):
                            if marke_option.get("value") == current_marke:
                                if "children" in marke_option and "year" in marke_option["children"]:
                                    for year_option in marke_option["children"]["year"].get("options", []):
                                        if year_option.get("value") == current_year:
                                            if "children" in year_option and "model" in year_option["children"]:
                                                for model_option in year_option["children"]["model"].get("options", []):
                                                    if model_option.get("value") == current_model:
                                                        if "children" in model_option and "mkb" in model_option["children"]:
                                                            html_parts.append('<option value=\'null\' selected>Engine</option>')
                                                            for mkb_option in model_option["children"]["mkb"].get("options", []):
                                                                if mkb_option.get("value") and not mkb_option.get("placeholder"):
                                                                    selected = ' selected' if mkb_option["value"] == _get_param_value(params, "mkb") else ''
                                                                    html_parts.append(f'<option value="{mkb_option["value"]}"{selected}>{mkb_option.get("title", mkb_option["value"])}</option>')
                                                        break
                                            break
                                break
                    break
    
    if not html_parts:
        # Default placeholder
        if select_type == "marke":
            html_parts.append('<option value="null" selected>Make</option>')
        elif select_type == "year":
            html_parts.append('<option selected>Year</option>')
        elif select_type == "model":
            html_parts.append('<option value=\'null\' selected>Model</option>')
        elif select_type == "mkb":
            html_parts.append('<option value=\'null\' selected>Engine</option>')
    
    return "".join(html_parts)

# ============================================

@app.route("/ajax.php", methods=["GET"])
def ajax_handler():
    """Handle AJAX requests - OFFLINE ONLY, chỉ dùng cache hoặc generate từ tree"""
    cat = request.args.get("cat")
    
    target = f"{ORIGIN}/ajax.php"
    raw_qs = request.query_string.decode("utf-8")
    if raw_qs:
        target = f"{target}?{raw_qs}"
    
    params = {
        "mode": request.args.getlist("mode"),
        "marke": request.args.getlist("marke"),
        "year": request.args.getlist("year"),
        "model": request.args.getlist("model"),
        "mkb": request.args.getlist("mkb"),
        "vin": request.args.getlist("vin"),
    }
    
    # Kiểm tra cache trước
    cached = _load_cache("GET", target)
    if cached:
        body, meta = cached
        headers = meta.get("headers", {})
        status = int(meta.get("status", 200))
        content_type = headers.get("Content-Type", "text/html")
        
        if _is_textual(content_type):
            enc = "utf-8"
            try:
                text = body.decode(enc, errors="replace")
                text = _rewrite_text(text)  # Rewrite về port 5003
                return Response(text, status=status, content_type=content_type)
            except Exception:
                pass
    
    # Generate từ tree_title.json nếu không có cache
    if cat == "leftMenu":
        menu_html = _generate_menu_html(params)
        return Response(menu_html, content_type="text/html; charset=utf-8")
    
    elif cat == "titleCar":
        title = _generate_title_car(params)
        return Response(title, content_type="text/html; charset=utf-8")
    
    elif cat and cat.startswith("get_"):
        select_type = cat.replace("get_", "")
        if select_type in ["marke", "year", "model", "mkb"]:
            options_html = _generate_select_options(params, select_type)
            return Response(options_html, content_type="text/html; charset=utf-8")
    
    # OFFLINE ONLY - không fetch từ internet
    return Response("Offline cache miss - This AJAX request is not cached yet.", status=404)

@app.route("/_cache_stats")
def cache_stats():
    """Cache stats - chỉ đếm, không ảnh hưởng crawl"""
    n = len([f for f in os.listdir(CACHE_DIR) if f.endswith(".bin")])
    return {
        "cached_responses": n, 
        "live_fallback": False,  # OFFLINE ONLY
        "origin": ORIGIN,
        "port": 5003,
        "mode": "offline-viewer",
        "read_only": True
    }

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>", methods=["GET"])
def any_get(path):
    return _proxy_get("/" + path)

if __name__ == "__main__":
    print("=" * 60)
    print("🔌 Offline Viewer Proxy")
    print("=" * 60)
    print(f"Port: 5003")
    print(f"Mode: OFFLINE ONLY (read-only)")
    print(f"Cache dir: {CACHE_DIR}")
    print(f"URL: http://localhost:5003")
    print(f"⚠️  Only cached URLs are available")
    print(f"✅ Does NOT affect crawl process at port 5002")
    print("=" * 60)
    print("")
    app.run(host="0.0.0.0", port=5003)

