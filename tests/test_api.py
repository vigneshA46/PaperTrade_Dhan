from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import requests

router = APIRouter()

DEPLOYMENT_STATUS_URL = "https://algoapi.dreamintraders.in/api/deployments/user/status"
OPEN_TRADES_URL = "https://algoapi.dreamintraders.in/api/realtradegroups/opentrades"


class ExitRequest(BaseModel):
    user_id: str
    strategy_id: str
    broker_account_id: str
    date: str


async def execute_exit(user, signal):
    broker = user["broker_name"]

    if broker == "angelone":
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
        #user = user["credentials"]

        payload = {
            "user_id": req.user_id,
            "strategy_id": req.strategy_id,
            "broker_account_id": req.broker_account_id,
            "date": req.date,
            "status": "EXITING"
        }

        requests.patch(DEPLOYMENT_STATUS_URL, json=payload)

        open_res = requests.get(OPEN_TRADES_URL, params={
            "user_id": req.user_id,
            "strategy_id": req.strategy_id,
            "broker_id": req.broker_account_id,
            "date": req.date
        })

        if open_res.status_code != 200:
            raise HTTPException(status_code=500, detail="Failed to fetch positions")

        open_positions = open_res.json()


        if not open_positions:
            payload["status"] = "CLOSED"
            requests.patch(DEPLOYMENT_STATUS_URL, json=payload)
            return {"message": "No open positions"}

        results = []

        for trade in open_positions:
            try:
                if trade.get("status") != "ENTRY":
                    continue

                exit_side = "SELL" if trade["side"] == "BUY" else "BUY"

                signal = {
                    "symbol": trade.get("symbol"),
                    "token": trade.get("token"),
                    "security_id": trade.get("security_id"),
                    "instrument_token": trade.get("instrument_token"),
                    "exchange": trade.get("exchange"),
                    "quantity": trade.get("qty"),
                    "side": exit_side,
                    "is_fno": trade.get("is_fno"),
                    "strike": trade.get("strike"),
                    "expiry": trade.get("expiry"),
                    "is_ce": trade.get("is_ce"),
                }

                await execute_exit(signal)

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