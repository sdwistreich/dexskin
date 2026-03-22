# DexSkin Learning Guide

This guide gives a brief overview of data collection and base policy training with DexSkin. We also provide several sample scripts for RL fine-tuning with DexSkin.

---

## Data Collection
<a name="data-collection"></a>

We collect real-world demonstrations using a teleoperated robotic setup equipped with DexSkin sensors.

Each demonstration consists of:
- Robot observations (e.g., proprioception, optional vision via wrist camera)
- DexSkin tactile readings
- Corresponding action trajectories

These demonstrations are used to train policies via imitation learning. In our setup, ~50 human demonstrations per task are sufficient to learn a reasonable base policy.

---

## Base Policy Training
<a name="base-policy-training"></a>

We train a base manipulation policy using a standard **diffusion policy** formulation, though any imitation-learning framework will do.


In the online RL setting below, this base policy provides the nominal robot behavior. we keep this policy fixed and learn a small **residual policy** on top.

## RL Fine-Tuning with DexSkin
<a name="rl-fine-tuning-with-dexskin"></a>

We provide a small set of **example residual RL scripts** to illustrate how DexSkin can be used in real-world, online learning settings.

These scripts are provided as a **helpful reference implementation**. Reward functions, force thresholds, termination conditions, etc. should be adapted to one's own target task and hardware setup.

### Script Overview

- **[`./scripts/franka_env_with_policy.py`](./scripts/franka_env_with_policy.py)**: Defines a Gym-compatible real-robot environment that wraps a pretrained base policy together with a residual controller. The residual action modifies the base policy’s gripper behavior, where DexSkin signals are used to compute reward terms such as force-threshold penalties and action-magnitude costs.

- **[`./scripts/residual_inference_train_env.py`](./scripts/residual_inference_train_env.py)**: Runs real-robot rollouts with the base policy plus a residual controller. This script supports evaluation with a learned residual, base-policy-only execution, or random residual actions, and can optionally log trajectories for later inspection.

- **`./scripts/residual_train_env.py`**: Runs online SAC-based residual policy training on the real robot. This script loads the pretrained base policy, constructs the real-robot environment, collects rollouts, updates the residual policy online, and periodically saves checkpoints.


### Provided Scripts

- **[`learning/scripts/franka_env_with_policy.py`](./scripts/franka_env_with_policy.py)**  
  Defines a Gym-compatible Franka environment that combines a pretrained diffusion policy with a residual controller. The residual action modifies the base policy online, and the environment computes tactile- and action-based rewards.

- **[`learning/scripts/residual_inference_train_env.py`](./scripts/residual_inference_train_env.py)**  
  Runs the real-robot environment with either:
  - a learned residual policy,
  - the base policy only, or
  - a random residual baseline.  

  This script is useful for evaluation, trajectory logging, and comparing residual-policy behavior against non-RL baselines.

- **[`learning/scripts/residual_train.py`](./scripts/residual_train.py)**  
  Trains a residual SAC policy online on the real robot. This script loads the base policy, constructs the DexSkin-enabled environment, and updates the residual controller from replay-buffer data collected during interaction.



---