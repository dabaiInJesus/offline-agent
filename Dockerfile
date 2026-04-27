# Offline Agent Dockerfile
# 支持 CPU 和 GPU 的多阶段构建

# ============ 构建阶段 ============
FROM python:3.10-slim AS builder

WORKDIR /app

# 安装编译依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖（构建阶段）
RUN pip install --no-cache-dir --user -r requirements.txt

# ============ 运行阶段 - CPU ============
FROM python:3.10-slim AS cpu

WORKDIR /app

# 安装运行时依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    nodejs \
    npm \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 从构建阶段复制已安装的 Python 包
COPY --from=builder /root/.local /root/.local
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# 设置 PATH
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1

# 复制应用代码
COPY . .

# 创建必要目录
RUN mkdir -p logs vector_db knowledge_base knowledge_bases

# 暴露端口
# 8000 - FastAPI 后端
# 8080 - Vue 前端
# 8001 - MCP 服务
EXPOSE 8000 8080 8001

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 默认启动命令
CMD ["python", "run.py"]

# ============ 运行阶段 - GPU (可选) ============
# 构建: docker build -t offline-agent:gpu --target gpu .
FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04 AS gpu

WORKDIR /app

# 安装运行时依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    nodejs \
    npm \
    curl \
    python3.10 \
    python3.10-venv \
    && rm -rf /var/lib/apt/lists/*

# 设置 Python 3.10
RUN ln -sf /usr/bin/python3.10 /usr/bin/python && \
    ln -sf /usr/bin/pip /usr/bin/pip

# 复制依赖文件并安装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建必要目录
RUN mkdir -p logs vector_db knowledge_base knowledge_bases

# 暴露端口
EXPOSE 8000 8080 8001

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 默认启动命令
CMD ["python", "run.py"]
