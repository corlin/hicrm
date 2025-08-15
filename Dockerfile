# 多阶段构建的 Dockerfile，使用 uv 进行依赖管理
FROM python:3.11-slim as builder

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安装 uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# 设置工作目录
WORKDIR /app

# 复制项目配置文件
COPY pyproject.toml uv.toml .python-version ./

# 创建虚拟环境并安装依赖
RUN uv venv /opt/venv
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 安装生产依赖
RUN uv sync --frozen --no-dev

# 生产阶段
FROM python:3.11-slim as production

# 安装运行时系统依赖
RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# 创建非root用户
RUN groupadd -r crm && useradd -r -g crm crm

# 设置工作目录
WORKDIR /app

# 从构建阶段复制虚拟环境
COPY --from=builder /opt/venv /opt/venv
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 复制应用代码
COPY src/ ./src/
COPY alembic/ ./alembic/
COPY alembic.ini ./

# 设置Python路径
ENV PYTHONPATH=/app/src

# 创建必要的目录
RUN mkdir -p /app/logs /app/data && \
    chown -R crm:crm /app

# 切换到非root用户
USER crm

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["gunicorn", "src.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]