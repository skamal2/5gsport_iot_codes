


# Lightweight FIFO with bounded size to protect heap
class SimpleQueue:
    def __init__(self, max_len=50):
        self._buf = []
        self._max = max_len
    def enqueue(self, x):
        self._buf.append(x)
        if len(self._buf) > self._max:
            # drop oldest to prevent RAM growth
            self._buf.pop(0)
    def dequeue(self):
        return self._buf.pop(0) if self._buf else None
    def is_empty(self):
        return not self._buf
    def __len__(self):
        return len(self._buf)

# Smaller queues = lower memory pressure
imu_queue  = SimpleQueue(20)
ecg_queue  = SimpleQueue(20)
hr_queue   = SimpleQueue(10)
gnss_queue = SimpleQueue(10)

class State:
    def __init__(self):
        self.running_state = True
        self.network_connection_state = False
        self.trigger_connecting_network = False
        self.movesense_detect = False
        self.trigger_ble_scan = True

state = State()

