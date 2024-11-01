import requests


class Client:
    def __init__(self, api_key, api_secret_key, base_url):
        self.headers = {
            "accept": "application/json",
            "APCA-API-KEY-ID": api_key,
            "APCA-API-SECRET-KEY": api_secret_key
        }
        self.base_url = base_url

    def get(self, url):
        return requests.get(url, headers=self.headers)
    
    def post(self, url, payload):
        return requests.post(url, json=payload, headers=self.headers)


class TradingClient(Client):
    def __init__(self, api_key, api_secret_key, base_url):
        super().__init__(api_key, api_secret_key, base_url)

    def get_account(self):
        return requests.get(f"{self.base_url}/v2/account", headers=self.headers)

    def get_asset(self, asset: str):
        return requests.get(f"{self.base_url}/v2/assets/{asset}", headers=self.headers)
    
    def get_position(self):
        pass

    def get_order(self):
        pass

    def get_watchlist(self):
        return self.get(f"{self.base_url}/v2/watchlists")
        

    def create_order(self, payload: dict):
        return self.post(f"{self.base_url}/v2/orders", payload)
    
    def create_watchlist(self, name: str, symbols: list[str]):
        return self.post(f"{self.base_url}/v2/watchlist", {"name": name, "symbols": symbols})


class TradingDataClient(Client):
    def __init__(self, api_key, api_secret_key, base_url):
        super().__init__(api_key, api_secret_key, base_url)

    def get_snapshot(self, asset: str, feed: str = "iex"):
        url = f"{self.base_url}/v2/stocks/{asset}/snapshot?feed={feed}"
        return self.get(url)
    
    def get_historical_bars(self, asset: str, timeframe: str, limit: int, start: str, end: str):
        url = f"{self.base_url}/v2/stocks/{asset}/bars?timeframe={timeframe}&start={start}&end={end}&limit={limit}&adjustment=raw&feed=iex&sort=desc"
        return self.get(url)
