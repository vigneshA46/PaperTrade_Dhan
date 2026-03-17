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


# =========================
# CONFIG
# =========================
TRADE_LOG_URL = "https://dreaminalgo-backend-production.up.railway.app/api/paperlogger/papertradelogger"
EVENT_LOG_URL = "https://dreaminalgo-backend-production.up.railway.app/api/paperlogger/paperlogger"

COMMON_ID = "b6330608-96c1-46d9-8bc4-9696db6b9aa7"
SYMBOL = "NIFTY"

load_dotenv()

CLIENT_ID = os.getenv("DHAN_CLIENT_ID")
ACCESS_TOKEN = get_access_token()

IST = pytz.timezone("Asia/Kolkata")


INDEX_TOKEN = "13"

TRADE_START = dtime(10, 1)
TRADE_END   = dtime(15, 20)

LOT_QTY = 1
DAY_TARGET = -38

today = datetime.now(IST).strftime("%Y-%m-%d")

# =========================
# LOGIN
# =========================

dhan = dhanhq(CLIENT_ID, ACCESS_TOKEN)

builder = OneMinuteCandleBuilder()
fno_df = load_fno_master()

finder = find_option_security()

idx_builder = OneMinuteCandleBuilder()
opt_builder = OneMinuteCandleBuilder()

# =========================
# STATE
# =========================

top_line = None
bottom_line = None

CE_ID = None
PE_ID = None
ce_strike = None
pe_strike = None

ce_pos = None
pe_pos = None

pending_ce = False
pending_pe = False

total_pnl = 0
stop_trading = False

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



def log_trade(leg_name,token,side,lot,entry_price,entry_time,exit_price,exit_time,pnl,cum_pnl,reason):
    payload = {
        "run_id": COMMON_ID,
        "strategy_id": COMMON_ID,
        "leg_name": leg_name,
        "token": int(token),
        "symbol": SYMBOL,
        "side": side,
        "lots": lot,
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


# =========================
# HELPERS
# =========================

def wait_for_start():
    print("⏳ Waiting for market...")
    while True:
        if datetime.now(IST).time() >= TRADE_START:
            print("✅ Market Started")
            return
        time.sleep(1)


def calculate_atm(price, step=50):
    return int(round(price / step) * step)

def mark_range():
    global top_line, bottom_line, CE_ID, PE_ID, ce_strike, pe_strike

    today = datetime.now(IST).strftime("%Y-%m-%d")

    data = dhan.intraday_minute_data(
        security_id=13,
        exchange_segment="IDX_I",
        instrument_type="INDEX",
        from_date=f"{today} 9:55",
        to_date=f"{today} 10:00"
    )

    c = data.iloc[-1]

    top_line = max(c["open"], c["close"])
    bottom_line = min(c["open"], c["close"])

    ATM = calculate_atm(c["close"])

    ce_strike = ATM - 400
    pe_strike = ATM + 400

    ce_row = find_option_security(fno_df, ATM, "CE", today, "NIFTY")
    pe_row = find_option_security(fno_df, ATM, "PE", today, "NIFTY")

    CE_ID = str(ce_row["SECURITY_ID"])
    PE_ID = str(pe_row["SECURITY_ID"])

    print("\n📏 RANGE MARKED")
    print("TOP    :", top_line)
    print("BOTTOM :", bottom_line)
    print("ATM    :", ATM)
    print("CE     :", ce_strike, CE_ID)
    print("PE     :", pe_strike, PE_ID)

# =========================
# ENGINE
# =========================

def on_index_candle(token, t, row):
    global pending_ce, pending_pe, stop_trading

    if stop_trading:
        return

    if t.time() < TRADE_START or t.time() > TRADE_END:
        return

    avg_price = (row["open"] + row["high"] + row["low"] + row["close"]) / 4
    # ---- REARM LOGIC ----
    if not allow_pe and row["close"] < top_line:
        allow_pe = True
        print("🔓 PE REARMED @", t)

    if not allow_ce and row["close"] > bottom_line:
        allow_ce = True
        print("🔓 CE REARMED @", t)

    # ---- CE SIGNAL ----
    if ce_pos is None and allow_ce:
        if row["close"] < bottom_line and avg_price < bottom_line and avg_price < row["close"]:
            pending_ce = True
            print("📉 CE SIGNAL @", t)

    # ---- PE SIGNAL ----
    if pe_pos is None and allow_pe:
        if row["close"] > top_line and avg_price > top_line and avg_price < row["close"]:
            pending_pe = True
            print("📈 PE SIGNAL @", t)

    # ---- INDEX EXIT ----
    if ce_pos and row["close"] > bottom_line:
        exit_position("CE", row["close"], t,"INDEX")

    if pe_pos and row["close"] < top_line:
        exit_position("PE", row["close"], t,"INDEX")


def on_option_candle(token, t, row):
    global ce_pos, pe_pos, pending_ce, pending_pe

    if stop_trading:
        return

    # ---- EXECUTION ----
    if token == CE_ID and pending_ce:
        price = row["open"]
        ce_pos = {
            "entry_time": t,
            "entry_price": price,
            "best": price,
            "sl": price - 15,
            "trail": price - 30,
            "active": False,
        }
        pending_ce = False
        print("✅ CE SELL @", price, t)

    if token == PE_ID and pending_pe:
        price = row["open"]
        pe_pos = {
            "entry_time": t,
            "entry_price": price,
            "best": price,
            "sl": price - 15,
            "trail": price - 30,
            "active": False,
        }
        pending_pe = False
        print("✅ PE SELL @", price, t)

    # ---- MANAGEMENT ----
    if token == CE_ID and ce_pos:
        manage_position("CE", row["close"], t)

    if token == PE_ID and pe_pos:
        manage_position("PE", row["close"], t)


def manage_position(side, price, t):
    global ce_pos, pe_pos

    pos = ce_pos if side == "CE" else pe_pos

    pos["best"] = min(pos["best"], price)

    if not pos["active"] and price <= pos["entry_price"] - 30:
        pos["active"] = True

    if pos["active"]:
        new_trail = pos["best"] - 30
        new_sl = new_trail - 15

        if new_trail < pos["trail"]:
            pos["trail"] = new_trail
            pos["sl"] = new_sl

        if price >= pos["sl"]:
            exit_position(side, price, t, "SL")


def exit_position(side, price, t, reason):
    global ce_pos, pe_pos, total_pnl, stop_trading ,allow_ce, allow_pe

    pos = ce_pos if side == "CE" else pe_pos

    pnl = pos["entry_price"] - price
    total_pnl += pnl

    print(f"❌ {side} EXIT [{reason}] @ {price} | PNL {round(pnl,2)} | TOTAL {round(total_pnl,2)}")


    if side == "CE":
        ce_pos = None
        if reason in ("SL", "TSL"):
            allow_ce = False
    else:
        pe_pos = None
        if reason in ("SL", "TSL"):
            allow_pe = False


    if total_pnl <= DAY_TARGET:
        print("🛑 DAY TARGET HIT")
        stop_trading = True

# =========================
# WS HANDLERS
# =========================


def on_tick_index(msg):
    idx_builder.process_tick(msg, on_index_candle)


def on_tick_option(msg):
    opt_builder.process_tick(msg, on_option_candle)

# =========================
# MAIN
# =========================

if __name__ == "__main__":

    load_fno_master()

    wait_for_start()
    mark_range()

    instruments = [
        (marketfeed.NSE, INDEX_TOKEN),
        (marketfeed.NSE_FNO, CE_ID),
        (marketfeed.NSE_FNO, PE_ID)
    ]

    feed = marketfeed.DhanFeed(CLIENT_ID, ACCESS_TOKEN, instruments, "v2")

    print("\n🚀 Range Breakout Paper Engine Running...\n")

    while True:

        msg = feed.get_data()

        if msg:

            if msg["security_id"] == INDEX_TOKEN:
                on_tick_index(msg)

            elif msg["security_id"] in (CE_ID, PE_ID):
                on_tick_option(msg)