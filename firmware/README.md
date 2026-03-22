# DexSkin Interfacing Setup Guide

This guide explains:
- [DexSkin firmware setup](#firmware-setup)
- [Board readout and visualization scripts](#readout--visualization-setup)

Compatible with **Windows, macOS, and Linux**

---
## Firmware Setup
<a name="firmware-setup"></a>

### 1. Install FTDI Drivers

If you haven’t worked with embedded systems before, you will need a driver to communicate with the onboard Serial USB. Please visit and install the USB serial drivers:

https://ftdichip.com/drivers/vcp-drivers/

- Select your OS and install
- **Linux:** typically already installed (check via Step #3)

---

### 2. Install Flashing Tool (esptool)

The esptool utility is a universal Python-based application used to communicate and flash in firmware with the ESP32 MCU series.

    pip install esptool

---

### 3. Identify Serial Port

Connect the board via USB-C.

If there are two ports, orient the board such that ESP32 is facing up, antenna is on the right, and the use **top-left port**.

You need to identify the specific port and its name assigned to the connected board:

**Windows**

Right-click the Start menu, select Device Manager, and expand Ports (COM & LPT). Look for USB Serial Port (`COMx`).

**macOS**

    ls /dev/cu.usbserial*

**Linux**

    ls /dev/ttyUSB*

---

### 4. Flash Firmware

Download the provided [`dexskin_finger_firmware.bin`](../firmware/dexskin_finger_firmware.bin). Navigate to the firmware directory and run:

    esptool --chip esp32s3 --port PORT --baud 460800 write_flash 0x0 dexskin_finger_firmware.bin

Replace `PORT` with your device found in Step #3.

**Example (macOS):**

    esptool --chip esp32s3 --port /dev/cu.usbserial-DP05L1VU --baud 460800 write_flash 0x0 dexskin_finger_firmware.bin

---

### 5. Troubleshooting

**Automatic Boot:**  
The board should enter flashing mode automatically once the flash command is executed.

**If “Failed to connect”:**
1. Hold **User/Boot** on the top right of the board.
2. Press + release **Reset** on the bottom right of the board.
3. Release **User/Boot** button before retrying flash command.
4. Retry flash command.


---

### 6. Completion

When the terminal displays

    Hard resetting via RTS pin…

the firmware update is complete.

You may need to press the **Reset** button once more to cleanly power cycle and boot up the system.

---

## Board Readout & Visualization Scripts
<a name="readout--visualization-setup"></a>

### Python Dependencies

We provide two Python scripts for interfacing and visualization DexSkin sensor readings.  
Tested with Python 3.10 (Python ≥ 3.8 supported).

**Required packages:**
- PyQt5 (5.15.11)
- pyqtgraph (0.13.7)
- pyserial (3.5)
- numpy (2.0.2)

**Quick Setup (conda example):**

    conda create -n dexskin_env python=3.10 -y
    conda activate dexskin_env
    pip install PyQt5==5.15.11 pyqtgraph==0.13.7 pyserial==3.5 numpy==2.0.2

---

### Script Overview

The software architecture is split into two independent processes that communicate via shared memory. This allows the readout script to run at high priority for data logging, while the visualization script consumes data for display without slowing down sensor sampling.


- **[`./scripts/readout.py`](./scripts/readout.py)**: Handles serial communication, packet decoding, and baseline normalization. **Always run this script first**, it must be running for the visualization or any other application to access sensor data.



- **[`./scripts/visualize.py`](./scripts/visualize.py)**: Provides a real-time visualization of tactile data for both the left and right fingers. Each taxel is displayed as a white dot, with dot size proportional to the raw sensor values (sampled pressure / force magnitude).

---

### Developer Guide: Interfacing with Shared Memory

The DexSkin system exposes its real-time data buffer to the operating system’s shared memory. This allows developers to write their own scripts (e.g., for Machine Learning inference, ROS robot control, or custom logging) without modifying the core driver.

Any Python script running on the same machine can attach to the shared memory block as a client:


    SHM_NAME = 'dexskin_memory'
    NUM_TAXELS = 120

    try:
        self.shm = shm.SharedMemory(name=SHM_NAME)
        self.frame_buffer = np.ndarray((NUM_TAXELS,), dtype=np.float32, buffer=self.shm.buf)
        print(f"Attached to shared memory: {SHM_NAME}")
    except FileNotFoundError:
        print(f"ERROR: Shared memory block '{SHM_NAME}' not found.")
        print("Please ensure the data providing script is running.")
        sys.exit(1)

Then in other function calls, use:

    self.frame_buffer.copy()

to access latest data.