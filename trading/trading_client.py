import json
import requests


class TradingClient:
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
            raise Exception(f"Error: {req.content}")
