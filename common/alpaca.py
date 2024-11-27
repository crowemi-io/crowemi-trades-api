import json
import requests


def alert_channel(message: str, bot: str, channel_id: str = "-1002416451737"):
    uri = f"https://api.telegram.org/bot{bot}/sendMessage?chat_id={channel_id}&text={message}"
    ret = requests.get(uri)
    return ret


class Client:
    def __init__(self, api_key, api_secret_key, base_url):
        self.headers = {
            "accept": "application/json",
            "APCA-API-KEY-ID": api_key,
            "APCA-API-SECRET-KEY": api_secret_key
        }
        self.base_url = base_url

    def get(self, url) -> dict | None:
        req = requests.get(url, headers=self.headers)
        if req.status_code == 200:
            return json.loads(req.content)
        else:
            #TODO: do something
            return None
    
    def post(self, url, payload) -> dict | None:
        req = requests.post(url, json=payload, headers=self.headers)
        if req.status_code == 200:
            return json.loads(req.content)
        else:
            return None


class TradingClient(Client):
    def __init__(self, api_key, api_secret_key, base_url):
        super().__init__(api_key, api_secret_key, base_url)

    def get_account(self):
        return requests.get(f"{self.base_url}/v2/account", headers=self.headers)

    def get_asset(self, asset: str):
        return self.get(f"{self.base_url}/v2/assets/{asset}")

    def get_order(self, symbol: str = None, order_id: str = None, status: str = 'all') -> list:
        if order_id:
            return self.get(f"{self.base_url}/v2/orders/{order_id}")
        else:
            endpoint = f"{self.base_url}/v2/orders?status={status}"
            if symbol:
                endpoint += f"&symbols={symbol}"

            return self.get(endpoint)

    def get_watchlist(self):
        return self.get(f"{self.base_url}/v2/watchlists")
        
    def get_clock(self):
        return self.get(f"{self.base_url}/v2/clock")
    
    def get_positions(self):
        return self.get(f"{self.base_url}/v2/positions")

    def create_order(self, payload: dict):
        return self.post(f"{self.base_url}/v2/orders", payload)
    
    def create_watchlist(self, name: str, symbols: list[str]):
        return self.post(f"{self.base_url}/v2/watchlist", {"name": name, "symbols": symbols})


class TradingDataClient(Client):
    def __init__(self, api_key, api_secret_key, base_url):
        super().__init__(api_key, api_secret_key, base_url)

    def get_latest_bar(self, symbol: str, feed: str = "iex"):
        return self.get(f"{self.base_url}/v2/stocks/bars/latest?symbols={symbol}&feed={feed}")

    def get_latest_quote(self, symbol: str, feed: str = "iex"):
        return self.get(f"{self.base_url}/v2/stocks/quotes/latest?symbols={symbol}&feed={feed}")

    def get_snapshot(self, asset: str, feed: str = "iex"):
        url = f"{self.base_url}/v2/stocks/{asset}/snapshot?feed={feed}"
        return self.get(url)
    
    def get_historical_bars(self, asset: str, timeframe: str, limit: int, start: str, end: str):
        '''Gets the historical bars for a given asset, within the specified timeframe for regular trading days.'''
        url = f"{self.base_url}/v2/stocks/{asset}/bars?timeframe={timeframe}&start={start}&end={end}&limit={limit}&adjustment=raw&feed=iex&sort=desc"
        r = self.get(url)
        return r
