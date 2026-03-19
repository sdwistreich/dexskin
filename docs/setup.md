# DexSkin Interfacing Setup Guide

This guide explains:
- How to flash the DexSkin finger firmware
- How to use the board readout and visualization scripts

Compatible with **Windows, macOS, and Linux**

---

## 1. Install FTDI Drivers

If you haven’t worked with embedded systems before, you will need a driver to communicate with the onboard Serial USB. Please visit and install the USB serial drivers:

https://ftdichip.com/drivers/vcp-drivers/

- Select your OS and install
- **Linux:** typically already installed (check via Step #3)

---

## 2. Install Flashing Tool (esptool)

The esptool utility is a universal Python-based application used to communicate and flash in firmware with the ESP32 MCU series.

    pip install esptool

---

## 3. Identify Serial Port

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

## 4. Flash Firmware

Download the provided `firmware/dexskin_finger_firmware.bin` file. Navigate to the firmware directory and run:

    esptool --chip esp32s3 --port PORT --baud 460800 write_flash 0x0 dexskin_finger_firmware.bin

Replace `PORT` with your device found in Step #3.

**Example (macOS):**

    esptool --chip esp32s3 --port /dev/cu.usbserial-DP05L1VU --baud 460800 write_flash 0x0 dexskin_finger_firmware.bin

---

## 5. Troubleshooting

**Automatic Boot:**  
The board should enter flashing mode automatically once the flash command is executed.

**If “Failed to connect”:**
1. Hold **User/Boot** on the top right of the board.
2. Press + release **Reset** on the bottom right of the board.
3. Release **User/Boot** button before retrying flash command.
4. Retry flash command.


---

## 6. Completion

When the terminal displays

    Hard resetting via RTS pin…

the firmware update is complete.

You may need to press the **Reset** button once more to cleanly power cycle and boot up the system.
