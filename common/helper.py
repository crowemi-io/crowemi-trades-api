import base64
import json

class Helper():
    @staticmethod
    def percent_change(old_value, new_value):
        return ((new_value - old_value) / old_value) * 100
    
    @staticmethod
    def convert_config(b64: str) -> dict | None:
        try:
            config = base64.b64decode(b64).decode("utf-8")
            return json.loads(config)
        except Exception as e:
            print(f"Error reading config file: {e}")
            return None
