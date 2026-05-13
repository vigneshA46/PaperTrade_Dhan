import threading
import time

option_chain_data = None

lock = threading.Lock()

def get_next_expiry():
    """
    Returns current/next NIFTY expiry date
    directly from Dhan expiry list API
    """

    expiries = dhan.expiry_list(
        under_security_id=13,
        under_exchange_segment="IDX_I"
    )

    expiry_list = expiries["data"]

    # first expiry is always nearest expiry
    next_expiry = expiry_list["data"][0]

    return next_expiry


next_expiry = get_next_expiry()


def fetch_option_chain(dhan):

    global option_chain_data

    try:

        oc = dhan.option_chain(
            under_security_id=13,
            under_exchange_segment="IDX_I",
            expiry=next_expiry
        )

        with lock:
            option_chain_data = oc

        print("✅ OPTION CHAIN FETCHED")

    except Exception as e:

        print("❌ OPTION CHAIN FETCH ERROR:", e)



def set_option_chain(data):

    global option_chain_data

    with lock:
        option_chain_data = data




def get_option_chain():

    with lock:
        return option_chain_data