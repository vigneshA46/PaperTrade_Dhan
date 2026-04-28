from dispatcher import publish
import paper_trade_niftyoption50_no_reentry as strategy1
import paper_trade_niftyoption50_reentry as strategy2
import paper_trade_niftyoption35_reentry as strategy3
import paper_trade_niftyoption35_reentry_point as strategy4
import paper_trade_niftyoption50_reentry_point as strategy5

import delta_option_buying as strategy6
import bank_nifty_option_buying as strategy7
import paper_trade_niftyoption8_no_reentry as strategy8
from dhanhq import MarketFeed
from dhanhq import dhanhq,DhanContext
from datetime import datetime
from dhan_token import get_access_token
from dotenv import load_dotenv
import os

rb_started = False

# collect all tokens
ALL_TOKENS = set()
ALL_TOKENS.update(strategy1.TOKENS)
ALL_TOKENS.update(strategy6.TOKENS)
ALL_TOKENS.update(strategy7.TOKENS)
#ALL_TOKENS.update(strategy5.TOKENS)
#ALL_TOKENS.update(strategy4.TOKENS)

#ALL_TOKENS.update(strategy8.TOKENS)
#ALL_TOKENS.update(strategy2.TOKENS)
#ALL_TOKENS.update(strategy3.TOKENS)


access_token = get_access_token()
client_id = os.getenv("CLIENT_ID")
dhan_context = DhanContext(client_id, access_token)
dhan = dhanhq(dhan_context)

print("ALL TOKENS",ALL_TOKENS)

instruments = [
    (MarketFeed.NSE_FNO, token, MarketFeed.Quote)
    for (token) in ALL_TOKENS
]

instruments.append((MarketFeed.IDX, "13", MarketFeed.Quote))

feed = MarketFeed(dhan_context, instruments, "v2")

def on_message(msg):
    token = str(msg["security_id"])
    publish(token, msg)  # 🔥 send tick to correct strategies
    

while True:
    try:

        now = datetime.now()

        #if not rb_started and now.hour == 10 and now.minute >= 0:
            #import range_breakout_selling as strategy9

            #print("Starting Range Breakout Strategy")

            #ALL_TOKENS.update(strategy9.TOKENS)

            #instruments = [
                #(MarketFeed.NSE_FNO, token, MarketFeed.Quote)
                #for (token) in ALL_TOKENS
            #]

            #feed = MarketFeed(dhan_context, instruments, "v2")

            #feed.on_message = on_message

            #rb_started = True

        feed.run_forever()
        data = feed.get_data()

        if data:
            on_message(data)

    except Exception as e:
        print("WS ERROR:", e)
        feed.run_forever()
        