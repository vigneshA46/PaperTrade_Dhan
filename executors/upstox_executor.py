from brokers.upstox_api import UpstoxBroker

async def upstox_order(user, signal):
    try:
        creds = user["credentials"]

        broker = UpstoxBroker(
            access_token=creds["accessToken"]
        )

        # 🔐 Validate token (important)
        profile = broker.get_profile()
        if profile["status"] != "success":
            raise Exception("Invalid / Expired Access Token")

        qty = signal["quantity"] * user["multiplier"]

        # 🔁 SIDE mapping (Upstox accepts BUY / SELL directly)
        side = signal["side"]

        # 🎯 INSTRUMENT RESOLUTION
        if signal.get("is_fno"):
            option_type = "CE" if signal["is_ce"] else "PE"

            inst = broker.get_option(
                symbol=signal["symbol"],
                option_type=option_type,
                mode="STRIKE",
                strike=signal["strike"]
            )

            if inst["status"] != "success":
                raise Exception(f"Instrument fetch failed: {inst}")

            instrument_token = inst["instrument_key"]

            # ⚠️ override qty using lot size (important)
            qty = inst["lot_size"] * user["multiplier"]

        else:
            # For equity (you can enhance later)
            raise Exception("Equity flow not implemented yet for Upstox")

        # 🛒 PLACE ORDER
        response = broker.place_order(
            instrument_token=instrument_token,
            qty=qty,
            side=side,
            order_type="MARKET",
            product="I"
        )

        print(response)

        print(f"✅ UPSTOX order success {user['user_id']}")

    except Exception as e:
        print(f"❌ UPSTOX failed {user['user_id']}: {e}")