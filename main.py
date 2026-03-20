from dispatcher import publish
import paper_trade_niftyoption50_no_reentry as strategy1
import paper_trade_niftyoption50_reentry as startergy2
import paper_trade_niftyoption35_reentry as startergy3
from dhanhq import marketfeed
from dhanhq import dhanhq
from dhan_token import get_access_token
from dotenv import load_dotenv
import os

# collect all tokens
ALL_TOKENS = set()
ALL_TOKENS.update(strategy1.TOKENS)


access_token = get_access_token()
CLIENT_ID = os.getenv("CLIENT_ID")



instruments = [
    (exchange, token, marketfeed.Quote)
    for (exchange, token) in ALL_TOKENS
]

feed = marketfeed.DhanFeed(CLIENT_ID, access_token, instruments, "v2")

def on_message(msg):
    token = str(msg["security_id"])
    publish(token, msg)   # 🔥 send tick to correct strategies

while True:
    try:
        feed.run_forever()
        data = feed.get_data()

        if data:
            on_message(data)

    except Exception as e:
        print("WS ERROR:", e)
        feed.run_forever()