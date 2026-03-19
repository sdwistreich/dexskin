# DexSkin (CoRL 2025)

<p align="center">
Suzannah Wistreich*, Baiyu Shi*, Stephen Tian*, Samuel Clarke, Michael Nath, Chengyi Xu, Zhenan Bao, Jiajun Wu<br>
(* equal contribution)<br><br>
Stanford University, UAB<br>
Conference on Robot Learning (CoRL), 2025
</p>

🔗 Project page: https://dex-skin.github.io

## 🎉 Open-Source Release: DexSkin — High-Coverage Conformable Robotic Skin for Contact-Rich Manipulation

We are excited to release **DexSkin**! 🎊  

DexSkin is a soft, high-resolution, conformable tactile sensing system designed for **contact-rich robotic manipulation**. It enables dense, localized sensing across complex surfaces and supports learning-based control in real-world settings.

**This repository contains the full stack needed to:**
- fabricate the DexSkin sensor  
- interface with readout hardware  
- stream and visualize tactile data  
- integrate DexSkin with downstream learning pipelines  

---

## Getting Started

👉 See the setup guide:  
[docs/setup.md](docs/setup.md)

---


## Repository Overview

```
hardware/        # Sensor design (electrodes, fPCB, calibration rigs)
firmware/        # ESP32 firmware + flashing binaries
scripts/         # Readout + visualization interfaces
docs/            # Setup + usage documentation
```

This repository includes:
- **Sensor design files** (electrodes, fPCB, fabrication assets)  
- **Calibration hardware** (3D-printable pneumatic setup)  
- **Firmware + readout stack** (ESP32 + real-time streaming)  
- **Visualization tools** (live tactile display)  
- **Developer interface** (shared memory for ML / robotics integration)  


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