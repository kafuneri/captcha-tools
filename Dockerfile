# 第一阶段：构建依赖
FROM python:3.10-slim as builder

WORKDIR /app
COPY requirements_without_train.txt .

# 合并清理步骤到单个 RUN 指令
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc python3-dev \
 && pip3 install --user --no-cache-dir -r requirements_without_train.txt \
 && apt-get purge -y --auto-remove gcc python3-dev \
 && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# 第二阶段：运行环境
FROM python:3.10-slim

# 合并运行时依赖安装步骤
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

WORKDIR /app

# 复制 Python 依赖
COPY --from=builder /root/.local/lib/python3.10/site-packages /root/.local/lib/python3.10/site-packages
COPY --from=builder /root/.local/bin /root/.local/bin
COPY . .

# 设置环境变量
# 开启 pdl(九宫格) 和 dfine(图标点选)，强制关闭 multi(多模态流水线)
ENV PATH=/root/.local/bin:$PATH \
    PIP_BREAK_SYSTEM_PACKAGES=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    use_pdl=1 \
    use_dfine=1 \
    use_multi=0

# 清理 Python 缓存和临时文件
RUN find /app -name "*.pyc" -delete \
 && find /app -name "__pycache__" -delete \
 && find /root/.local -name "*.pyc" -delete \
 && find /root/.local -type d -name "__pycache__" -exec rm -rf {} +

CMD ["python3", "main.py"]