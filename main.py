


# main.py
import uasyncio as asyncio
import machine, sys
from wifi_connection import connect_wifi
from mqtt import connect_mqtt, publish_to_mqtt
from movesense_controller import movesense_task
from bynav_GNSS import gnss_setup, gnss_task

async def supervise(name, fn, *args):
    while True:
        try:
            await fn(*args)
        except Exception as e:
            print(f"[{name}] ERROR:")
            sys.print_exception(e)
            await asyncio.sleep(1)

async def main():
    pico = machine.unique_id().hex()
    print("=== PicoW ID:", pico, "===")

    if not await connect_wifi():
        print("[MAIN] No Wi-Fi; stopping.")
        return

    sock, uart, _ = await gnss_setup()      # returns immediately

    cli = await connect_mqtt()
    if not cli:
        print("[MAIN] MQTT connect failed; running sensors without publish.")

    tasks = []
    if cli:
        tasks.append(asyncio.create_task(supervise("MQTT", publish_to_mqtt, cli)))
    tasks.append(asyncio.create_task(supervise("MOVE", movesense_task, pico)))
    tasks.append(asyncio.create_task(supervise("GNSS", gnss_task, sock, uart, pico)))

    print("[MAIN] Started: Movesense + GNSS + MQTT")
    await asyncio.gather(*tasks)

print(">>> Start...")
loop = asyncio.get_event_loop()
loop.create_task(main())
loop.run_forever()

 






