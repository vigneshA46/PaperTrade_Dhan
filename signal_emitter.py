import asyncio
from signal_manager import process_signal

def emit_signal(signal):
    loop = asyncio.get_event_loop()
    loop.create_task(process_signal(signal))