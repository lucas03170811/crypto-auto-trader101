import os
from exchange import Exchange

# 🚨 改成讀環境變數（從 flyctl secrets set 設定進去）
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

TESTNET = os.getenv("TESTNET", "False").lower() == "true"
DRY_RUN = os.getenv("DRY_RUN", "False").lower() == "true"

def main():
    ex = Exchange(API_KEY, API_SECRET, testnet=TESTNET)
    # 你的交易邏輯...
    print("[OK] Trading bot 啟動成功")

if __name__ == "__main__":
    main()
