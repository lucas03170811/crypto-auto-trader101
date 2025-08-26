import os
from exchange import Exchange

from strategies.trend import generate_trend_signal
from strategies.revert import generate_revert_signal

def main():
    # 讀取環境變數
    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")
    testnet = os.getenv("TESTNET", "true").lower() == "true"
    dry_run = os.getenv("DRY_RUN", "true").lower() == "true"
    exit_on_auth_error = os.getenv("EXIT_ON_AUTH_ERROR", "true").lower() == "true"

    symbols = os.getenv("SYMBOLS", "BTCUSDT,ETHUSDT,SOLUSDT,BNBUSDT,TONUSDT,SUIUSDT").split(",")

    exch = Exchange(api_key, api_secret, testnet=testnet, dry_run=dry_run)

    print(f"Monitoring symbols: {symbols} | TESTNET={testnet} DRY_RUN={dry_run}")

    # 啟動前 API 健檢
    if not exch.check_connection():
        print("[ERROR] 無法通過 API 驗證，請檢查：")
        print("  1. 是否主網金鑰但 TESTNET=true？")
        print("  2. API 是否勾選期貨交易？")
        print("  3. 是否設定了 IP 白名單？")
        print("  4. API Key / Secret 是否有多餘空格？")
        if exit_on_auth_error:
            return

    # 模擬訊號
    for sym in symbols:
        trend_signal = generate_trend_signal(sym)
        revert_signal = generate_revert_signal(sym)
        print(f"[{sym}] Trend={trend_signal} | Revert={revert_signal}")

if __name__ == "__main__":
    main()
