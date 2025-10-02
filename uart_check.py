import machine, time

# --- CONFIG: set these to your wiring/receiver ---
UART_NUM      = 1                  # 0 or 1 on Pico W
BAUD          = 115200             # try 9600 if you see nothing
PIN_TX        = 4                  # Pico TX pin wired to GNSS RX
PIN_RX        = 5                  # Pico RX pin wired to GNSS TX
PRINT_RAW_HEX = False              # set True to debug binary noise

# ------------------------------------------------
uart = machine.UART(UART_NUM, baudrate=BAUD,
                    tx=machine.Pin(PIN_TX), rx=machine.Pin(PIN_RX))

buf = b""
print("=== UART NMEA Sniffer ===")
print("UART%d @ %d baud (TX=%s, RX=%s)" % (UART_NUM, BAUD, PIN_TX, PIN_RX))
print("Waiting for NMEA sentences... (press Ctrl+C to stop)")

def _print_line(line_bytes):
    # Try to print decoded line; fall back to hex if it looks like binary
    try:
        s = line_bytes.decode().strip()
        if PRINT_RAW_HEX:
            print("TXT:", s)
        else:
            print(s)
    except:
        # Non-UTF8 garbage / binary RTCM
        if PRINT_RAW_HEX:
            print("HEX:", line_bytes.hex())
        else:
            # Show that data exists but couldn't decode cleanly
            print("BIN len", len(line_bytes))

while True:
    try:
        if uart.any():
            b = uart.read(1)
            if not b:
                continue
            if b == b'\n':
                if buf:
                    _print_line(buf)
                    buf = b""
            else:
                # Normalize CR as newline separator too
                if b == b'\r':
                    if buf:
                        _print_line(buf)
                        buf = b""
                else:
                    buf += b
        else:
            time.sleep_ms(5)
    except KeyboardInterrupt:
        print("\nStopping sniffer.")
        break
    except Exception as e:
        # Keep running even on random decode/IO hiccups
        print("ERR:", e)
        time.sleep_ms(100)
