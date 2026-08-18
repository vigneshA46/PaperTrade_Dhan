import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))


from brokers.zebuclient import ZebuClient
from brokers.symbolresolver import SymbolResolver


client = ZebuClient(
    uid="Z68774",
    password="mT621214@",
    api_key="k3YE57Yy99D2QdCBF5r73ef2XZ5bN73G",
    vendor_code="Z68774",
    factor2="4CB6L2Q32TN6MA6633C27V6IZ6I4RN5A"
)


# Login
client.login()

# Get details
print(client.get_client_details())

# Place MARKET order
client.place_order(
    exch="NFO",
    tsym="NIFTY18AUG26C24100",  # corrected expiry
    qty=65,                     # 1 lot
    trantype="B"
)

