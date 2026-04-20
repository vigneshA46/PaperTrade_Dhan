from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import requests

router = APIRouter()

DEPLOYMENT_STATUS_URL = "https://algoapi.dreamintraders.in/api/deployments/user/status"
OPEN_TRADES_URL = "https://algoapi.dreamintraders.in/api/realtradegroups/opentrades"
USER_DETAILS_URL = "https://algoapi.dreamintraders.in/api/deployments/user/status"


class ExitRequest(BaseModel):
    user_id: str
    strategy_id: str
    broker_account_id: str
    date: str


async def execute_exit(user, signal):
    broker = user["broker_name"]

    if broker == "angelone":
        print("user",user,"signal",signal)
        from executors.angel_executor import angel_order
        return await angel_order(user, signal)

    elif broker == "dhan":
        from executors.dhan_executor import dhan_order
        return await dhan_order(user, signal)

    elif broker == "aliceblue":

        from executors.ant_executer import ant_order
        return await ant_order(user, signal)

    elif broker == "upstox":
        from executors.upstox_executor import upstox_order
        return await upstox_order(user, signal)

    elif broker == "zebumynt":

        from executors.zebu_executer import zebu_order
        return await zebu_order(user, signal)

    else:
        raise Exception("Unsupported broker")


@router.post("/exit-strategy")
async def exit_strategy(req: ExitRequest):
    try:

        payload = {
            "user_id": req.user_id,
            "strategy_id": req.strategy_id,
            "broker_account_id": req.broker_account_id,
            "date": req.date,
            "status": "EXITING"
        }

        requests.patch(DEPLOYMENT_STATUS_URL, json=payload)

        user_res = requests.patch(USER_DETAILS_URL, json={
            "user_id": req.user_id,
            "strategy_id": req.strategy_id,
            "broker_account_id": req.broker_account_id
        })

        if user_res.status_code != 200:
            print("❌ USER API ERROR:", user_res.status_code, user_res.text)
            raise HTTPException(status_code=500, detail=f"User API failed: {user_res.text}")

        user_data = user_res.json()

        credentials = user_data.get("credentials")
        broker_name = user_data.get("broker_name")

        if not credentials:
            raise HTTPException(status_code=500, detail="Credentials missing")

        open_res = requests.get(OPEN_TRADES_URL, json={
            "user_id": req.user_id,
            "strategy_id": req.strategy_id,
            "broker_id": req.broker_account_id,
            "date": req.date
        })

        if open_res.status_code != 200:
            raise HTTPException(status_code=500, detail=f"Failed to fetch positions: {open_res.text}")

        open_positions = open_res.json()

        if not open_positions:
            payload["status"] = "CLOSED"
            requests.patch(DEPLOYMENT_STATUS_URL, json=payload)
            return {"message": "No open positions"}

        results = []

        for trade in open_positions:
            try:
        
                if trade.get("event_type") != "ENTRY":
                    continue

                exit_side = "SELL" if trade["side"] == "BUY" else "BUY"

        
                user = {
                    "user_id": req.user_id,
                    "broker_name": broker_name,
                    "broker_account_id": req.broker_account_id,
                    "multiplier": 1,
                    "credentials": credentials   
                }

                signal = {
                    "symbol": trade.get("symbol"),
                    "token": trade.get("token"),
                    "security_id": trade.get("security_id"),
                    "instrument_token": trade.get("instrument_token"),
                    "exchange": trade.get("exchange"),
                    "quantity": trade.get("quantity"),
                    "side": exit_side,
                    "is_fno": trade.get("is_fno"),
                    "strike": trade.get("strike"),
                    "expiry": trade.get("expiry"),
                    "is_ce": trade.get("is_ce"),
                }

                if not signal["token"]:
                    print(f"Skipping {signal['symbol']} - token missing")
                    results.append({
                        "trade_id": trade.get("id"),
                        "status": "FAILED",
                        "error": "Token missing"
                    })
                    continue

                await execute_exit(user, signal)

                results.append({
                    "trade_id": trade.get("id"),
                    "status": "EXITED"
                })

            except Exception as e:
                results.append({
                    "trade_id": trade.get("id"),
                    "status": "FAILED",
                    "error": str(e)
                })

        payload["status"] = "CLOSED"
        requests.patch(DEPLOYMENT_STATUS_URL, json=payload)

        return {
            "message": "Exit done",
            "results": results
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))