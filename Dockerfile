# Dockerfile
# 使用 Python 3.10 基础镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 设置时区和环境变量
ENV TZ=Asia/Shanghai
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 安装系统依赖（用于编译某些 Python 包）
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制 requirements.txt
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 创建数据目录
RUN mkdir -p /app/sqlite_db /app/chroma_db /app/logs /app/docs

# 复制项目代码
COPY . .

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动命令（生产模式）
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]