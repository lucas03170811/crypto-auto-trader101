import os
import time
import requests
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceRequestException

class Exchange:
    def __init__(self, api_key=None, api_secret=None, testnet=False, max_retries=5, retry_delay=3):
        # 🚨 預設讀環境變數，保留你 main.py 的傳參數方式
        self.api_key = api_key or os.getenv("API_KEY")
        self.api_secret = api_secret or os.getenv("API_SECRET")
        self.testnet = testnet
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # 初始化 Binance client
        self.client = self._init_client()

        # 顯示目前 egress IP 與位置 (debug 用)
        self._print_network_info()

    def _init_client(self):
        for attempt in range(1, self.max_retries + 1):
            try:
                client = Client(self.api_key, self.api_secret, testnet=self.testnet)
                # 簡單測試連線
                client.ping()
                return client
            except (BinanceAPIException, BinanceRequestException, Exception) as e:
                print(f"[WARN] 初始化 Binance Client 失敗 (第 {attempt} 次)：{e}")
                time.sleep(self.retry_delay)
        raise RuntimeError("[FATAL] 無法連線 Binance API，請檢查 API Key 或網路設定")

    def _print_network_info(self):
        """顯示目前 Fly.io 容器的 egress IP 與區域"""
        try:
            ip = requests.get("https://api.ipify.org").text
            geo = requests.get(f"https://ipapi.co/{ip}/json/").json()
            print(f"[NET] Egress IP = {ip} | Country={geo.get('country_name')} | City={geo.get('city')} | ASN={geo.get('asn')}")
        except Exception as e:
            print(f"[WARN] 無法獲取 IP 資訊: {e}")

    # ========= 保留你原本的交易方法 ========= #
    def get_balance(self, asset="USDT"):
        """取得資產餘額"""
        try:
            balance = self.client.futures_account_balance()
            for b in balance:
                if b['asset'] == asset:
                    return float(b['balance'])
        except BinanceAPIException as e:
            print(f"[ERROR] 無法獲取餘額: {e}")
        return 0.0

    def get_price(self, symbol="BTCUSDT"):
        """取得即時價格"""
        try:
            ticker = self.client.futures_symbol_ticker(symbol=symbol)
            return float(ticker["price"])
        except BinanceAPIException as e:
            print(f"[ERROR] 無法獲取價格: {e}")
            return None

    def place_order(self, symbol, side, quantity, order_type="MARKET"):
        """下單（市價單）"""
        for attempt in range(1, self.max_retries + 1):
            try:
                order = self.client.futures_create_order(
                    symbol=symbol,
                    side=side,
                    type=order_type,
                    quantity=quantity
                )
                return order
            except BinanceAPIException as e:
                print(f"[WARN] 下單失敗 (第 {attempt} 次)：{e}")
                time.sleep(self.retry_delay)
        print("[FATAL] 下單失敗，已達最大重試次數")
        return None
