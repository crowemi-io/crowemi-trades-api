import os
import unittest

from common.alpaca import alert_channel


class TestAlert(unittest.TestCase):

    def setUp(self):
        self.bot_id = os.getenv("BOT_ID")

    def test_get(self):
        alert_channel("Test message", self.bot_id)


if __name__ == '__main__':
    unittest.main()