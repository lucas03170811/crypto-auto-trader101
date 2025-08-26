import os
from binance.client import Client
from binance.exceptions import BinanceAPIException

class Exchange:
    def __init__(self, api_key: str, api_secret: str, testnet: bool = False):
        # 允許以環境變數覆蓋 Futures Base URL（預設主網）
        override = os.getenv("BINANCE_FUTURES_URL", "").strip()
        if testnet:
            base = "https://testnet.binancefuture.com"
        else:
            base = override if override else "https://fapi.binance.com"

        self.client = Client(api_key, api_secret, testnet=testnet)
        self.client.FUTURES_URL = base

        # 增加 headers，避免被邊緣規則擋下（仍可能需要換區域）
        try:
            self.client.session.headers.update({
                "User-Agent": "Mozilla/5.0 (compatible; BinanceFuturesBot/1.0)",
                "Accept": "application/json, text/plain, */*",
            })
        except Exception:
            pass

    def test_connection(self):
        """測試連線健康狀態"""
        try:
            account_info = self.client.futures_account()
            return account_info
        except BinanceAPIException as e:
            print(f"[ERROR] API 驗證失敗 -> {e}")
            raise
        except Exception as e:
            print(f"[ERROR] 無法連線 -> {e}")
            raise

    def set_one_way_mode(self, symbol="BTCUSDT"):
        """設定單向持倉模式"""
        try:
            self.client.futures_change_position_mode(dualSidePosition=False)
            print("[INFO] 已切換為單向持倉模式")
        except BinanceAPIException as e:
            print(f"[WARN] 無法設定單向持倉模式 -> {e}")

    def set_leverage(self, symbol="BTCUSDT", leverage=10):
        """設定槓桿"""
        try:
            self.client.futures_change_leverage(symbol=symbol, leverage=leverage)
            print(f"[INFO] 已設定 {symbol} 槓桿 = {leverage}x")
        except BinanceAPIException as e:
            print(f"[WARN] 無法設定槓桿 -> {e}")

    def get_balance(self, asset="USDT"):
        """取得餘額"""
        try:
            balances = self.client.futures_account_balance()
            for b in balances:
                if b["asset"] == asset:
                    return float(b["balance"])
            return 0.0
        except Exception as e:
            print(f"[ERROR] 無法取得餘額 -> {e}")
            return 0.0

    def place_order(self, symbol, side, quantity, order_type="MARKET"):
        """下單"""
        try:
            order = self.client.futures_create_order(
                symbol=symbol,
                side=side,
                type=order_type,
                quantity=quantity
            )
                def health_check(self):
        """兼容 main.py 用的健康檢查"""
        return self.test_connection()

            print(f"[TRADE] 下單成功 -> {order}")
            return order
        except BinanceAPIException as e:
            print(f"[ERROR] 下單失敗 -> {e}")
            return None
