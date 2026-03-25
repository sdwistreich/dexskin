# Hardware

This folder contains DexSkin hardware assets for fabricating the sensor, ordering the PCBs, and reproducing the calibration setup described in the paper.

## Release Status

Currently available in this folder:

- Finger electrode SVG layout
- Flexible PCB manufacturing files for the sensor array interconnects
- Readout PCB Gerbers
- Calibration fixture STLs

In progress (target: mid-April 2026):

- Readout board BOM
- Calibration fabrication guide
- Assembly and ordering recommendations

## Folder Guide

### `finger/`

- `DexSkin_Electrode_design.svg`: Layout of top and bottom capacitive electrode layers for the finger design described in the paper
  - *For researchers interested in access to the stretchable cylindrical DexSkin form described in the paper, please contact Baiyu Shi at the Bao Group (`baiyushi@stanford.edu`) regarding sample availability.*

### `fpcb/`

- `dexskin_5pin_row_interconnection.zip` and `dexskin_12pin_column_interconnection.zip`: Gerber-ready flexible PCB files for the polyimide sensor array interconnects. Design specifications:
  - Intended for a 5 x 12 taxel layout, mountable on flat or cylindrical grippers
  - 2.5 mm x 2.5 mm square taxels 
  - 1.5 mm spacing between neighboring taxels

Layer notes for the flexible PCB fabrication files:

- `Mechanical Layer 1`: PCB outline
- `Top Overlay`: top EMI shielding film outline
- `Bottom Overlay`: bottom stiffener outline

### `readout_pcb/`

- `dexskin_readout_pcb_v1.1.zip`
- Manufacturing files for the 4-layer readout board used to read both finger arrays simultaneously
- Prepared as a fabrication-ready Gerber archive

### `calibration/`

- `Final_Mold_Top.stl`
- `Final_Mold_Bot.stl`
- `Final_Mold_Supporting_Platform.stl`
- `D20.8_Inner_Sleeve_TOP.stl`
- `D20.8_Inner_Sleeve_BOT.stl`
- 3D-printable parts for molding Ecoflex and building airtight calibration chambers
- Used for the 3-minute transfer calibration procedure described in the paper across sensor instances from different fabrication batches

## Assembly Guide
Assembly overview:

> Placeholder: [pending FPCB assembly GIF here]

- Materials: two fabricated fPCB pieces, thin double-sided tape, a nonconductive dielectric layer, and a sharp scalpel for trimming the dielectric and tape
- In our builds, we use a sandpaper-structured midlayer as the dielectric
- First, apply double-sided tape around the boundary of one fPCB piece
- Second, laminate the dielectric layer onto the other fPCB piece
- Finally, manually align the top and bottom electrode layers by matching the exposed copper square taxels, then press around the edges to ensure the double-sided tape bonds the two pieces together securely
- After assembly, follow [`../firmware/README.md`](../firmware/README.md) and run [`../firmware/scripts/readout.py`](../firmware/scripts/readout.py) together with [`../firmware/scripts/visualize.py`](../firmware/scripts/visualize.py) to verify that the sensor reads out correctly and view the real-time visualization

> Placeholder: [pending FPCB interaction GIF here]

## Manufacturing Notes

- The ZIP archives in `fpcb/` and `readout_pcb/` are intended for direct submission to a PCB manufacturer.
- If your manufacturer asks for layer clarification on the flexible PCB files, you may use the layer notes above.

## Planned Additions

- Readout PCB BOM, including alternative parts where distributor availability changes
- Calibration fixture build notes
- Step-by-step assembly guidance

Last updated: March 25, 2026
