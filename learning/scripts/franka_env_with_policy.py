"""
Residual Policy Environment for Franka Robot.

Defines a Gym-compatible environment that integrates a pretrained policy
with a residual RL controller for refined manipulation control.

Note: This example corresponds to the gentle manipulation task (Sec. 4.3),
where the robot must place a real blueberry into a basket without damage.
Reward definitions, weights, and constants should be tuned for other tasks 
and environments.
"""


import sys
import time
import copy
import numpy as np
import pandas as pd

from gymnasium import Env, spaces

sys.path.insert(0, "../../")
from src.franka_kdm.observables.observable import PointCloudAndRobotObservable
from src.franka_kdm.policy import DiffusionImagePolicy
from src.franka_kdm.env.franka_env import FrankaEnv
from scripts.real_robot.residual.reward import CompositeReward, ForceThresholdReward, ActionMagnitudeReward


# Robot and Environment constants
CURRENT               = 400
MAX_TIMEOUT           = 425  
FRANKA_ACT_LEN        = 8  
GRIPPER_ACTION_SPACE  = 0.2    # range for residual adjustment of gripper action
TERM_TOLERANCE        = 0.30   # position tolerance for reaching the basket
TERM_HEIGHT           = 0.45   # end-stage lift required for success
BASKET_REACH_POS      = np.array([0.14570156, 0.40587807, 0.37084416,
                                  -1.6586009, -0.08961675, 2.2776477, 0.841698])

# Reward constants
FORCE_THRESHOLD       = 0.1     # contact force limit
FORCE_COEFF           = 1.0     # tune coeffs for weight in reward calculation
ACTION_COEFF          = 0.01
COMPOSITE_COEFF       = 1.0


class FrankaEnvWithPolicy(FrankaEnv, Env): 
    """
    Class for environment combining pretrained policy with RL controller.

    Args:
        il_policy (DiffusionImagePolicy): pretrained imitation policy.
        observable (PointCloudAndRobotObservable): provides tactile and visual inputs.
        using_tactile (bool): whether to include tactile data in observations.
        max_timeout (int): maximum number of steps before truncation.
        *args, **kwargs: passed from parent FrankaEnv.
    """

    def __init__(
        self, 
        il_policy: DiffusionImagePolicy,      
        observable: PointCloudAndRobotObservable,
        using_tactile=True,
        max_timeout=MAX_TIMEOUT,        
        *args,  
        **kwargs
    ):

        super().__init__(*args, **kwargs)
        
        self.il_policy = il_policy 
        self.observable = observable
        self.using_tactile = using_tactile
        self.max_timeout = max_timeout

        # Action and observation spaces
        self.obs_size = 181  # includes 120-taxel DexSkin sensor
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(self.obs_size,), dtype=np.float32,
        )
        self.action_size = FRANKA_ACT_LEN
        self.action_space = spaces.Box(
            low=np.array([1 - GRIPPER_ACTION_SPACE], dtype=np.float32),
            high=np.array([1 + GRIPPER_ACTION_SPACE], dtype=np.float32),
            dtype=np.float32
        )
        self.gripper_action_space = GRIPPER_ACTION_SPACE

        # Policy and step tracking
        self.current_il_action = np.zeros(FRANKA_ACT_LEN)
        self.next_il_action = np.zeros(FRANKA_ACT_LEN)
        self.previous_obs = None
        self.inferred_robot_actions = None
        self.step_count = 0

        # State tracking
        self.next_obs_dict = None
        self.joint_pos = None
        self.basket_reached = False
        self.in_transit = False

        # Reward setup
        self.force_reward = ForceThresholdReward(threshold=FORCE_THRESHOLD, coefficient=FORCE_COEFF)
        self.action_reward = ActionMagnitudeReward(coefficient=ACTION_COEFF)
        self.composite_reward = CompositeReward(
            [self.force_reward, self.action_reward], coefficient=COMPOSITE_COEFF
        ) 

        # Logging
        self.force_reward_total = 0
        self.action_reward_total = 0
        self.composite_reward_total = 0
        self.max_gripper_close = 0
        self.composite_gripper_actions = [0] * 4


    def step(self, residual_action):
        """
        Execute one environment step by applying a residual scale to the IL gripper command,
        executing the IL joint target, and returning the next residual-policy observation.

        Args:
            residual_action: residual scalar applied to the IL gripper action.

        Returns:
            next_obs (np.ndarray): flattened observation for residual policy.
            reward (float): scalar reward.
            term (bool): episode termination flag.
            trun (bool): episode truncation flag.
            dropped (bool): task-specific drop detection flag.
        """
        if self.step_count == 0:
            # lazily initialize the IL action queue on the first env step
            self.inferred_robot_actions, null_action_detected = self.il_policy.forward(visualize=False, discretize_gripper=self.gripper_type == "franka")

        if "JOINT" in self.controller_type:
            # take the next IL action; residual only scales the gripper command
            self.current_il_action = self.inferred_robot_actions[0]     
            action = self.current_il_action
            action[-1] *= residual_action

            # keep a short history for EMA smoothing to reduce gripper jitter
            self.composite_gripper_actions.append(float(action[-1]))
            if len(self.composite_gripper_actions) > 5:
                self.composite_gripper_actions.pop(0)

            self.joint_pos = action[:7]

            # execute joint target
            self.move_to_joint_positions(action[:7])
            series = pd.Series(self.composite_gripper_actions)
            ema_gripper = series.ewm(alpha=0.3).mean().iloc[-1]
            self.set_gripper_action(ema_gripper)

            time.sleep(0.04)
        
        self.inferred_robot_actions = np.delete(self.inferred_robot_actions, 0, axis=0) 

        if self.inferred_robot_actions.size == 0:  
            # refresh IL action queue
            obs_dict = self.observable.get_obs(get_tactile=self.using_tactile, get_points=False, depth=False)
            self.il_policy.step_obs_cache(obs_dict)
            self.inferred_robot_actions, null_action_detected = self.il_policy.forward(visualize=False, discretize_gripper=self.gripper_type == "franka")

            if null_action_detected:
                # early exit
                print("Null action detected!", null_action_detected)
                return None, 0, True, False
        
        self.next_il_action = self.inferred_robot_actions[0] 

        next_obs = self._get_obs()       
        reward = self._compute_reward(residual_action, self.next_obs_dict)
        term = self._check_term() 
        trun = self._check_trun()   
        dropped = self._check_dropped(self.next_obs_dict)

        self.previous_obs = next_obs
        self.step_count += 1

        return next_obs, reward, term, trun, dropped
    

    def set_gripper_action(self, gripper_action):
        """
        Execute gripper command for the active gripper type.

        Args:
            gripper_action (float): target gripper command (discrete for Franka,
                continuous in [0, 1] for SSG48).
        """
        if self.gripper_type == "franka":
            # skip redundant commands
            if gripper_action == 0 or gripper_action == self.get_last_gripper_action():
                return
            
            # Franka uses discrete open / close commands
            if gripper_action == 1.0:
                self.close_gripper(gripper_action)
            elif gripper_action == -1.0:
                self.open_gripper()
            else:
                raise ValueError(f"Invalid gripper action {gripper_action}")

        elif self.gripper_type == "ssg48":
            # SSG48 expects continuous position in [0, 1]
            gripper_action = np.clip(gripper_action, 0.0, 1.0)
            self.gripper.move_gripper(position=gripper_action, speed=self.gripper_default_speed, current=CURRENT)
            self.last_gripper_action = gripper_action


    def reset(self):
        """
        Reset environment state and internal buffers in preparation for a new episode.

        Returns:
            obs (np.ndarray): initial observation.
        """
        input("About to reset robot, press enter to continue")
       
        # reset robot + parent env state
        super().reset() 

        # clear per-episode state
        self.current_il_action = np.zeros(FRANKA_ACT_LEN)
        self.previous_obs = self._get_obs()
        self.basket_reached = False
        self.in_transit = False 
        self.step_count = 0

        # clear observable + reward bookkeeping
        self.observable.obs_buffer = []
        self.observable.obs_dict = {}
        self.force_reward_total = 0
        self.action_reward_total = 0
        self.composite_reward_total = 0
        self.max_gripper_close = 0
        self.composite_gripper_actions = [0] * 4

        return self.previous_obs


    def clear_cache(self):
        """
        Clear cached imitation-policy observations between RL rollouts.
        """
        # reset IL cache to improve performance over RL iterations
        self.il_policy.cache_observations = [] 


    def _get_obs(self):       
        """
        Collect current environment observation and format it for the residual policy.

        Returns:
            obs (np.ndarray): flattened observation vector concatenated with next IL action.
        """

        obs_dict = self.observable.get_obs(get_tactile=self.using_tactile, get_points=False, depth=False)
        # save full dict for reward / termination checks
        self.next_obs_dict = copy.deepcopy(obs_dict)
        # update IL cache for next action inference
        self.il_policy.step_obs_cache(obs_dict.copy())

        # remove entries not used by residual policy
        del obs_dict['imgs']    
        del obs_dict['time']
        del obs_dict['baseline']
        del obs_dict['std']

        if self.max_gripper_close < obs_dict['gripper_width']:
            self.max_gripper_close = obs_dict['gripper_width']

        return np.concatenate([np.ravel(value) for value in obs_dict.values()] + [self.next_il_action])


    def _compute_reward(self, residual_action, observation_dict):
        """
        Compute composite reward for the current step.

        Args:
            residual_action: residual gripper action.
            observation_dict (dict): full observation dictionary.

        Returns:
            reward (float): scalar composite reward.
        """
        # update basket-reached flag before computing reward
        self.basket_reached = self._basket_reached(self.joint_pos)
        
        composite_reward = self.composite_reward.get_reward(
            residual_action, observation_dict, self.basket_reached
        )

        # accumulate episode totals for logging
        self.composite_reward_total += composite_reward
        self.action_reward_total += self.composite_reward.action_reward
        self.force_reward_total += self.composite_reward.force_reward
       
        return composite_reward
        
    
    def _basket_reached(self, joint_pos):
        """
        Check whether the basket joint target has been reached.

        Args:
            joint_pos (np.ndarray): current joint positions.

        Returns:
            reached (bool): True if within tolerance of basket pose.
        """
        return (np.all(np.abs(joint_pos - BASKET_REACH_POS) <= TERM_TOLERANCE)) if (not self.basket_reached) else True
            

    def _check_dropped(self, next_observation):
        """
        Detect object drop using end-effector height and tactile feedback.

        Args:
            next_observation (dict): full observation dictionary.

        Returns:
            dropped (bool): True if an object drop is detected.
        """
        tactile = np.array(next_observation['full_tactile'])          
        eef_pos = next_observation['eef_pos']         

        # consider object picked up if lifted and tactile contact is present
        picked_up = (eef_pos[2] >= 0.2) and (np.any(tactile >= 0.08))

        if picked_up:
            self.in_transit = True
        
        dropped = self.in_transit and (not picked_up) and (not self.basket_reached)

        return dropped
        

    def _check_term(self):
        """
        Check task success termination condition.

        Returns:
            term (bool): True if basket reached and end-effector lifted.
        """
        
        joint_pos = self.joint_pos
        eef_pos = (self.next_obs_dict['eef_pos'])

        # update basket-reached flag
        if self._basket_reached(joint_pos):
            self.basket_reached = True
        
        # success when basket reached and end-effector lifted
        if(self.basket_reached and eef_pos[2] >= TERM_HEIGHT):       
            return True
        return False


    def _check_trun(self):
        """
        Check episode truncation due to timeout.

        Returns:
            trun (bool): True if max step count is reached.
        """
        return self.step_count >= self.max_timeout