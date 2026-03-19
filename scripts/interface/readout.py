# File name: readout.py
# Author: Baiyu Shi
# Date created: Jan.2025
# Version: v1.3

import serial
import time
import numpy as np
from multiprocessing.shared_memory import SharedMemory
import threading
from serial import SerialException

#the main parameters to change.
PORT = 'COM3'      
BAUDRATE = 460800         #specify the baud rate, default to 460800 with the provided firmware.
NUM_TAXELS = 120            
numRow = 10
numCol = 12
NUM_TAXELS = numRow * numCol       
BASELINE_SAMPLE_NUM = 30      # Number of frames to be averaged for baselines.
FLUSH_FRAME_COUNT = 50        # Number of initial frames to flush to stabilize readouts.
TIMEOUT = 1            
SHM_NAME = 'dexskin_memory' # Shared memory block name

ITEMSIZE = np.dtype(np.float32).itemsize
BUFSIZE = NUM_TAXELS * ITEMSIZE
try:
    shm = SharedMemory(name=SHM_NAME, create=True, size=BUFSIZE)
    print(f"Created New Shared Memory")
except FileExistsError:
    shm = SharedMemory(name=SHM_NAME, create=False)
    print(f"Attached to Existing Memory '{SHM_NAME}'")
shared_frame = np.ndarray((NUM_TAXELS,), dtype=np.float32, buffer=shm.buf)

class MCUController1DShared:
    def __init__(self):
        self.port = PORT
        self.baudrate = BAUDRATE
        self.timeout = TIMEOUT
        self.serial = None

        #baseline and std instantiation.
        self.CurrentFrame = np.zeros(NUM_TAXELS, dtype=np.float32)
        self.baseline = np.zeros(NUM_TAXELS, dtype=np.float32)
        self.std = np.ones(NUM_TAXELS, dtype=np.int32)

        #for calculating FPS.
        self._frame_count = 0
        self._last_fps_time = time.time()
        self.fps = 0.0
        self.running = False

        try:
            self.connect()
            self.init_flush()
            self.start_periodic_task()
        except SerialException as e:
            print(f"SerialException: {e}")

    def connect(self):
        """Open serial port."""
        self.serial = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
        print(f"Serial connected on {self.port} at {self.baudrate}")

    def init_flush(self):
        """
        Discard FLUSH_FRAME_COUNT number of initial frames, then collect
        BASELINE_SAMPLE_NUM frames to compute per-taxel baseline and std.
        """
        flushed = 0
        while flushed < FLUSH_FRAME_COUNT:
            f = self.read_frame(initial=True)
            if f is not None:
                flushed += 1

        frames = []
        while len(frames) < BASELINE_SAMPLE_NUM:
            f = self.read_frame(initial=True)
            if f is not None:
                frames.append(f)

        arr = np.stack(frames, axis=0)
        # compute mean baseline
        self.baseline = np.mean(arr, axis=0)
        var = np.mean((arr - self.baseline)**2, axis=0)
        float_std = np.sqrt(var)
        self.std = float_std.astype(np.int32)
        self.std[self.std < 1] = 1

        print("Baseline computed:", self.baseline)
        print("Std deviation, expected to be below 1:", self.std)

    def read_frame(self, initial=False):
        if self.serial is None:
            raise Exception("Serial not connected.")

        try:
            line = self.serial.readline()
            raw_values = [
                int(val) for val in line.decode('utf-8').rstrip().split(',')
                if val != ''
            ]

            if len(raw_values) != numRow * numCol:
                return None

            frame = np.array(raw_values, dtype=np.int32)
            if frame.size != NUM_TAXELS:
                return None

            if initial:
                return frame

            # normalize and push to shared memory
            self.CurrentFrame = (frame.astype(np.float32) - self.baseline) / self.baseline
            shared_frame[:] = self.CurrentFrame

            self._frame_count += 1
            self._update_fps()
            return None
        
        
        except Exception as e:
            print(f"Error retrieving frame: {e}")
            return None


    def _update_fps(self):
        now = time.time()
        delta = now - self._last_fps_time
        if delta >= 1.0:
            self.fps = self._frame_count / delta
            self._frame_count = 0
            self._last_fps_time = now

    def get_fps(self):
        return self.fps

    def periodic_task(self):
        self.running = True
        interval = 1 / 120
        while self.running:
            self.read_frame(initial=False)
            time.sleep(interval)

    def start_periodic_task(self):
        t = threading.Thread(target=self.periodic_task, daemon=True)
        t.start()
        self.thread = t
        print(f"Started reader thread")

    def stop(self):
        """
        Stop the thread and clean up shared memory.
        Please call this before exiting.
        """
        self.running = False
        if hasattr(self, 'thread'):
            self.thread.join()
        shm.close()
        try:
            shm.unlink()
        except FileNotFoundError:
            pass
        print("Stopped and cleaned up shared memory.")

    def get_frame(self):
        return self.CurrentFrame

if __name__ == '__main__':
    ctrl = MCUController1DShared()
    try:
        while True:
            print(f"FPS: {ctrl.get_fps():.1f}")
            time.sleep(0.5)
    except KeyboardInterrupt:
        #use Keyboard interrupts to end the thread and safely unlink the memory.
        ctrl.stop()
