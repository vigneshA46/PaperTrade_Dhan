import time
import pytz
import requests
from datetime import datetime, time as dtime
from dotenv import load_dotenv
import os
from dhanhq import marketfeed
from dhanhq import dhanhq
from dhan_token import get_access_token
from candle_builder import OneMinuteCandleBuilder
from find_security import load_fno_master, find_option_security
import threading



# =========================
# CONFIG
# =========================
ATM = None 
TRADE_LOG_URL = "https://dreaminalgo-backend-production.up.railway.app/api/paperlogger/papertradelogger"
EVENT_LOG_URL = "https://dreaminalgo-backend-production.up.railway.app/api/paperlogger/paperlogger"

COMMON_ID = "1fff432a-0411-40ff-aefd-c0b0026d5a6d"
SYMBOL = "NIFTY"

load_dotenv()

STRATEGY_NAME = "NIFTY_OPTION_BUYING_50"

CLIENT_ID = os.getenv("CLIENT_ID")

IST = pytz.timezone("Asia/Kolkata")

TRADE_START = dtime(9, 16)
TRADE_END   = dtime(15, 20)

TARGET_POINTS = 50
LOTSIZE = 65

today = datetime.now(IST).strftime("%Y-%m-%d")

telemetry = {
    "strategy_id": COMMON_ID,
    "run_id": COMMON_ID,
    "status": "RUNNING",
    "pnl": 0,
    "pnl_percentage": 0,
    "ce_ltp": 0,
    "pe_ltp": 0,
    "ce_pnl": 0,
    "pe_pnl": 0
}


# =========================
# LOGIN
# =========================

access_token = get_access_token()
dhan = dhanhq(CLIENT_ID, access_token)

builder = OneMinuteCandleBuilder()

fno_df=load_fno_master()


# =========================
# HELPERS
# =========================

def get_first_candle_mark(security_id):

    today = datetime.now(IST).strftime("%Y-%m-%d")
   

    idx= dhan.intraday_minute_data(
        security_id=security_id,
        exchange_segment="NSE_FNO",
        instrument_type="OPTIDX",
        from_date=today,
        to_date=today
    )
    print("Today :",type(today),today)

    data = idx.get("data", {})
    closes = data.get("close", [])
    timestamps = data.get("timestamp", [])

    for i in range(len(timestamps)):
        ts = datetime.fromtimestamp(timestamps[i], IST)  

        if ts.hour == 9 and ts.minute == 15:
            mark = float(closes[i])
            print(f"📍 HIST MARK {security_id} @ {mark}")
            return mark

    print("❌ 09:15 candle not found")
    return None

def log_event(leg_name, token, action, price, remark=""):
    payload = {
        "run_id": COMMON_ID,
        "strategy_id": COMMON_ID,
        "leg_name": leg_name,
        "token": int(token),
        "symbol": SYMBOL,
        "action": action,
        "price": price,
        "log_type": "TRADE_EVENT",
        "remark": remark
    }

    try:
        requests.post(EVENT_LOG_URL, json=payload, timeout=3)
    except Exception as e:
        print("EVENT LOG ERROR:", e)


def telemetry_broadcaster():
    while True:
        try:
            requests.post(
                "https://dreaminalgo-backend-production.up.railway.app/api/telemetry",
                json=telemetry,
                timeout=1
            )
        except Exception as e:
            print("Telemetry error:", e)

        time.sleep(1)  # 🔥 KEY PART


threading.Thread(target=telemetry_broadcaster, daemon=True).start()

def logtradeleg(strategyid, leg, symbol, strike_price, date):
    url = "https://dreaminalgo-backend-production.up.railway.app/api/tradelegs/create"
    
    payload = {
        "strategy_id": strategyid,
        "leg": leg,
        "symbol": symbol,
        "strike_price": strike_price,
        "date": date
    }

    try:
        response = requests.post(url, json=payload)

        if response.status_code == 200 or response.status_code == 201:
            print("✅ Trade leg logged successfully")
            return response.json()
        else:
            print(f"❌ Failed to log trade leg: {response.status_code}")
            print(response.text)
            return None

    except Exception as e:
        print(f"⚠️ Error while calling API: {e}")
        return None



def log_trade(leg_name,token,side,lot,entry_price,entry_time,exit_price,exit_time,pnl,cum_pnl,reason):
    payload = {
        "run_id": COMMON_ID,
        "strategy_id": COMMON_ID,
        "leg_name": leg_name,
        "token": int(token),
        "symbol": SYMBOL,
        "side": side,
        "lots": lot,
        "quantity": lot * LOTSIZE,
        "entry_price": entry_price,
        "entry_time": entry_time,
        "exit_price": exit_price,
        "exit_time": exit_time,
        "pnl": pnl,
        "cumulative_pnl": cum_pnl,
        "trade_status": "CLOSED",
        "reason": reason,
        "deployed_by": COMMON_ID
    }

    try:
        requests.post(TRADE_LOG_URL, json=payload, timeout=3)
    except Exception as e:
        print("TRADE LOG ERROR:", e)


def wait_for_start():
    print("⏳ Waiting for market...")
    while True:
        if datetime.now(IST).time() >= TRADE_START:
            print("✅ Market Started")
            return
        time.sleep(1)


def calculate_atm(price, step=50):
    return int(round(price / step) * step)


def init_state():
    return {
        "marked": None,
        "position": False,
        "pending_entry": False,
        "trading_disabled": False,
        "entry_price": None,
        "entry_time": None,
        "lot": 1,
        "pnl": 0.0,
        "symbol": None,
        "rearm_required": False
    }
# =========================
# START
# =========================


wait_for_start()

print("\n🚀 NIFTY OPTION BUYING STARTED\n")


# =========================
# INDEX FIRST CANDLE
# =========================
idx = dhan.intraday_minute_data(
    security_id=13,
    exchange_segment="IDX_I",
    instrument_type="INDEX",
    from_date=today,
    to_date=today
)

data = idx.get("data", {})

opens = data.get("open", [])
highs = data.get("high", [])
lows = data.get("low", [])
closes = data.get("close", [])
volumes = data.get("volume", [])
timestamps = data.get("timestamp", [])

opening_candles = []

for i in range(len(timestamps)):
    ts = datetime.fromtimestamp(timestamps[i], IST) 

    if ts.hour == 9 and 15 <= ts.minute <= 17:
        candle = {
            "timestamp": timestamps[i],
            "open": opens[i],
            "high": highs[i],
            "low": lows[i],
            "close": closes[i],
            "volume": volumes[i]
        }
        opening_candles.append(candle)

print("Opening candles:", opening_candles)



if opening_candles:
    atm_price = float(opening_candles[-1]["close"])  
    ATM = calculate_atm(atm_price)
    print("📌 ATM:", ATM)
   
else:
    print("Waiting for 9:17 candle...")

# =========================
# OPTION SELECTION
# =========================
today_date = datetime.now().date()

ce_row = find_option_security(fno_df, ATM, "CE", today_date, "NIFTY")
pe_row = find_option_security(fno_df, ATM, "PE", today_date, "NIFTY")

CE_ID = str(ce_row["SECURITY_ID"])
PE_ID = str(pe_row["SECURITY_ID"])
print("CE :", CE_ID)
print("PE :", PE_ID)

# Log CE leg
logtradeleg(
    COMMOM_ID,
    "CE",
    str(ce_row["SEM_TRADING_SYMBOL"]),
    ATM,
    str(today_date)
)

# Log PE leg
logtradeleg(
    COMMOM_ID,
    "PE",
    str(pe_row["SEM_TRADING_SYMBOL"]),
    ATM,
    str(today_date)
)


# =========================
# STATE
# =========================

ce_state = init_state()
pe_state = init_state()

combined_pnl = 0

ce_state["marked"] = get_first_candle_mark(CE_ID)
pe_state["marked"] = get_first_candle_mark(PE_ID)


# =========================
# STRATEGY ENGINE
# =========================

def handle_leg(name, token, candle, state, ltp):

    global combined_pnl

    now = datetime.now(IST).time()

    close = candle["close"]
    avg = (candle["open"] + candle["high"] +
           candle["low"] + candle["close"]) / 4

    timestamp = candle["timestamp"]

    # =========================
    # TIME EXIT (15:20)
    # =========================
    if now >= TRADE_END:

        if state["position"]:
            exit_price = ltp

            pnl = (exit_price - state["entry_price"]) * LOTSIZE * state["lot"]

            state["pnl"] += pnl
            combined_pnl += pnl

            log_trade(
                f"{name} BUY",
                token,
                "BUY",
                state["lot"],
                state["entry_price"],
                state["entry_time"],
                exit_price,
                datetime.now(IST).isoformat(),
                pnl,
                combined_pnl,
                "TIME EXIT"
            )

            state["position"] = False

        state["pending_entry"] = False
        state["trading_disabled"] = True
        return

    # =========================
    # STOP TRADING
    # =========================
    if state["trading_disabled"]:
        return

    # =========================
    # ENTRY SIGNAL
    # =========================
    if not state["position"] and not state["pending_entry"]:

        if close > state["marked"] and avg > state["marked"] and avg < close:

            state["pending_entry"] = True
            state["signal_time"] = timestamp

            print("🟡 SIGNAL", name)

            log_event(f"{name} BUY", token, "ENTRY_SIGNAL", close, "Entry condition met")

    # =========================
    # EXECUTE ENTRY (NEXT CANDLE ONLY)
    # =========================
    elif state["pending_entry"] and not state["position"]:

        # only next candle
        if timestamp != state["signal_time"]:

            entry_price = candle["open"]

            state["entry_price"] = entry_price
            state["entry_time"] = datetime.now(IST).isoformat()

            state["position"] = True
            state["pending_entry"] = False

            print("🟢 BUY", name, entry_price)

            log_event(f"{name} BUY", token, "ENTRY_EXECUTED", entry_price, "Trade opened")

    # =========================
    # EXIT CONDITION (STRUCTURE BREAK)
    # =========================
    if state["position"] and close < state["marked"]:

        exit_price = ltp

        pnl = (exit_price - state["entry_price"]) * LOTSIZE * state["lot"]

        state["pnl"] += pnl
        combined_pnl += pnl

        print("🔴 EXIT", name, exit_price)

        log_trade(
            f"{name} BUY",
            token,
            "BUY",
            state["lot"],
            state["entry_price"],
            state["entry_time"],
            exit_price,
            datetime.now(IST).isoformat(),
            pnl,
            combined_pnl,
            "Below Mark"
        )

        state["position"] = False
        state["pending_entry"] = False
        state["lot"] += 1


def universal_exit_check(ce_ltp, pe_ltp):

    global combined_pnl

    ce_running = 0
    pe_running = 0

    if ce_state["position"]:
        ce_running = (ce_ltp - ce_state["entry_price"]) * LOTSIZE * ce_state["lot"]

    if pe_state["position"]:
        pe_running = (pe_ltp - pe_state["entry_price"]) * LOTSIZE * pe_state["lot"]

    total = ce_state["pnl"] + pe_state["pnl"] + ce_running + pe_running

    if total >= TARGET_POINTS:

        print("🏁 TARGET HIT", total)

        # FORCE EXIT CE
        if ce_state["position"]:
            exit_price = ce_ltp
            pnl = (exit_price - ce_state["entry_price"]) * LOTSIZE * ce_state["lot"]

            ce_state["pnl"] += pnl

            log_trade(
                "CE BUY",
                CE_ID,
                "BUY",
                ce_state["lot"],
                ce_state["entry_price"],
                ce_state["entry_time"],
                exit_price,
                datetime.now(IST).isoformat(),
                pnl,
                total,
                "UNIVERSAL EXIT"
            )

            ce_state["position"] = False

        # FORCE EXIT PE
        if pe_state["position"]:
            exit_price = pe_ltp
            pnl = (exit_price - pe_state["entry_price"]) * LOTSIZE * pe_state["lot"]

            pe_state["pnl"] += pnl

            log_trade(
                "PE BUY",
                PE_ID,
                "BUY",
                pe_state["lot"],
                pe_state["entry_price"],
                pe_state["entry_time"],
                exit_price,
                datetime.now(IST).isoformat(),
                pnl,
                total,
                "UNIVERSAL EXIT"
            )

            pe_state["position"] = False

        # STOP EVERYTHING
        ce_state["trading_disabled"] = True
        pe_state["trading_disabled"] = True

        ce_state["pending_entry"] = False
        pe_state["pending_entry"] = False
# =========================
# CALLBACKS
# =========================

def on_candle(token, time_, candle):
    print("🕯", token, time_, candle)
    #print("security id",CE_ID,type(CE_ID),"token",token,type(token))

    if token == CE_ID:   
        handle_leg("CE", token, candle, ce_state)

    if token == PE_ID:
        handle_leg("PE", token, candle, pe_state)

    


def on_message(msg):

    candle = builder.process_tick(msg)

    token = str(msg["security_id"])
    ltp = msg.get("LTP")

    # store LTP
    if token == CE_ID:
        telemetry["ce_ltp"] = ltp

    if token == PE_ID:
        telemetry["pe_ltp"] = ltp

    # =========================
    # RUN UNIVERSAL EXIT (TICK LEVEL)
    # =========================
    if "ce_ltp" in telemetry and "pe_ltp" in telemetry:
        universal_exit_check(telemetry["ce_ltp"], telemetry["pe_ltp"])

    # =========================
    # CANDLE LOGIC
    # =========================
    if candle:

        if token == CE_ID:
            handle_leg("CE", token, candle, ce_state, ltp)

        if token == PE_ID:
            handle_leg("PE", token, candle, pe_state, ltp)

    # =========================
    # TELEMETRY (REAL-TIME PnL)
    # =========================
    ce_running = 0
    pe_running = 0

    if ce_state["position"]:
        ce_running = (telemetry["ce_ltp"] - ce_state["entry_price"]) * LOTSIZE * ce_state["lot"]

    if pe_state["position"]:
        pe_running = (telemetry["pe_ltp"] - pe_state["entry_price"]) * LOTSIZE * pe_state["lot"]

    telemetry["ce_pnl"] = ce_state["pnl"] + ce_running
    telemetry["pe_pnl"] = pe_state["pnl"] + pe_running
    telemetry["pnl"] = telemetry["ce_pnl"] + telemetry["pe_pnl"]

# ========================= 
# START WEBSOCKET
# =========================

instruments = [
    (marketfeed.NSE_FNO, CE_ID, marketfeed.Quote),
    (marketfeed.NSE_FNO, PE_ID, marketfeed.Quote)
]

feed = marketfeed.DhanFeed(CLIENT_ID, access_token, instruments, "v2")

while True:
    try:
        feed.run_forever()
        data = feed.get_data()

        if data:
            on_message(data)

    except Exception as e:
        print("WS ERROR:", e)
        feed.run_forever()
