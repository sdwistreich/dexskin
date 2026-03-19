"""
Residual policy runner for Franka real-robot experiments (online SAC residual).

Loads configs, constructs the IL policy + FrankaEnvWithPolicy, and runs a SAC
residual policy online (from scratch or fine-tuning). Optionally logs
trajectories via the observable observation buffer.
"""

import sys
import os
import time
import warnings
import copy
import argparse

import yaml
import numpy as np
import torch
import wandb
from termcolor import colored
from tqdm import tqdm
from omegaconf import OmegaConf

from stable_baselines3 import SAC
from stable_baselines3.common.logger import configure

sys.path.insert(0, "../../")
from src.franka_kdm.env.franka_env_with_policy import FrankaEnvWithPolicy
from src.franka_kdm.observables.observable import PointCloudAndRobotObservable
from src.franka_kdm.policy import DiffusionImagePolicy

OmegaConf.register_new_resolver("eval", eval, replace=True)

NUM_EPISODES = 1000
BATCH_SIZE = 256
NUM_GRAD_STEPS = 5
SAVE_EVERY = 5


def load_config(file_path):
    """
    Load an OmegaConf config file.

    Args:
        path (str): Path to yaml config.

    Returns:
        OmegaConf: Loaded config.
    """
    print(colored(f"Loading configuration from {file_path}", "blue"))
    return OmegaConf.load(file_path)


def get_arguments(config):
    """
    Create CLI args from a base OmegaConf config, with a few extra flags.

    Args:
        config (OmegaConf): Base config.

    Returns:
        argparse.Namespace: Parsed CLI args.
    """
    parser = argparse.ArgumentParser(description="Residual SAC runner for Franka real robot.")
    for k, v in config.items():
        if isinstance(v, list):
            v = ",".join(v)
        parser.add_argument(f"--{k}", default=v, type=type(v), help=f"Default: {v}")

    parser.add_argument("--use_tactile", action="store_true", help="Use tactile sensing.")
    parser.add_argument("--checkpoint", type=str, required=True, help="IL checkpoint dir/path.")
    parser.add_argument("--log_trajectory", action="store_true", help="Log observable buffer to disk.")
    parser.add_argument("--buffer_init", type=str, help="Path to a saved replay buffer (torch.load).")
    parser.add_argument("--rl_checkpoint", type=str, help="SAC checkpoint to fine-tune (optional).")
    return parser.parse_args()


class FakeLoggerForWandb:
    """
    Minimal SB3-style logger that forwards recorded scalars to Weights & Biases.
    """
    def __init__(self):
        self._log_dict = {}
    
    def record(self, name, values, **kwargs):
        """
        Record a value.

        Args:
            name (str): Metric name.
            value: Metric value.
        """
        self._log_dict[name] = values
    
    def add_dict(self, d):
        """
        Merge a dict of scalars into the current pending log dict.

        Args:
            d (dict): Metrics to merge.
        """
        self._log_dict.update(d)

    def flush(self):
        """
        Flush pending scalars to W&B.
        """
        if self._log_dict:
            wandb.log(self._log_dict)
            self._log_dict = {}

def main():
    """
    Entry point for online residual SAC training with a base IL policy on the real robot.
    """
    
    def save_obs_buffer(ts: str):
        """
        Save observable observation buffer to a pickle file (if enabled).

        Args:
            ts (str): Timestamp string used in filename.

        Returns:
            str | None: Basename of saved file, or None if nothing saved.
        """
        if observable.save_all_obs and len(observable.obs_buffer) > 0:
            p = os.path.join(log_dir, f"obs_buffer_{ts}.pkl")
            observable.write_obs_to_pickle(p)
            print(f"Observation buffer saved to {p}")
            return os.path.basename(p)
        return None

    
    def log_iteration_info(i, force, action, comp, max_gc, buf):
        """
        Append per-episode summary stats to a local text log.

        Args:
            i (int): Episode index.
            force (float): Force reward total.
            action (float): Action reward total.
            comp (float): Composite reward total.
            max_gc (float): Max gripper close.
            buf (str | None): Obs buffer filename (if any).
        """
        p = os.path.join(log_dir, "iteration_logs.txt")
        with open(p, "a") as f:               
            f.write(f"Iteration: {i}, "
                        f"Force Reward: {force}, "
                        f"Action Reward: {action}, "
                        f"Composite Reward: {comp}, "
                        f"Max Gripper Close: {max_gc}, "
                        f"Obs Buffer Log: {buf}\n")


    # saving dir for this session
    log_dir = "/your/log/path"
    os.makedirs(log_dir, exist_ok=True)
    wandb.init(project="franka-kdm-residual", name=f"residual-training-{time.strftime('%Y%m%d-%H%M%S')}")

    config = load_config("../../cfg/real_robot_defaults_tactile.yaml")
    args = get_arguments(config)

    using_tactile = bool(args.use_tactile)
    args.sampler_model_cfg = (
        "train_diffusion_unet_real_hybrid_workspace.yaml"
        if using_tactile
        else "train_diffusion_unet_real_hybrid_workspace_notac.yaml"
    )

    if not os.path.exists(args.cam_extrinsics):
        raise ValueError(f"Camera calibration file {args.cam_extrinsics} does not exist")
    with open(args.cam_extrinsics, "r") as f:
        transformations = [item["transformation"] for item in yaml.safe_load(f)]

    if not os.path.exists(args.cam_intrinsics):
        raise ValueError(f"Camera calibration file {args.cam_intrinsics} does not exist")
    with open(args.cam_intrinsics, "r") as f:
        intrinsic_matrices = [np.array(item["color"]) for item in yaml.safe_load(f).values()]

    robot_cfg = OmegaConf.load(args.robot_configs)

    il_policy = DiffusionImagePolicy(
        base_config_file=args.model_base_cfg,
        sampler_config_file=args.sampler_model_cfg,
        classifier_config_file=args.classifier_model_cfg,
        data_config_file=args.data_cfg,
        intrinsics=np.array(intrinsic_matrices),
        extrinsics=np.array(transformations),
        num_samples=1,
        workspace_bounds=args.workspace_bounds,
        checkpoint_dir=args.checkpoint,
        controller_type=None
    )

    franka_env = FrankaEnvWithPolicy(
        il_policy=il_policy, 
        observable=None, 
        using_tactile=using_tactile, 
        skip_reset=False, 
        gripper_type="ssg48",
        **robot_cfg
    )

    observable = PointCloudAndRobotObservable(
        camera_ids=args.camera_serials,
        camera_intrinsics=intrinsic_matrices,
        camera_transformations=transformations,
        pointcloud_sampled_points=1024,
        robot_env=franka_env,
        pointcloud_filter_z_min=0.01,
        save_all_obs=args.log_trajectory
    )

    franka_env.observable = observable
    il_policy.controller_type = franka_env.controller_type

    franka_env.verbose = True
    franka_env.reset()

    # residual policy: from scratch or fine-tune
    if args.rl_checkpoint:
        residual_policy = SAC.load(args.rl_checkpoint)
    else:
        residual_policy = SAC("MlpPolicy", env=franka_env, verbose=1)

    residual_policy.set_logger(FakeLoggerForWandb())

    # possibly init replay buffer
    if args.buffer_init and os.path.exists(args.buffer_init):
        residual_policy.replay_buffer = torch.load(args.buffer_init)
        print(f"Loaded replay buffer with {residual_policy.replay_buffer.size()} transitions")

    replay_buffer = residual_policy.replay_buffer

    # warmup: gripper + tactile reads + confirm robot state stream
    franka_env.close_gripper()
    time.sleep(1)
    franka_env.open_gripper()
    time.sleep(1)

    for _ in range(10):
        print(observable.get_tactile())
        time.sleep(0.01)

    obs_dict = observable.get_obs(get_points=False, get_tactile=using_tactile, depth=False)
    if len(obs_dict["eef_pos"]) == 0:
        raise SystemError("Robot state not received. Please check robot!")

    try:
        for ep in range(NUM_EPISODES):
            obs = franka_env.reset()
            done = False
            print(f"Iteration {ep + 1}/{NUM_EPISODES}")

            with tqdm(total=franka_env.max_timeout, desc="Steps in Episode", leave=False) as pbar:
                while not done:
                    obs = np.array(obs, dtype=np.float32)
                    residual_action, _ = residual_policy.predict(obs)

                    next_obs, reward, term, trun, _ = franka_env.step(residual_action)
                    done = (term or trun)

                    if done:
                        fail_reward = -10
                        response = input(f"End of trajectory, add {fail_reward} failure penalty? (y, Enter to skip)")
                        if 'y' in response.lower():
                            reward += fail_reward
                            franka_env.composite_reward_total += fail_reward    

                    buffer_action = residual_policy.policy.scale_action(residual_action)
                    replay_buffer.add(
                        copy.deepcopy(obs),
                        copy.deepcopy(next_obs),
                        copy.deepcopy(buffer_action),
                        copy.deepcopy(reward),
                        copy.deepcopy(done),
                        [{}],
                    )

                    if args.log_trajectory:
                        franka_env.observable.log(
                            franka_env.next_obs_dict,
                            {
                                "force_reward": franka_env.composite_reward.force_reward,
                                "action_reward": franka_env.composite_reward.action_reward,
                                "composite_reward": reward,
                                "force_reward_total": franka_env.force_reward_total,
                                "action_reward_total": franka_env.action_reward_total,
                                "composite_reward_total": franka_env.composite_reward_total,
                                "residual_action": np.asarray(residual_action).tolist(),
                                "il_action": franka_env.current_il_action.tolist(),
                            },
                        )

                    if replay_buffer.size() >= BATCH_SIZE:
                        residual_policy.train(NUM_GRAD_STEPS, batch_size=BATCH_SIZE)

                    obs = next_obs
                    pbar.update(1)
                    residual_policy.logger.flush()

            # reward totals for trajectory
            print(
                "force, action, composite reward",
                franka_env.force_reward_total,
                franka_env.action_reward_total,
                franka_env.composite_reward_total,
            )
            
            franka_env.clear_cache()

            # save obs buffer
            ts = time.strftime("%Y%m%d-%H%M%S")
            residual_policy.logger.add_dict(
                {
                    "force_reward_total": franka_env.force_reward_total,
                    "action_reward_total": franka_env.action_reward_total,
                    "composite_reward_total": franka_env.composite_reward_total,
                    "max_gripper_close": franka_env.max_gripper_close,
                }
            )
            
            buf = None
            if args.log_trajectory:
                buf = save_obs_buffer(ts)
                log_iteration_info(
                    ep,
                    franka_env.force_reward_total,
                    franka_env.action_reward_total,
                    franka_env.composite_reward_total,
                    franka_env.max_gripper_close,
                    buf,
                )

            if ep % SAVE_EVERY == 0:
                residual_policy.save(os.path.join(log_dir, f"trained_residual_policy_{ts}_iter_{ep}.zip"))

            franka_env.observable.ESP32.stop_periodic_task()
            franka_env.observable.ESP32.calibrate()
            franka_env.observable.ESP32.start_periodic_task(update_freq=120)

            print("Waiting after episode end, press enter to continue")
            input()
                
    except KeyboardInterrupt:
        print("\nCtrl+C detected. Saving residual policy before exit...")
        ts = time.strftime("%Y%m%d-%H%M%S")
        residual_policy.save(os.path.join(log_dir, f"trained_residual_policy_{ts}.zip"))
        if args.log_trajectory:
            save_obs_buffer(ts)
        raise

if __name__ == "__main__":
    main()