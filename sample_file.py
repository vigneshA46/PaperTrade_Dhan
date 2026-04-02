# sample_vwap_ws.py

from vwap_engine import VWAPManager, MinuteVWAPSampler
import threading
from dhanhq import marketfeed

    # 🔑 Replace with your credentials
CLIENT_ID = "1107425275"
ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwicGFydG5lcklkIjoiIiwiZXhwIjoxNzc1MTE3NTk4LCJpYXQiOjE3NzUwMzExOTgsInRva2VuQ29uc3VtZXJUeXBlIjoiU0VMRiIsIndlYmhvb2tVcmwiOiIiLCJkaGFuQ2xpZW50SWQiOiIxMTA3NDI1Mjc1In0.pDC39gkDfcI3zPYm3ziXNTf3hT-fgCyR1c6rwzrbQJjtZCPXkRU5t4kt33f7ziKSvOEoIGOUsg8TqnO04uicjA"

# 🔥 Your instruments
CE_ID = 40761
PE_ID = 40769

# Init VWAP manager
vwap_manager = VWAPManager()

# Optional: store latest prices
price_store = {}

sampler = MinuteVWAPSampler()


# -------------------------------
# 🧠 Tick Handler
# -------------------------------


def on_tick(msg):
    if msg["type"] == 'Quote Data':

        security_id = int(msg["security_id"])

        if security_id not in [CE_ID, PE_ID]:
            return

        # Update VWAP (tick-by-tick internally)
        _, vwap = vwap_manager.on_tick(msg)

        if vwap is None:
            return

        # 🔥 Emit only once per minute
        if sampler.should_emit(security_id):

            price = float(msg["LTP"])

            if security_id == CE_ID:
                print(f"🟢 CE 1-min VWAP: {vwap:.2f} | Price: {price}")

            elif security_id == PE_ID:
                print(f"🔴 PE 1-min VWAP: {vwap:.2f} | Price: {price}")

# -------------------------------
# 🔌 WebSocket Connection
# -------------------------------
def start_ws():

    instruments = [
    (marketfeed.NSE_FNO, str(CE_ID), marketfeed.Quote),
    (marketfeed.NSE_FNO, str(PE_ID), marketfeed.Quote)
    ]


    feed = marketfeed.DhanFeed(CLIENT_ID, ACCESS_TOKEN, instruments, "v2")
 
    while True:
        try:
            feed.run_forever()
            data = feed.get_data()

            if data:
                on_tick(data)

        except Exception as e:
            print("WS ERROR:", e)
            feed.run_forever()
# -------------------------------
# 🚀 Run
# -------------------------------
if __name__ == "__main__":
    start_ws()