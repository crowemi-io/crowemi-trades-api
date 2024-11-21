import json

class Helper():
    @staticmethod
    def percent_change(old_value, new_value):
        return ((new_value - old_value) / old_value) * 100
    
    @staticmethod
    def read_local_config() -> dict | None:
        try:
            with open('.secret/config-paper.json') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading config file: {e}")
            return None
