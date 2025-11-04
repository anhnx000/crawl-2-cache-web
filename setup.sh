#!/bin/bash
# Script tự động thiết lập môi trường cho Ubuntu Linux với Conda và uv

set -e  # Dừng ngay khi có lỗi

echo "🚀 Thiết lập môi trường kiagds_local_cache cho Ubuntu Linux"
echo "============================================================"

# Kiểm tra conda có tồn tại không
if ! command -v conda &> /dev/null; then
    echo "❌ Conda chưa được cài đặt!"
    echo "Vui lòng cài đặt Conda trước:"
    echo "  wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh"
    echo "  bash Miniconda3-latest-Linux-x86_64.sh"
    exit 1
fi

# Kiểm tra uv có tồn tại không
if ! command -v uv &> /dev/null; then
    echo "❌ uv chưa được cài đặt!"
    echo "Đang cài đặt uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
    if ! command -v uv &> /dev/null; then
        echo "❌ Không thể cài đặt uv. Vui lòng cài thủ công:"
        echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
        echo "  source ~/.bashrc"
        exit 1
    fi
fi

echo "✅ Conda và uv đã sẵn sàng"

# Tạo môi trường conda tên "crawl" nếu chưa tồn tại
if conda env list | grep -q "^crawl "; then
    echo "✅ Môi trường conda 'crawl' đã tồn tại"
else
    echo "📦 Đang tạo môi trường conda 'crawl' với Python 3.11..."
    conda create -n crawl python=3.11 -y
    echo "✅ Đã tạo môi trường conda 'crawl'"
fi

# Kích hoạt conda environment và cài đặt dependencies bằng uv
echo "📦 Đang cài đặt dependencies bằng uv vào môi trường 'crawl'..."

# Sử dụng conda run để chạy lệnh trong môi trường crawl
conda run -n crawl uv pip install -r requirements.txt

# Hoặc nếu có pyproject.toml:
if [ -f "pyproject.toml" ]; then
    echo "📦 Đang cài đặt từ pyproject.toml..."
    conda run -n crawl uv pip install -e .
fi

echo ""
echo "✅ Thiết lập hoàn tất!"
echo ""
echo "Để sử dụng, chạy lệnh sau:"
echo "  conda activate crawl"
echo "  export LIVE_FALLBACK=true"
echo "  python app.py"
echo ""

