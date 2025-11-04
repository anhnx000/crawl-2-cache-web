
FROM ubuntu:22.04

# Thiết lập biến môi trường
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    LIVE_FALLBACK=true

# Cài đặt các dependencies cần thiết
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    bzip2 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Cài đặt Miniconda
RUN wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /tmp/miniconda.sh && \
    bash /tmp/miniconda.sh -b -p /opt/conda && \
    rm /tmp/miniconda.sh && \
    /opt/conda/bin/conda clean -tipsy && \
    ln -s /opt/conda/etc/profile.d/conda.sh /etc/profile.d/conda.sh

# Thêm conda vào PATH
ENV PATH=/opt/conda/bin:$PATH

# Cài đặt uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH=/root/.cargo/bin:$PATH

# Tạo môi trường conda tên "crawl"
RUN conda create -n crawl python=3.11 -y

# Thiết lập working directory
WORKDIR /app

# Copy requirements và pyproject.toml
COPY requirements.txt pyproject.toml* ./

# Cài đặt dependencies vào môi trường crawl bằng uv
RUN conda run -n crawl uv pip install -r requirements.txt

# Copy ứng dụng
COPY app.py .

# Expose port
EXPOSE 5002

# Chạy ứng dụng với conda environment
CMD ["conda", "run", "--no-capture-output", "-n", "crawl", "python", "app.py"]

