

import uasyncio as asyncio
import aioble
from data_queue import state
from movesense_device import MovesenseDevice
from config import MOVESENSE_SERIES

SCAN_MS = 8000
RESCAN_DELAY_MS = 1200
IMU_RATE = 26
ECG_RATE = 125

async def _find(ms_series):
    print(f"[MS] Scanning for Movesense {ms_series} ...")
    try:
        async with aioble.scan(duration_ms=SCAN_MS, interval_us=30000,
                               window_us=30000, active=True) as scanner:
            async for res in scanner:
                if (res.name() or "").strip() == f"Movesense {ms_series}":
                    print("[MS] Found:", res.device)
                    state.movesense_detect = True
                    return res.device
    except Exception as e:
        print("[MS] scan error:", e)
    print("[MS] Not found")
    state.movesense_detect = False
    return None

async def movesense_task(pico_id, ms_series=MOVESENSE_SERIES):
    dev = None
    ms = None
    connected = False
    while True:
        if dev is None:
            dev = await _find(ms_series)
            if dev is None:
                await asyncio.sleep_ms(RESCAN_DELAY_MS)
                continue
        if state.running_state and not connected:
            try:
                print(f"[MS] Connecting to {ms_series} ...")
                ms = MovesenseDevice(ms_series, pico_id)
                await ms.connect_ble(dev)
                await ms.subscribe_sensor("IMU9", IMU_RATE)
                await ms.subscribe_sensor("HR")
                await ms.subscribe_sensor("ECG", ECG_RATE)
                connected = True
                print("[MS] Connected & subscribed.")
            except Exception as e:
                print("[MS] connect/sub error:", e)
                dev = None
                connected = False
                await asyncio.sleep_ms(600)
                continue
        if connected and not state.running_state:
            print("[MS] Paused -> disconnecting...")
            try:
                await ms.disconnect_ble()
            except Exception as e:
                print("[MS] disconnect error:", e)
            connected = False
            await asyncio.sleep_ms(200)
            continue
        if connected:
            try:
                await ms.process_notification()  # should have small timeouts internally
            except Exception as e:
                print("[MS] notif error:", e)
                connected = False
                dev = None
                await asyncio.sleep_ms(300)
        else:
            await asyncio.sleep_ms(200)














