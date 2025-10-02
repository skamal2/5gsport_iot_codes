


# bynav_GNSS.py
import machine, usocket, uselect, ubinascii, time
import uasyncio as asyncio
from config import TX_PIN, RX_PIN, UART_BAUD_RATE
from password import NTRIP_CONFIG
from data_queue import gnss_queue

async def gnss_setup():
    """Quick, non-blocking UART init. NTRIP is connected later in gnss_task."""
    print("Initializing GNSS (UART) quick setup...")
    uart = machine.UART(1, baudrate=UART_BAUD_RATE,
                        tx=machine.Pin(TX_PIN), rx=machine.Pin(RX_PIN))
    return None, uart, None

def _parse_gpgga(s: str):
    if not s.startswith("$GPGGA"):
        return None
    p = s.strip().split(',')
    if len(p) < 15:
        return None
    try:
        fixq = int(p[6] or 0)
        if fixq < 1:                 # accept any valid fix during testing
            return None
        lat_raw, lat_dir = p[2], p[3]
        lon_raw, lon_dir = p[4], p[5]
        if not lat_raw or not lon_raw:
            return None
        lat = int(lat_raw[:2]) + float(lat_raw[2:]) / 60.0
        lon = int(lon_raw[:3]) + float(lon_raw[3:]) / 60.0
        if lat_dir == 'S': lat = -lat
        if lon_dir == 'W': lon = -lon
        return {"lat": lat, "lon": lon, "fixq": fixq}
    except:
        return None

async def _connect_ntrip_with_gga(gga_str: str):
    auth = ubinascii.b2a_base64(
        ("%s:%s" % (NTRIP_CONFIG['username_ntrip'], NTRIP_CONFIG['password_ntrip'])).encode()
    ).decode().strip()
    req = (
        "GET /%s HTTP/1.1\r\n"
        "Host: %s\r\n"
        "Ntrip-Version: Ntrip/2.0\r\n"
        "User-Agent: MicroPython NTRIP Client\r\n"
        "Authorization: Basic %s\r\n"
        "Ntrip-GGA: %s\r\n"
        "\r\n"
    ) % (NTRIP_CONFIG['mountpoint'], NTRIP_CONFIG['host'], auth, gga_str)

    addr = usocket.getaddrinfo(NTRIP_CONFIG['host'], NTRIP_CONFIG['port'])[0][-1]
    sock = usocket.socket()
    sock.connect(addr)
    sock.send(req.encode())
    while True:
        line = sock.readline()
        if not line or line == b'\r\n':
            break
    print("NTRIP connected; streaming RTCM.")
    return sock

async def gnss_task(sock, uart, pico_id):
    """Wait for first valid GGA, then connect NTRIP; pump RTCM <-> UART; enqueue points."""
    print("[GNSS] Task started.")
    poller = None
    last_gga_ms = time.ticks_ms()
    latest_fix_gga = None
    connected = False

    while True:
        try:
            # Read UART for GGA
            if uart.any():
                line = uart.readline()
                if line and line.startswith(b"$GPGGA"):
                    s = None
                    try:
                        s = line.decode().strip()
                    except:
                        s = None

                    if s:
                        parsed = _parse_gpgga(s)
                        if parsed:
                            latest_fix_gga = s
                            gnss_queue.enqueue({
                                "Pico_ID": pico_id,
                                "Timestamp_UTC": time.time(),
                                "Latitude": parsed["lat"],
                                "Longitude": parsed["lon"],
                                "FixQ": parsed["fixq"],
                            })

                        now = time.ticks_ms()
                        if connected and time.ticks_diff(now, last_gga_ms) > 1000:
                            try:
                                sock.send(line)
                            except Exception:
                                # Suppressed NTRIP send errors
                                connected = False
                                poller = None
                                sock = None
                            last_gga_ms = now

            # Connect NTRIP once we have a fix GGA
            if (not connected) and latest_fix_gga:
                try:
                    sock = await _connect_ntrip_with_gga(latest_fix_gga)
                    poller = uselect.poll()
                    poller.register(sock, uselect.POLLIN)
                    connected = True
                except Exception:
                    # Suppressed NTRIP connect errors
                    await asyncio.sleep_ms(1000)

            # Pump RTCM -> UART (non-blocking)
            if connected and poller:
                try:
                    for _, ev in poller.poll(5):
                        if ev & uselect.POLLIN:
                            rtcm = sock.recv(512)
                            if rtcm:
                                uart.write(rtcm)
                except Exception:
                    # Suppressed RTCM errors
                    connected = False
                    poller = None
                    sock = None

        except Exception as e:
            print("[GNSS] loop error:", e)

        await asyncio.sleep_ms(20)



































