# DexSkin Setup Guide

This guide explains:
- how to flash the DexSkin finger firmware
- how to use the readout and visualization scripts

Compatible with **Windows, macOS, and Linux**

---

## 1. Install FTDI Drivers

If you haven’t worked with embedded systems before, install the USB serial drivers:

https://ftdichip.com/drivers/vcp-drivers/

- Select your OS and install
- **Linux:** typically already installed

---

## 2. Install Flashing Tool (esptool)

    pip install esptool

---

## 3. Identify Serial Port

Connect the board via USB-C.

If there are two ports:
- ESP32 facing up
- antenna on the right
- use **top-left port**

Find your port:

**Windows**
- Device Manager → Ports → `COMx`

**macOS**

    ls /dev/cu.usbserial*

**Linux**

    ls /dev/ttyUSB*

---

## 4. Flash Firmware

Navigate to the firmware directory and run:

    esptool --chip esp32s3 --port PORT --baud 460800 write_flash 0x0 dexskin_finger_firmware.bin

Replace `PORT` with your device.

**Example (macOS):**

    esptool --chip esp32s3 --port /dev/cu.usbserial-DP05L1VU --baud 460800 write_flash 0x0 dexskin_finger_firmware.bin

---

## 5. Troubleshooting

**If “Failed to connect”:**
1. Hold **User/Boot**
2. Press + release **Reset**
3. Release **User/Boot**
4. Retry

**Automatic mode:**  
Board should enter flashing mode automatically.

---

## 6. Completion

Look for:

    Hard resetting via RTS pin…

Firmware is now installed.

Press **Reset** once more if needed to reboot cleanly.