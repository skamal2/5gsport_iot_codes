


import ujson
import uasyncio as asyncio
import gc
from umqtt.robust import MQTTClient
from data_queue import ecg_queue, hr_queue, imu_queue, gnss_queue, state
from password import MQTT_CONFIG

_CLIENT_ID = b'raspberrypi-picow'
TOP_IMU  = b"sensors/imu"
TOP_ECG  = b"sensors/ecg"
TOP_HR   = b"sensors/hr"
TOP_GNSS = b"sensors/gnss"
TOP_HB   = b"sensors/hb"

def _ssl_params():
    base = dict(MQTT_CONFIG.get("ssl_params", {}))
    ca_path = base.pop("ca_path", None)
    if ca_path:
        try:
            with open(ca_path, "rb") as f:
                base["cadata"] = f.read()
        except Exception as e:
            print("[MQTT] CA load warn:", e)
    return base

def _json_bytes(obj):
    # compact JSON (double quotes) -> bytes
    return ujson.dumps(obj, separators=(",", ":")).encode()

async def connect_mqtt():
    print("[MQTT] Preparing client...")
    kw = dict(client_id=_CLIENT_ID,
              server=MQTT_CONFIG["server"],
              port=MQTT_CONFIG["port"],
              user=MQTT_CONFIG["username"],
              password=MQTT_CONFIG["password"],
              keepalive=30)
    if MQTT_CONFIG.get("ssl", False) or MQTT_CONFIG["port"] in (443, 8883):
        kw.update(ssl=True, ssl_params=_ssl_params())
    try:
        cli = MQTTClient(**kw)
        print("[MQTT] Connecting to {}:{} (TLS:{})..."
              .format(kw["server"], kw["port"], "on" if "ssl" in kw else "off"))
        cli.connect()
        print("[MQTT] Connected.")
        state.network_connection_state = True
        return cli
    except Exception as e:
        print("[MQTT] CONNECT ERROR:", e)
        state.network_connection_state = False
        return None

async def publish_to_mqtt(cli):
    hb = 0
    while True:
        try:
            if cli:
                if not imu_queue.is_empty():
                    cli.publish(TOP_IMU,  _json_bytes(imu_queue.dequeue()))
                if not ecg_queue.is_empty():
                    cli.publish(TOP_ECG,  _json_bytes(ecg_queue.dequeue()))
                if not hr_queue.is_empty():
                    cli.publish(TOP_HR,   _json_bytes(hr_queue.dequeue()))
                if not gnss_queue.is_empty():
                    cli.publish(TOP_GNSS, _json_bytes(gnss_queue.dequeue()))
                hb += 1
                if hb >= 50:  # ~5s
                    cli.publish(TOP_HB, b'{"hb":1}')
                    gc.collect()          # periodic GC to reduce fragmentation
                    hb = 0
        except Exception as e:
            print("[MQTT] Publish error:", e)
        await asyncio.sleep_ms(100)


