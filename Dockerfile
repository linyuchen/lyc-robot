FROM python:3.12-slim-bookworm

WORKDIR /app

RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources && \
    sed -i 's/security.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources

RUN set -eux; \
    apt-get update; \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        tzdata \
        ffmpeg \
        gcc \
        libffi-dev \
        libssl-dev \
        git \
        curl \
        build-essential; \
    ln -fs /usr/share/zoneinfo/Asia/Shanghai /etc/localtime; \
    echo "Asia/Shanghai" > /etc/timezone; \
    rm -rf /var/lib/apt/lists/*

#RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple uv

RUN export UV_INSTALLER_GHE_BASE_URL="https://gh-proxy.com/https://github.com" && \
 curl -LsSf https://gh-proxy.com/https://github.com/astral-sh/uv/releases/latest/download/uv-installer.sh | sh

# Configure uv to use system Python and Chinese mirrors
ENV UV_PYTHON_PREFERENCE=system
ENV UV_INDEX_URL="https://pypi.tuna.tsinghua.edu.cn/simple"

COPY pyproject.toml uv.lock ./

RUN mkdir -p /root/.config/uv/
RUN echo 'index-url = "https://mirrors.aliyun.com/pypi/simple"' > /root/.config/uv/uv.toml
RUN echo 'python-preference = "system"' >> /root/.config/uv/uv.toml

# Use system Python instead of downloading a new one
RUN /root/.local/bin/uv sync --frozen --python $(which python3) && \
    rm -rf /root/.cache/uv

RUN export PLAYWRIGHT_DOWNLOAD_HOST="https://playwright.azureedge.net" && \
    /app/.venv/bin/python -m playwright install --with-deps chromium

COPY . .

RUN mkdir -p /app/data /app/logs

EXPOSE 8888

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

CMD ["/app/.venv/bin/python", "bot.py"]
