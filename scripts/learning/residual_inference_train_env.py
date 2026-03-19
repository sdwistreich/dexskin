"""
Residual policy runner for Franka real-robot experiments.

Loads configs, constructs the IL policy + FrankaEnvWithPolicy, and optionally
runs a learned residual SAC policy (or a random / identity residual) over
episodes. Can also log trajectories via the observable observation buffer.
"""

import sys
import os
import time
import copy
import argparse
import random

import yaml
import numpy as np
import torch
from termcolor import colored
from tqdm import tqdm
from omegaconf import OmegaConf

from stable_baselines3 import SAC
from stable_baselines3.common.logger import configure

sys.path.insert(0, "../../")
from src.franka_kdm.env.franka_env_with_policy import FrankaEnvWithPolicy
from src.franka_kdm.observables.observable import PointCloudAndRobotObservable
from src.franka_kdm.policy import DiffusionImagePolicy


# allows arbitrary python code execution in configs using the ${eval:''} resolver
OmegaConf.register_new_resolver("eval", eval, replace=True)

NUM_EPISODES = 1000
BATCH_SIZE = 256


def load_config(file_path):
    """
    Load an OmegaConf config file.

    Args:
        file_path (str): path to yaml config

    Returns:
        config (OmegaConf): loaded config
    """
    print(colored(f"Loading configuration from {file_path}", "blue"))
    return OmegaConf.load(file_path)


def get_arguments(config):
    """
    Create CLI arguments from a base config, with a few extra flags.

    Args:
        config (OmegaConf): base config

    Returns:
        args (argparse.Namespace): parsed args
    """
    parser = argparse.ArgumentParser(description="Process configuration.")
    for key, value in config.items():
        if isinstance(value, list):
            value = ",".join(value)
        parser.add_argument(f"--{key}", default=value, type=type(value), help=f"Default: {value}")
    
    parser.add_argument("--use_tactile", action="store_true", help="Use tactile sensing")
    parser.add_argument("--checkpoint", type=str, help="Path to the checkpoint")
    parser.add_argument("--log_trajectory", action="store_true", help="whether to log the trajectory")
    parser.add_argument("--buffer_init", type=str, help="path to buffer init") 

    # inference / eval switches
    parser.add_argument("--rl_checkpoint", type=str, help="Path to rl checkpoint")
    parser.add_argument("--base_policy_only", action="store_true", help="whether to use base policy only or not (no residual)")
    parser.add_argument("--random_residual", action="store_true", help="use random 'residual' scaling (uniform [0.8, 1.2]) ")

    args = parser.parse_args()

    return args

def main():
    """
    Entry point for running residual + IL control loop on the real robot.
    """

    def save_obs_buffer(timestamp):
        """
        Save observable observation buffer to a pickle file.

        Args:
            timestamp (str): timestamp for filename

        Returns:
            fname (str or None): basename of saved file, or None if nothing saved
        """
        if observable.save_all_obs and len(observable.obs_buffer) > 0:
            filename = os.path.join(log_dir, f"obs_buffer_{timestamp}.pkl")
            observable.write_obs_to_pickle(filename)
            print(f"Observation buffer saved to {filename}")
            return os.path.basename(filename)
        return None

    
    def log_iteration_info(iteration, force, action, composite, max_gripper_close, buffer_filename):
        """
        Append per-episode reward statistics to a local log file.
        """
        log_filename = os.path.join(log_dir, "iteration_logs.txt")
        with open(log_filename, "a") as log_file:                    
            log_file.write(f"Iteration: {iteration}, "
                        f"Force Reward: {force}, "
                        f"Action Reward: {action}, "
                        f"Composite Reward: {composite}, "
                        f"Max Gripper Close: {max_gripper_close}, "
                        f"Obs Buffer Log: {buffer_filename}\n")


    # session logging directory
    log_dir = "/your/log/path/"
    os.makedirs(log_dir, exist_ok=True)

    config = load_config("../../cfg/your_config.yaml")
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
    _ = OmegaConf.load(args.model_base_cfg)

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

    logger = configure(folder="./logs", format_strings=["stdout", "csv"])

    residual_policy = SAC("MlpPolicy", env=franka_env, learning_rate=0.0, verbose=1)
    residual_policy.set_logger(logger)
    replay_buffer = residual_policy.replay_buffer

    if args.rl_checkpoint:
        residual_policy = SAC.load(args.rl_checkpoint)
        residual_policy.lr_schedule = lambda x: 0
        residual_policy.target_update_interval = 100000000000000
        residual_policy.set_logger(logger)
        replay_buffer = residual_policy.replay_buffer

        if args.buffer_init is not None and os.path.exists(args.buffer_init):
            replay_buffer = torch.load(args.buffer_init)
            residual_policy.replay_buffer = replay_buffer
            print(f"Loaded replay buffer with {replay_buffer.size()} transitions")


    # warmup: gripper + tactile reads + confirm robot state stream
    franka_env.close_gripper()
    time.sleep(1)
    print("Test open gripper")
    franka_env.open_gripper()
    time.sleep(1)

    for _ in range(10):
        data = observable.get_tactile()
        print(data)
        time.sleep(0.01)

    obs = observable.get_obs(get_points=False, get_tactile=using_tactile, depth=False)
    if len(obs["eef_pos"]) == 0:
        raise SystemError("Robot state not received. Please check robot!")

    try:
        for k in range(NUM_EPISODES):
            obs = franka_env.reset()
            done = False

            with tqdm(total=franka_env.max_timeout, desc="Steps in Episode", leave=False) as pbar:
                while not done:
                    obs = np.array(obs, dtype=np.float32)

                    # select residual action: learned policy, identity (IL only), or random scaling
                    if args.base_policy_only:
                        residual_action = 1
                    elif args.random_residual:
                        residual_action = random.uniform(0.8, 1.2)
                    else:
                        residual_action, _ = residual_policy.predict(obs)

                    next_obs, reward, term, trun, dropped = franka_env.step(residual_action) 
                    done = (term or trun)

                    # add transitions until buffer has enough samples to train on
                    if (not args.base_policy_only) and (not args.random_residual):
                        buffer_action = residual_policy.policy.scale_action(residual_action)
                        while replay_buffer.size() < BATCH_SIZE:
                            replay_buffer.add(
                                copy.deepcopy(obs),
                                copy.deepcopy(next_obs),
                                copy.deepcopy(buffer_action),
                                copy.deepcopy(reward),
                                copy.deepcopy(done),
                                [{}],
                            )

                    if args.log_trajectory:
                        residual_info = {
                            "force_reward": franka_env.composite_reward.force_reward,
                            "action_reward": franka_env.composite_reward.action_reward,
                            "composite_reward": reward,
                            "force_reward_total": franka_env.force_reward_total,
                            "action_reward_total": franka_env.action_reward_total,
                            "composite_reward_total": franka_env.composite_reward_total,                            
                            "residual_action": residual_action,
                            "il_action": franka_env.current_il_action.tolist()
                        }
                        franka_env.observable.log(franka_env.next_obs_dict, residual_info)

                    # update residual policy from replay buffer
                    if (not args.base_policy_only) and (not args.random_residual):
                        if replay_buffer.size() >= BATCH_SIZE:
                            num_grad_steps = 5
                            residual_policy.train(num_grad_steps, batch_size=BATCH_SIZE)

                    obs = next_obs
                    pbar.update(1)
                    
            print(
                "force, action, composite reward",
                franka_env.force_reward_total,
                franka_env.action_reward_total,
                franka_env.composite_reward_total,
            )

            franka_env.clear_cache()

            timestamp = time.strftime("%Y%m%d-%H%M%S")
            filename = None
            if args.log_trajectory:
                filename = save_obs_buffer(timestamp)
                log_iteration_info(
                    k,
                    franka_env.force_reward_total,
                    franka_env.action_reward_total,
                    franka_env.composite_reward_total,
                    franka_env.max_gripper_close,
                    filename,
                )

            franka_env.observable.ESP32.stop_periodic_task()
            franka_env.observable.ESP32.calibrate()
            franka_env.observable.ESP32.start_periodic_task(update_freq=120)

            print("Waiting after episode end, press enter to continue")
            input()
                    

    except KeyboardInterrupt:
        # Save only if we're actually running a learned residual policy
        if (not args.base_policy_only) and (not args.random_residual):
            print("\nCtrl+C detected. Saving residual policy before exit...")
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            residual_policy.save(os.path.join(log_dir, f"trained_residual_policy_{timestamp}.zip"))

        if args.log_trajectory:
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            save_obs_buffer(timestamp)

        sys.exit(0)

if __name__ == "__main__":
    main()