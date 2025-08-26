import os
from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceOrderException

class Exchange:
    def __init__(self, api_key=None, api_secret=None, testnet=False, dry_run=True):
        self.api_key = api_key or os.getenv("BINANCE_API_KEY")
        self.api_secret = api_secret or os.getenv("BINANCE_API_SECRET")
        self.testnet = testnet
        self.dry_run = dry_run

        if not self.api_key or not self.api_secret:
            raise ValueError("缺少 API Key 或 Secret，請確認環境變數已正確設定")

        self.client = Client(self.api_key, self.api_secret)

        if self.testnet:
            self.client.FUTURES_URL = "https://testnet.binancefuture.com"
            print("[INFO] 使用 Binance Testnet API")
        else:
            self.client.FUTURES_URL = "https://fapi.binance.com"
            print("[INFO] 使用 Binance Mainnet API")

    def test_connection(self):
        """測試 API 是否正常連線"""
        try:
            info = self.client.futures_account()
            return info
        except Exception as e:
            print(f"[ERROR] API 驗證失敗: {e}")
            return None

    def health_check(self):
        """兼容 main.py 用的健康檢查"""
        return self.test_connection()

    def set_one_way_mode(self):
        """設定成單向持倉模式"""
        try:
            res = self.client.futures_change_position_mode(dualSidePosition=False)
            print("[INFO] 已切換為單向持倉模式")
            return res
        except BinanceAPIException as e:
            print(f"[WARN] 設定單向持倉模式失敗: {e}")
        except Exception as e:
            print(f"[WARN] 設定單向持倉模式未知錯誤: {e}")

    def get_balance(self, asset="USDT"):
        try:
            balances = self.client.futures_account_balance()
            for b in balances:
                if b["asset"] == asset:
                    return float(b["balance"])
            return 0.0
        except Exception as e:
            print(f"[WARN] account_balance failed: {e}")
            return 0.0

    def set_leverage(self, symbol, leverage=10):
        try:
            self.client.futures_change_leverage(symbol=symbol, leverage=leverage)
            print(f"[INFO] 設定 {symbol} 槓桿為 {leverage}x")
        except BinanceAPIException as e:
            print(f"[WARN] set_leverage {symbol} failed: {e}")
        except Exception as e:
            print(f"[WARN] set_leverage {symbol} unknown error: {e}")

    def place_order(self, symbol, side, quantity, order_type="MARKET", reduce_only=False):
        if self.dry_run:
            print(f"[DRY-RUN] {side} {symbol} {quantity} {order_type}")
            return {"status": "dry-run", "symbol": symbol, "side": side, "qty": quantity}

        try:
            order = self.client.futures_create_order(
                symbol=symbol,
                side=side,
                type=order_type,
                quantity=quantity,
                reduceOnly=reduce_only
            )
            print(f"[INFO] 下單成功: {order}")
            return order
        except BinanceAPIException as e:
            print(f"[ERROR] 下單失敗: {e}")
            return None
        except BinanceOrderException as e:
            print(f"[ERROR] 訂單異常: {e}")
            return None
        except Exception as e:
            print(f"[ERROR] 其他錯誤: {e}")
            return None
