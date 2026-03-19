# DexSkin (CoRL 2025)

## 🎉 Open-Source Release: DexSkin — High-Coverage Conformable Robotic Skin for Contact-Rich Manipulation

We are excited to release **DexSkin**! 🎉  

DexSkin is a soft, high-resolution, conformable tactile sensing system designed for **contact-rich robotic manipulation**. It enables dense, localized sensing across complex surfaces and supports learning-based control in real-world settings.

This repository contains the full stack needed to:
- fabricate the sensor  
- interface with the hardware  
- stream and visualize tactile data  
- integrate with downstream learning pipelines  

---

## Authors

Suzannah Wistreich*, Baiyu Shi*, Stephen Tian*,  
Samuel Clarke, Michael Nath, Chengyi Xu, Zhenan Bao, Jiajun Wu  

(* equal contribution)

**Stanford University, UAB**  
**Conference on Robot Learning (CoRL), 2025**

---

## Repository Structure

```
hardware/        # Sensor design (electrodes, fPCB, calibration rigs)
firmware/        # ESP32 firmware + flashing binaries
scripts/         # Readout + visualization interfaces
docs/            # Setup + usage documentation
```

---

## What’s Included

- **Sensor design files**  
  Electrode layouts, flexible PCB designs, and fabrication assets  

- **Calibration hardware**  
  3D-printable parts for pneumatic force calibration  

- **Firmware + readout stack**  
  ESP32 firmware + real-time data streaming  

- **Visualization tools**  
  Live tactile visualization for debugging and analysis  

- **Developer interface**  
  Shared-memory API for integrating with robotics / ML pipelines  

---

## Getting Started

👉 See the setup guide:  
[docs/setup.md](docs/setup.md)

---

## Project Page

More details, videos, and results:  
https://sdwistreich.github.io/dexskin/

---

## BibTeX

If you found this open-source helpful, please consider citing:
```
@inproceedings{wistreich2025dexskin,
    title={DexSkin: High-Coverage Conformable Robotic Skin for Learning Contact-Rich Manipulation},
    author={Suzannah Wistreich and Baiyu Shi and Stephen Tian and Samuel Clarke and Michael Nath and Chengyi Xu and Zhenan Bao and Jiajun Wu},
    booktitle={Conference on Robot Learning (CoRL)},
    year={2025},
    eprint={2509.18830},
    archivePrefix={arXiv},
    primaryClass={cs.RO},
    url={https://arxiv.org/abs/2509.18830},
}
```