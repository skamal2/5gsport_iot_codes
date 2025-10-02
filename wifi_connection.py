

import uasyncio as asyncio
import network
from data_queue import state
from password import WIFI_SSID, WIFI_PASSWORD

async def connect_wifi(max_wait_s=20):
    print("[WIFI] Enabling station...")
    wlan = network.WLAN(network.STA_IF)
    if not wlan.active():
        wlan.active(True)
    if not wlan.isconnected():
        print("[WIFI] Connecting to:", WIFI_SSID)
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        for _ in range(max_wait_s * 10):
            if wlan.isconnected():
                break
            await asyncio.sleep_ms(100)
    if wlan.isconnected():
        print("[WIFI] Connected. ifconfig:", wlan.ifconfig())
        state.network_connection_state = True
        return True
    print("[WIFI] FAILED")
    state.network_connection_state = False
    return False

