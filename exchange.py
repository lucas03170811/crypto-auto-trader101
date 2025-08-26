import os
from typing import Dict, Any, List, Optional
from binance.client import Client
from binance.exceptions import BinanceAPIException

class Exchange:
    """
    python-binance 封裝（USDM Futures）
    - 支援：單向持倉、設定槓桿、市價進出、STOP_MARKET closePosition 出場
    - 對齊交易規則：LOT_SIZE / PRICE_FILTER / MIN_NOTIONAL
    - 額外：自訂 FUTURES_URL、增加 headers，降低邊緣 WAF 誤擋
    """

    def __init__(self, api_key: str, api_secret: str, testnet: bool = False):
        if not api_key or not api_secret:
            raise ValueError("缺少 API key/secret")

        # 允許以環境變數覆蓋 Futures Base URL（預設主網）
        override = os.getenv("BINANCE_FUTURES_URL", "").strip()
        base = "https://testnet.binancefuture.com" if testnet else (override if override else "https://fapi.binance.com")

        # 初始化 client
        self.client = Client(api_key, api_secret, testnet=testnet)
        self.client.FUTURES_URL = base

        # 增加 headers：有助於避開部分邊緣規則（不保證能繞過 403，但可減少誤擋）
        try:
            self.client.session.headers.update({
                "User-Agent": "Mozilla/5.0 (compatible; BinanceFuturesBot/1.0)",
                "Accept": "application/json, text/plain, */*",
            })
        except Exception:
            pass

        # 若環境有設定 proxy，讓 requests 也跟著走（可選）
        http_proxy = os.getenv("HTTP_PROXY", "").strip()
        https_proxy = os.getenv("HTTPS_PROXY", "").strip()
        if http_proxy or https_proxy:
            self.client.session.proxies.update({
                k: v for k, v in [("http", http_proxy), ("https", https_proxy)] if v
            })

        # 之後 prime_filters() 會填入
        self._tick_size: Dict[str, float] = {}
        self._step_size: Dict[str, float] = {}
        self._min_qty: Dict[str, float] = {}
        self._min_notional: Dict[str, float] = {}

    # -------- 健康檢查 / 帳戶資訊 --------
    def health_check(self) -> float:
        """驗證金鑰/權限，回傳 USDT 錢包餘額（失敗丟出例外讓主程式處理）"""
        self.client.futures_ping()
        acc = self.client.futures_account()
        # 嘗試讀 USDT 餘額
        try:
            balances = self.client.futures_account_balance()
            for b in balances:
                if b.get("asset") == "USDT":
                    return float(b.get("balance", 0.0))
        except Exception:
            pass
        return 0.0

    def account_balance(self) -> float:
        balances = self.client.futures_account_balance()
        for b in balances:
            if b.get('asset') == 'USDT':
                return float(b.get('balance', 0))
        return 0.0

    # -------- 基本參數 / 規則 --------
    def exchange_info(self) -> Dict[str, Any]:
        return self.client.futures_exchange_info()

    def symbol_filters(self) -> Dict[str, Dict[str, float]]:
        info = self.exchange_info()
        out: Dict[str, Dict[str, float]] = {}
        for s in info.get('symbols', []):
            if s.get('status') != 'TRADING':
                continue
            sym = s['symbol']
            f = {'stepSize': 0.0, 'tickSize': 0.0, 'minQty': 0.0, 'minNotional': 0.0}
            for flt in s.get('filters', []):
                t = flt.get('filterType')
                if t == 'LOT_SIZE':
                    f['stepSize'] = float(flt['stepSize']); f['minQty'] = float(flt['minQty'])
                elif t == 'PRICE_FILTER':
                    f['tickSize'] = float(flt['tickSize'])
                elif t == 'MIN_NOTIONAL':
                    # 有些品種沒提供 notional，預設 0
                    f['minNotional'] = float(flt.get('notional', 0.0))
            out[sym] = f
        return out

    def prime_filters(self):
        filters = self.symbol_filters()
        self._tick_size = {s: v.get('tickSize', 0.01) for s, v in filters.items()}
        self._step_size = {s: v.get('stepSize', 0.001) for s, v in filters.items()}
        self._min_qty = {s: v.get('minQty', 0.0) for s, v in filters.items()}
        self._min_notional = {s: v.get('minNotional', 0.0) for s, v in filters.items()}

    # -------- 交易設定 --------
    def set_one_way_mode(self):
        return self.client.futures_change_position_mode(dualSidePosition=False)

    def set_leverage(self, symbol: str, leverage: int = 30):
        return self.client.futures_change_leverage(symbol=symbol, leverage=leverage)

    # -------- 市場資料 --------
    def klines(self, symbol: str, interval: str = '5m', limit: int = 500) -> List[List[Any]]:
        return self.client.futures_klines(symbol=symbol, interval=interval, limit=limit)

    def ticker_price(self, symbol: str) -> float:
        t = self.client.futures_symbol_ticker(symbol=symbol)
        return float(t['price'])

    def top_symbols_by_quote_volume(self, limit: int = 10) -> List[str]:
        stats = self.client.futures_ticker()
        usdt_pairs = [s for s in stats if str(s.get('symbol','')).endswith('USDT')]
        usdt_pairs.sort(key=lambda x: float(x.get('quoteVolume', 0.0)), reverse=True)
        return [x['symbol'] for x in usdt_pairs[:limit]]

    # -------- 下單與撤單 --------
    def new_market_order(self, symbol: str, side: str, quantity: float, reduce_only: bool = False):
        params = dict(symbol=symbol, side=side, type='MARKET', quantity=str(quantity))
        if reduce_only:
            params['reduceOnly'] = True
        return self.client.futures_create_order(**params)

    def new_stop_market_close(self, symbol: str, side: str, stop_price: float):
        # side 是倉位方向（'LONG' / 'SHORT'），訂單方向要反向
        order_side = 'SELL' if side == 'LONG' else 'BUY'
        params = dict(
            symbol=symbol,
            side=order_side,
            type='STOP_MARKET',
            stopPrice=self._fmt_price(symbol, stop_price),
            closePosition=True,
            timeInForce='GTC'
        )
        return self.client.futures_create_order(**params)

    def cancel_all(self, symbol: str):
        return self.client.futures_cancel_all_open_orders(symbol=symbol)

    # -------- 對齊規則 --------
    def _fmt_price(self, symbol: str, price: float) -> str:
        tick = self._tick_size.get(symbol, 0.01)
        if tick > 0:
            precision = max(0, min(8, len(str(tick).split('.')[-1]) if '.' in str(tick) else 0))
            price = round(round(price / tick) * tick, precision)
        return f"{price:.8f}".rstrip('0').rstrip('.')

    def _fmt_qty(self, symbol: str, qty: float) -> float:
        step = self._step_size.get(symbol, 0.001)
        if step > 0:
            qty = round(round(qty / step) * step, 8)
        return max(qty, self._min_qty.get(symbol, 0.0))

    def round_price(self, symbol: str, price: float) -> float:
        return float(self._fmt_price(symbol, price))

    def round_qty(self, symbol: str, qty: float) -> float:
        return float(self._fmt_qty(symbol, qty))

    def min_notional(self, symbol: str) -> float:
        return float(self._min_notional.get(symbol, 0.0))
