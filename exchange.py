import os
from binance.um_futures import UMFutures
from binance.error import ClientError

class Exchange:
    def __init__(self, api_key, api_secret, testnet=True, dry_run=True):
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        self.dry_run = dry_run

        base_url = "https://testnet.binancefuture.com" if testnet else "https://fapi.binance.com"
        print(f"[INFO] Using FUTURES_URL: {base_url}")

        self.client = UMFutures(key=api_key, secret=api_secret, base_url=base_url)

    def check_connection(self):
        """測試 API Key 是否可用"""
        try:
            self.client.ping()
            acct = self.client.account()
            print("[INFO] API 連線成功，帳戶可用。")
            return True
        except ClientError as e:
            print(f"[ERROR] API 驗證失敗: {e}")
            return False

    def set_leverage(self, symbol, leverage=10):
        if self.dry_run:
            print(f"[DRY-RUN] Would set leverage {leverage} for {symbol}")
            return
        try:
            self.client.change_leverage(symbol=symbol, leverage=leverage)
            print(f"[INFO] Set leverage {leverage} for {symbol}")
        except ClientError as e:
            print(f"[WARN] set_leverage {symbol} failed: {e}")
