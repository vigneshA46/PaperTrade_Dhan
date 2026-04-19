# executors/angel_executor.py
import requests
from datetime import datetime
import uuid
from brokers.angel import AngelAdapter

API_URL = "https://algoapi.dreamintraders.in/api/realtradegroups"

async def angel_order(user, signal):
    try:
        creds = user["credentials"]

        adapter = AngelAdapter(
            api_key=creds["apiKey"],
            client_id=creds["clientCode"],
            password=creds["pin"],
            totp_secret=creds["totpSecret"]
        )

        adapter.login()

        qty = signal["quantity"] * user["multiplier"]

        order_id = adapter.place_order(
            symbol=signal["symbol"],
            token=signal["token"],
            side=signal["side"],
            quantity=qty
        )

        print(order_id)

        if order_id:

            print(f"✅ ANGEL order success {user['user_id']}")

            payload = {
                "user_id": user["user_id"],
                "strategy_id": user["strategy_id"],
                "broker_id": user["broker_account_id"], 
                "trade_id": str(uuid.uuid4()),
                "trade_date": datetime.now().strftime("%Y-%m-%d"),
                "event_type": signal["event_type"],
                "leg_name": signal["leg_name"],
                "symbol": signal["symbol"],
                "side": signal["side"],
                "quantity": qty,
                "price": signal["price"],
                "pnl": signal["pnl"],
                "cum_pnl": signal["cum_pnl"],
                "reason": signal["reason"]
            }

            response = requests.post(API_URL, json=payload)

            if response.status_code == 200:
                print("Trade logged successfully")
            else:
                print(f"API failed: {response.text}")

    except Exception as e:
        print(f"❌ ANGEL failed {user['user_id']}: {e}")