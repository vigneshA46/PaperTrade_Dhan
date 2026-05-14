from dhanhq import dhanhq, DhanContext, MarketFeed
from dhan_token import get_access_token
from option_chain_cache import set_option_chain

from datetime import datetime
from datetime import time as dtime
import pytz
import time
import os
import threading

access_token = get_access_token()
client_id = os.getenv("CLIENT_ID")

dhan_context = DhanContext(client_id, access_token)
dhan = dhanhq(dhan_context)

IST = pytz.timezone("Asia/Kolkata")
rb_started = False

print("Waiting for 9:15...")

while True:

    now = datetime.now(IST)

    if now.time() >= dtime(9, 16):

        print("9:15 reached")

        break

    time.sleep(1)

def get_next_expiry():
    """
    Returns current/next NIFTY expiry date
    directly from Dhan expiry list API
    """

    expiries = dhan.expiry_list(
        under_security_id=13,
        under_exchange_segment="IDX_I"
    )

    expiry_list = expiries["data"]

    # first expiry is always nearest expiry
    next_expiry = expiry_list["data"][0]
    print("next expiry", next_expiry)

    return next_expiry

next_expiry = get_next_expiry()

oc = dhan.option_chain(
    under_security_id=13,
    under_exchange_segment="IDX_I",
    expiry=str(next_expiry)
)

set_option_chain(oc)

print("OPTION CHAIN LOADED")

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
import pytz
import threading

rb_started = False

# collect all tokens
ALL_TOKENS = set()
ALL_TOKENS.update(map(str, strategy1.TOKENS))
ALL_TOKENS.update(map(str, strategy6.TOKENS))
ALL_TOKENS.update(map(str, strategy7.TOKENS))
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
    global rb_started

    token = str(msg["security_id"])
    publish(token, msg)

    ist = pytz.timezone("Asia/Kolkata")
    now = datetime.now(ist)
    #print(now.hour, now.minute, rb_started)

    if not rb_started and now.hour >= 10 and now.minute >= 1:
        print("STARTED CON")

        import range_breakout_state as strategy9

        print("Starting Range Breakout Strategy")

        threading.Thread(target=strategy9.start_strategy,daemon=True).start()

        rb_started = True


    
while True:
    try:

        feed.run_forever()

        while True:

            data = feed.get_data()

            if data:
                on_message(data)

    except Exception as e:
        print("WS ERROR:", e)
        feed.run_forever()