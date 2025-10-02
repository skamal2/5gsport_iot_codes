

import time
import bluetooth
import uasyncio as asyncio
from micropython import const
from struct import unpack
from data_queue import ecg_queue, imu_queue, hr_queue, state

# --------- Debug control (keep False in production) ----------
DEBUG = False
def _dprint(*a, **k):
    if DEBUG:
        print(*a, **k)

# GSP Service and Characteristic UUIDs
_GSP_SERVICE_UUID = bluetooth.UUID("34802252-7185-4d5d-b431-630e7050e8f0")
_GSP_WRITE_UUID   = bluetooth.UUID("34800001-7185-4d5d-b431-630e7050e8f0")
_GSP_NOTIFY_UUID  = bluetooth.UUID("34800002-7185-4d5d-b431-630e7050e8f0")

# Command IDs
_CMD_HELLO       = const(0)
_CMD_SUBSCRIBE   = const(1)
_CMD_UNSUBSCRIBE = const(2)

class MovesenseDevice:
    BYTES_PER_ELEMENT = 4

    def __init__(self, movesense_series, pico_id, imu_ref=99, hr_ref=98, ecg_ref=97):
        self.ms_series = str(movesense_series)
        self.picoW_id  = str(pico_id)
        self.imu_ref   = imu_ref
        self.hr_ref    = hr_ref
        self.ecg_ref   = ecg_ref
        self.connection = None
        self.sensor_service = None
        self.write_char = None
        self.notify_char = None
        self.imu_sensor = "IMU9"

    def log(self, msg):
        _dprint("[Movesense %s]: %s" % (self.ms_series, msg))

    async def connect_ble(self, device):
        try:
            self.log("Connecting to %s..." % device)
            self.connection = await device.connect(timeout_ms=10000)
        except asyncio.TimeoutError:
            self.log("Connection timeout")
            return
        self.log("Connected")

        try:
            self.sensor_service = await self.connection.service(_GSP_SERVICE_UUID)
            self.notify_char = await self.sensor_service.characteristic(_GSP_NOTIFY_UUID)
            self.write_char  = await self.sensor_service.characteristic(_GSP_WRITE_UUID)
        except asyncio.TimeoutError:
            self.log("Timeout discovering services/characteristics")
            return

        if not self.sensor_service or not self.write_char or not self.notify_char:
            self.log("Required service/characteristics not found")
            return

        await self.notify_char.subscribe(notify=True)

    async def subscribe_sensor(self, sensor_type, sensor_rate=None):
        if sensor_type == "IMU9":
            cmd = bytearray([_CMD_SUBSCRIBE, self.imu_ref]) + bytearray("Meas/IMU9/%d" % sensor_rate, "utf-8")
            self.imu_sensor = "IMU9"
        elif sensor_type == "IMU6":
            cmd = bytearray([_CMD_SUBSCRIBE, self.imu_ref]) + bytearray("Meas/IMU6/%d" % sensor_rate, "utf-8")
            self.imu_sensor = "IMU6"
        elif sensor_type == "HR":
            cmd = bytearray([_CMD_SUBSCRIBE, self.hr_ref]) + bytearray("Meas/HR", "utf-8")
        elif sensor_type == "ECG":
            cmd = bytearray([_CMD_SUBSCRIBE, self.ecg_ref]) + bytearray("Meas/ECG/%d" % sensor_rate, "utf-8")
        else:
            self.log("Invalid sensor type")
            return

        self.log("Subscribing %s" % sensor_type)
        await self.write_char.write(cmd)

    async def process_notification(self):
        self.log("Waiting for notifications...")
        # Short timeouts so we yield to other asyncio tasks
        while state.running_state and self.connection and self.connection.is_connected():
            try:
                data = await self.notify_char.notified(timeout_ms=300)
                if not data:
                    continue
                ref_code = data[1]
                if ref_code == self.imu_ref:
                    self._process_imu_data(data)
                elif ref_code == self.ecg_ref:
                    self._process_ecg_data(data)
                elif ref_code == self.hr_ref:
                    self._process_hr_data(data)
            except asyncio.TimeoutError:
                continue








        ###Added by Kamal
    
    def _process_imu_data(self, data):
        sensor_count  = 3 if self.imu_sensor == "IMU9" else 2
        sample_count  = len(data[6:]) // MovesenseDevice.BYTES_PER_ELEMENT
        unpacked      = list(unpack('<BBI' + 'f'*sample_count, data))
        ts            = unpacked[2]
        vals          = unpacked[3:]

        triples = list(zip(vals[::3], vals[1::3], vals[2::3]))
        n = len(triples) // sensor_count

        A, G, M = [], [], []
        for i in range(n):
            ax, ay, az = triples[i]
            gx, gy, gz = triples[i + n]
            A.append([round(ax, 3), round(ay, 3), round(az, 3)])
            G.append([round(gx, 3), round(gy, 3), round(gz, 3)])
            if self.imu_sensor == "IMU9":
                mx, my, mz = triples[i + 2*n]
                M.append([round(mx, 3), round(my, 3), round(mz, 3)])

        # --- ONLY NEW LINES: convert triples -> list of {x,y,z} objects ---
        A_obj = [{"x": ax, "y": ay, "z": az} for (ax, ay, az) in A]
        G_obj = [{"x": gx, "y": gy, "z": gz} for (gx, gy, gz) in G]
        M_obj = [{"x": mx, "y": my, "z": mz} for (mx, my, mz) in M] if M else []

        json_data = {
            "Pico_ID": self.picoW_id,
            "Movesense_series": self.ms_series,
            "Timestamp_UTC": time.time(),
            "Timestamp_ms": ts,
            "ArrayAcc": A_obj,
            "ArrayGyro": G_obj,
            "ArrayMagn": M_obj
        }
        imu_queue.enqueue(json_data)

    
    
    
    
    ###############################################################
        
        
        
        

    # --------- Robust HR (variable RR count) ----------
    def _process_hr_data(self, data):
        try:
            avg_hr   = unpack('<f', data[2:6])[0]
            rr_bytes = data[6:]
            cnt      = len(rr_bytes) // 2
            rr_list  = list(unpack('<' + 'H'*cnt, rr_bytes)) if cnt else []
            
            ''''
            json_data = {
                "Movesense_series": self.ms_series,
                "Pico_ID": self.picoW_id,
                "Timestamp_UTC": time.time(),
                "average": avg_hr,
                "rrData": rr_list
            }'''####Commented by Kamal
            ####Added by Kamal
            json_data = {
                "Pico_ID": self.picoW_id,
                "Movesense_series": self.ms_series,
                "Timestamp_UTC": time.time(),
                "Timestamp_ms": time.ticks_ms() if 'time' in dir(time) else 0,  # optional: add if you want like sample
                "Average_BPM": avg_hr,
                "rrData": rr_list
            }
            ###################
            
            
            hr_queue.enqueue(json_data)
        except Exception as e:
            self.log("HR parse error: %s" % e)

    def _process_ecg_data(self, data):
        sample_count = len(data[6:]) // MovesenseDevice.BYTES_PER_ELEMENT
        unpacked     = list(unpack('<BBI' + 'i'*sample_count, data))
        ts           = unpacked[2]
        samples      = unpacked[3:]
        json_data = {
            "Movesense_series": self.ms_series,
            "Pico_ID": self.picoW_id,
            "Timestamp_UTC": time.time(),
            "Timestamp_ms": ts,
            "Samples": samples
        }
        ecg_queue.enqueue(json_data)

    async def disconnect_ble(self):
        unsub_cmds = [
            bytearray([_CMD_UNSUBSCRIBE, self.imu_ref]),
            bytearray([_CMD_UNSUBSCRIBE, self.hr_ref]),
            bytearray([_CMD_UNSUBSCRIBE, self.ecg_ref]),
        ]
        if self.connection and self.connection.is_connected():
            for cmd in unsub_cmds:
                try:
                    await self.write_char.write(cmd)
                    await asyncio.sleep_ms(80)
                except Exception:
                    pass
            await self.connection.disconnect()
            self.log("Disconnected")


