# DexSkin Learning Guide

This guide explains:
- [Data collection](#data-collection)
- [Base policy training](#base-policy-training)

These steps provide the foundation for learning-based manipulation with DexSkin.

---

## Data Collection
<a name="data-collection"></a>

We collect real-world demonstrations using a teleoperated robotic setup equipped with DexSkin sensors.

Each demonstration consists of:
- Robot observations (e.g., proprioception, optional vision via wrist camera)
- DexSkin tactile readings (all taxels)
- Corresponding action trajectories

These demonstrations are used to train an initial policy via imitation learning. In our setup, ~50 human demonstrations per task are sufficient to learn a reasonable base policy.

---

## Base Policy Training
<a name="base-policy-training"></a>

We train a base manipulation policy using a standard **diffusion policy** formulation, though any imitation-learning framework will do.


## RL Fine-Tuning with DexSkin

---