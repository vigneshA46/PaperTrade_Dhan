""" import os
from dotenv import load_dotenv
from dhan_token import get_access_token
from dhanhq import dhanhq
from brokers.dhan import DhanAdapter


CLIENT_ID = os.getenv("CLIENT_ID")
access_token = get_access_token()
dhan = dhanhq(CLIENT_ID,access_token)

dhanadapter = DhanAdapter(
    client_id=CLIENT_ID,
    access_token=access_token
)

 
response = dhanadapter.place_order(
        security_id="54499",     # ⚠️ actual dhan securityId required
        side="BUY",
        quantity=65
        )

print(response) 

order_id = 362260327171231

res = dhan.get_order_by_id(order_id)

print(res) 

"""


import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import time
import asyncio
from strategy_cache import load_users
from signal_emitter import emit_signal
from brokers.dhan import DhanAdapter


import requests



strategy_id = "1fff432a-0411-40ff-aefd-c0b0026d5a6d"

loop = asyncio.get_event_loop()

def get_today_deployments():
    url = f"https://algoapi.dreamintraders.in/api/deployments/today/{strategy_id}"

    try:
        response = requests.get(url, timeout=10)

        # Raise error if status not 200
        response.raise_for_status()

        data = response.json()

        # 👉 store in variable (this is what you asked)
        user_deployments = data

        return user_deployments

    except requests.exceptions.RequestException as e:
        print("API Error:", e)
        return None



def group_users_by_broker(deployments):
    grouped = {}

    if not deployments:
        return grouped

    for d in deployments:

        if d["type"] == "paper":
            continue
        broker = d.get("broker_name")

        if not broker:
            continue

        if broker not in grouped:
            grouped[broker] = []

        grouped[broker].append(d)

    return grouped


deployments = get_today_deployments()

users = group_users_by_broker(deployments)

print("FORMATTED USERS:", users)

#changes to be done



emit_signal({
    "strategy_id": strategy_id,
    "users":users,
    "option": "CE",
    "side": "BUY",
    "quantity": 65,
    "security_id": "63426",
    "token": 63396,
    "symbol": "NIFTY21APR2623500CE",
    "exchange": "NFO",
    "expiry":"2026-04-21",
    "strike":23500,
    "zebusymbol":"NIFTY",
    "is_ce":True,
    "is_fno":True,
    "antsymbol":"NIFTY",
    "pnl":0,
    "cum_pnl":0,
    "reason":"test order",
    "leg_name":"CE",
    "event_type":"ENTRY",
    "price":234.45
})

loop.run_until_complete(asyncio.sleep(5))