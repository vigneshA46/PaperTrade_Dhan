import os
import asyncio
import time
from dhanhq import marketfeed
from dhan_token import get_access_token
from dotenv import load_dotenv
from datetime import datetime

from candle_builder import OneMinuteCandleBuilder

asyncio.set_event_loop(asyncio.new_event_loop())

load_dotenv()

access_token = get_access_token()
CLIENT_ID = os.getenv("CLIENT_ID")

ALL_TOKENS = ["72312", "72317","72323","72279"]

print("ALL TOKENS:", ALL_TOKENS)

def create_feed(active_tokens):
    instruments = [
        (marketfeed.NSE_FNO, token, marketfeed.Quote)
        for token in active_tokens
    ]
    #instruments.append((marketfeed.IDX, "13", marketfeed.Quote))

    return marketfeed.DhanFeed(CLIENT_ID, access_token, instruments, "v2")


active_tokens = [ALL_TOKENS[0]]
current_index = 0

feed = create_feed(active_tokens)

last_switch_time = time.time()
SWITCH_INTERVAL = 120

candle_builders = {}


def on_message(msg):
    if msg.get("type") != "Quote Data":
        return

    token = str(msg["security_id"])

    if token not in candle_builders:
        candle_builders[token] = OneMinuteCandleBuilder()

    builder = candle_builders[token]

    candle = builder.process_tick({
        "type": "Quote Data",   
        "LTP": float(msg["LTP"]),
        "volume": msg.get("volume", 0),
        "LTT": msg["LTT"]
    })

    if candle:
        print(f"CANDLE CLOSED → {token} → {candle}")


feed.on_message = on_message


while True:
    try:
        feed.run_forever()
        data = feed.get_data()

        if data:
                
            on_message(data)

        if time.time() - last_switch_time >= SWITCH_INTERVAL:
            current_index += 1

            if current_index < len(ALL_TOKENS):
                new_token = ALL_TOKENS[current_index]
                active_tokens.append(new_token)

                print(f"Adding Token: {new_token}")
                print("Active Tokens:", active_tokens)


                feed = create_feed(active_tokens)
                feed.on_message = on_message
                feed.run_forever()

            last_switch_time = time.time()

    except Exception as e:
        print("WS ERROR:", e)
        feed.run_forever()