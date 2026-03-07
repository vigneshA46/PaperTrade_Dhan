import asyncio
from dhanhq import marketfeed
from dhan_token import get_access_token
import os
from find_security import load_fno_master
from find_security import find_option_security


fno = load_fno_master()

print(fno)

data = find_option_security(fno ,26300, 'CE','2026-03-02','NIFTY')

print(data['SECURITY_ID'])
 