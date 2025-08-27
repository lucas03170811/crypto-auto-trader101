# 使用 Python 3.11 slim 版本
FROM python:3.11-slim

# 設定工作目錄
WORKDIR /app

# 安裝系統套件 (如果需要，例如 TA-Lib 可在這裡加)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 安裝 Python 套件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製專案檔案
COPY . .

# 啟動 bot
CMD ["python", "main.py"]
