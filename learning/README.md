# DexSkin Learning Guide

This guide gives a brief overview of data collection and base policy training with DexSkin. We also provide several sample scripts for RL fine-tuning with DexSkin.

---

## Data Collection
<a name="data-collection"></a>

We collect real-world demonstrations using a teleoperated Franka robot setup equipped with DexSkin sensors.

Each demonstration consists of:
- Robot observations (e.g., proprioception, optional vision via wrist camera)
- DexSkin tactile readings
- Corresponding action trajectories

These demonstrations are used to train policies via imitation learning. In our setup, ~50 human demonstrations per task are sufficient to learn a reasonable base policy.

---

## Base Policy Training
<a name="base-policy-training"></a>

We train a base manipulation policy using a standard **diffusion policy** formulation, though any imitation-learning framework will do.

---

## RL Fine-Tuning with DexSkin
<a name="rl-fine-tuning-with-dexskin"></a>

We provide a small set of **example residual RL scripts** to illustrate how DexSkin can be used in real-world, online learning settings.

These scripts are provided as a **helpful reference implementation**. In particular, reward functions, force thresholds, termination conditions, etc. should be adapted to one's own target task and hardware setup.

### Script Overview

- **[`./scripts/franka_env_with_policy.py`](./scripts/franka_env_with_policy.py)**: Defines a Gym-compatible Franka environment that combines a pretrained diffusion policy with a residual controller. The residual action modifies the base policy's gripper action online, where DexSkin signals are used to compute force-threshold rewards together with an action-magnitude penalty.

- **[`./scripts/residual_inference_train_env.py`](./scripts/residual_inference_train_env.py)**: Constructs a `FrankaEnvWithPolicy` environment (from `franka_env_with_policy.py`) and runs Franka rollouts with the base policy plus a residual controller, which is one of:
  - (default) a learned residual policy
  - `--base_policy_only`: the base policy only
  - `--random_residual`: a random residual baseline  

If neither `--base_policy_only` nor `--random_residual` is set, this script can also continue updating the learned residual policy online.

- **[`./scripts/residual_train.py`](./scripts/residual_train.py)**: Trains a residual SAC policy online on the Franka robot. This script loads the pretrained base policy, constructs the DexSkin-enabled environment (`FrankaEnvWithPolicy` from `franka_env_with_policy.py`), performs online rollouts, updates the residual policy, and periodically saves checkpoints.
