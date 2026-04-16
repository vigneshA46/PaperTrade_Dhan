from brokers.ant_broker import AntBroker
from TradeMaster.TradeSync import TransactionType, Exchange

async def ant_order(user, signal):
    try:
        creds = user["credentials"]

        adapter = AntBroker(
            user_id=creds["userId"],
            auth_code=creds["authCode"],
            secret_key=creds["apiKey"]
        )

        adapter.login()

        qty = signal["quantity"] * user["multiplier"]

        # 🔁 map side
        side = TransactionType.Buy if signal["side"] == "BUY" else TransactionType.Sell

        # 🔁 map exchange (IMPORTANT)
        exchange_map = {
            "NSE": Exchange.NSE,
            "NFO": Exchange.NFO,
            "MCX": Exchange.MCX
        }

        exchange = exchange_map.get(signal["exchange"])

        # 🎯 instrument
        if signal.get("is_fno"):
            instrument = adapter.get_fno_instrument(
                exchange=exchange,
                symbol=signal["antsymbol"],
                expiry=signal["expiry"],
                strike=str(signal["strike"]),
                is_ce=signal["is_ce"]
            )
        else:
            instrument = adapter.get_instrument(
                exchange=exchange,
                symbol=signal["antsymbol"]
            )

        # 🛒 order
        response = adapter.place_market_order(
            instrument=instrument,
            qty=qty,
            side=side,
            tag=f"algo_123"
        )

        print(response)

        print(f"✅ ANT order success {user['user_id']}")

    except Exception as e:
        print(f"❌ ANT failed {user['user_id']}: {e}")