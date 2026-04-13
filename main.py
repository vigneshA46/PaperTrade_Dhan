from dispatcher import publish
import paper_trade_niftyoption50_no_reentry as strategy1
import paper_trade_niftyoption50_reentry as strategy2
import paper_trade_niftyoption35_reentry as strategy3
import paper_trade_niftyoption35_reentry_point as strategy4
import paper_trade_niftyoption50_reentry_point as strategy5
#import range_breakout_selling as strategy5
import delta_option_buying as strategy6
import bank_nifty_option_buying as strategy7
from dhanhq import marketfeed
from dhanhq import dhanhq
from dhan_token import get_access_token
from dotenv import load_dotenv
import os

# collect all tokens
ALL_TOKENS = set()
ALL_TOKENS.update(strategy1.TOKENS)
ALL_TOKENS.update(strategy6.TOKENS)
ALL_TOKENS.update(strategy7.TOKENS)
#ALL_TOKENS.update(strategy5.TOKENS)

#ALL_TOKENS.update(strategy2.TOKENS)
#ALL_TOKENS.update(strategy3.TOKENS)


access_token = get_access_token()
CLIENT_ID = os.getenv("CLIENT_ID")

print("ALL TOKENS",ALL_TOKENS)

instruments = [
    (marketfeed.NSE_FNO, token, marketfeed.Quote)
    for (token) in ALL_TOKENS
]

instruments.append((marketfeed.IDX, "13", marketfeed.Quote))

feed = marketfeed.DhanFeed(CLIENT_ID, access_token, instruments, "v2")

def on_message(msg):
    token = str(msg["security_id"])
    publish(token, msg)  # 🔥 send tick to correct strategies
    

while True:
    try:
        feed.run_forever()
        data = feed.get_data()

        if data:
            on_message(data)

    except Exception as e:
        print("WS ERROR:", e)
        feed.run_forever()
        