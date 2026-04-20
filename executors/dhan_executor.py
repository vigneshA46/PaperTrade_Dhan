# executors/dhan_executor.py

from brokers.dhan import DhanAdapter
from dhan_token import get_access_token

async def dhan_order(user, signal):
    try:
        creds = user["credentials"]

        #print("CREDS:",creds)
        token= get_access_token()

        adapter = DhanAdapter(
            client_id=creds["clientId"],
            access_token=creds["accessToken"]
        )

        qty = signal["quantity"] * user["multiplier"]

        response = adapter.place_order(
            security_id=signal["security_id"],
            side=signal["side"],
            quantity=qty
        )
        print(response)

        print(f"✅ DHAN order success {user['user_id']}")

    except Exception as e:
        print(f"❌ DHAN failed {user['user_id']}: {e}")