# DexSkin (CoRL 2025)


![DexSkin Demo](assets/teaser.gif)

Suzannah Wistreich*, Baiyu Shi*, Stephen Tian*, Samuel Clarke, Michael Nath, Chengyi Xu, Zhenan Bao, Jiajun Wu  
Stanford University, UAB · CoRL 2025  

🔗 Project page: https://dex-skin.github.io

## 🎉 Open-Source Release: DexSkin — High-Coverage Conformable Robotic Skin for Contact-Rich Manipulation

We are excited to release **DexSkin**! 🎊  

DexSkin is a soft, high-resolution, conformable tactile sensing system designed for **contact-rich robotic manipulation**. It enables dense, localized sensing across complex surfaces and supports learning-based control in real-world settings.

---
## Getting Started

**This repository contains the full stack needed to:**

- **Fabricate the DexSkin sensor** → [hardware/README.md](hardware/README.md)  
- **Set up + interface with the hardware** → [firmware/README.md](firmware/README.md)  
- **Integrate DexSkin with learning pipelines** → [learning/README.md](learning/README.md)  

---

## Repository Overview

```
hardware/
  ├── finger/          # electrode design, finger assembly
  ├── fpcb/            # PCB interconnects
  ├── calibration/     # pneumatic calibration setup (STLs)
  └── readout_pcb/     # readout board Gerbers

firmware/    
  ├── dexskin_finger_firmware.bin       # ESP32 flashing binaries
  └── scripts/                          # readout and visualization scripts

learning/
  └── scripts/        # RL integration example
```
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