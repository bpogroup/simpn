"""
deep_solvers.py — Deep RL solvers for the BPMN+OPT SMDP.

Replaces tabular state hashing with neural network function approximation.
The network learns from a fixed-size feature vector extracted from the env,
enabling generalization across similar (but not identical) states.

Solvers:
  1. DQN  — Deep Q-Network with experience replay + target network
  2. PPO  — Proximal Policy Optimization with action masking

Both handle SMDP timing via gamma^tau discounting.
"""

import sys, os, math, random, copy
from collections import deque, defaultdict
import numpy as np

_CODE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _CODE_DIR)
sys.path.insert(0, os.path.join(os.path.dirname(_CODE_DIR), ".."))

import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim

from smdp_env import SMDPEnv


# ===========================================================================
# Feature extraction: env state → fixed-size float vector
# ===========================================================================

class FeatureExtractor:
    """
    Extracts a fixed-size feature vector from any BPMN+OPT SMDP environment.
    Features are computed on first call, then the same ordering is reused.
    """
    def __init__(self, spec):
        self.flow_names = sorted(spec["process"]["flows"], key=lambda f: f["name"])
        self.flow_order = [f["name"] for f in self.flow_names]
        self.lane_names = sorted(spec["process"]["lanes"], key=lambda l: l["name"])
        self.lane_order = [l["name"] for l in self.lane_names]

        self.task_names = sorted([t["name"] for t in spec["process"]["tasks"]])
        self.horizon = spec["smdp"]["horizon"]

        self._build_action_vocab(spec)

        self.n_flow = len(self.flow_order)
        self.n_lane = len(self.lane_order)
        self.n_task = len(self.task_names)
        self.state_dim = self.n_flow + self.n_lane + self.n_task + 2

    def _build_action_vocab(self, spec):
        """Build a fixed vocabulary of abstract action types.
        Handles both simple (Fig2: decision.variables) and complex (Fig1: decision.types) formats."""
        self.action_vocab = []
        self.action_to_idx = {}
        idx = 0

        decision = spec.get("decision", {})
        decision_types = decision.get("types", [])

        if not decision_types and "variables" in decision:
            decision_types = [{"type": decision["variables"].get("type", "assignment"),
                               "variables": decision["variables"]}]
            if decision_types[0]["type"] == "assignment":
                res_lane = decision["variables"].get("resource_lane", "")
                tasks = [t["name"] for t in spec["process"]["tasks"]
                         if t.get("resource_lane") == res_lane and t.get("controlled", True)]
                decision_types[0]["tasks"] = tasks

        for dt in decision_types:
            if dt["type"] == "scheduling":
                for offset in dt["variables"]["domain"]:
                    a = ("schedule", offset)
                    self.action_vocab.append(a)
                    self.action_to_idx[a] = idx
                    idx += 1

            elif dt["type"] == "routing":
                for val in dt["variables"]["domain"]:
                    a = ("route", val)
                    self.action_vocab.append(a)
                    self.action_to_idx[a] = idx
                    idx += 1

            elif dt["type"] == "assignment":
                tasks = dt.get("tasks", [])
                if not tasks:
                    tasks = [t["name"] for t in spec["process"]["tasks"]
                             if t.get("controlled", False)]
                res_lanes = set()
                for t in spec["process"]["tasks"]:
                    if t["name"] in tasks:
                        res_lanes.add(t["resource_lane"])
                for task_name in sorted(tasks):
                    for lane_cfg in spec["process"]["initial_resources"]:
                        if lane_cfg["lane"] not in res_lanes:
                            continue
                        for inst in lane_cfg["instances"]:
                            a = ("assign", task_name, inst["id"])
                            self.action_vocab.append(a)
                            self.action_to_idx[a] = idx
                            idx += 1

        self.n_actions = len(self.action_vocab)

    def state_features(self, env):
        """Extract a fixed-size feature vector from the current env state."""
        feats = np.zeros(self.state_dim, dtype=np.float32)
        clock = env.model.problem.clock

        for i, fname in enumerate(self.flow_order):
            if fname in env.model.flows:
                avail = [t for t in env.model.flows[fname].marking
                         if t.time <= clock + 1e-9]
                feats[i] = len(avail)

        base = self.n_flow
        for i, lname in enumerate(self.lane_order):
            if lname in env.model.lanes:
                avail = [t for t in env.model.lanes[lname].marking
                         if t.time <= clock + 1e-9]
                feats[base + i] = len(avail)

        base += self.n_lane
        for i, tname in enumerate(self.task_names):
            bvar = tname + "_busy"
            if bvar in env.model.problem.id2node:
                feats[base + i] = len(env.model.problem.id2node[bvar].marking)

        base += self.n_task
        feats[base] = clock / max(self.horizon, 1.0)
        feats[base + 1] = sum(feats[:self.n_flow])

        return feats

    def action_to_index(self, action, env):
        """Map a concrete action to its vocabulary index."""
        atype = action[0]
        if atype == "schedule":
            key = ("schedule", action[2])
        elif atype == "route":
            key = ("route", action[2])
        elif atype == "assign":
            key = ("assign", action[1], action[3])
        else:
            return None
        return self.action_to_idx.get(key)

    def available_mask(self, actions, env):
        """Binary mask over the action vocabulary for currently available actions."""
        mask = np.zeros(self.n_actions, dtype=np.float32)
        for a in actions:
            idx = self.action_to_index(a, env)
            if idx is not None:
                mask[idx] = 1.0
        return mask

    def index_to_concrete(self, idx, actions, env):
        """Map a vocabulary index back to the best concrete action."""
        if idx >= len(self.action_vocab):
            return random.choice(actions) if actions else None
        abs_a = self.action_vocab[idx]
        atype = abs_a[0]

        if atype == "schedule":
            offset = abs_a[1]
            candidates = [a for a in actions if a[0] == "schedule" and a[2] == offset]
            return candidates[0] if candidates else (actions[0] if actions else None)

        elif atype == "route":
            route_val = abs_a[1]
            candidates = [a for a in actions if a[0] == "route" and a[2] == route_val]
            return candidates[0] if candidates else (actions[0] if actions else None)

        elif atype == "assign":
            _, task_name, r_id = abs_a
            candidates = [a for a in actions
                          if a[0] == "assign" and a[1] == task_name and a[3] == r_id]
            if candidates:
                best = candidates[0]
                best_wait = -1
                for c in candidates:
                    start = env._lookup_start_time(c[2])
                    wait = env.model.problem.clock - start
                    if wait > best_wait:
                        best_wait = wait
                        best = c
                return best
            return actions[0] if actions else None

        return random.choice(actions) if actions else None


# ===========================================================================
# DQN — Deep Q-Network
# ===========================================================================

class QNetwork(nn.Module):
    def __init__(self, state_dim, n_actions, hidden=128):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(state_dim, hidden),
            nn.ReLU(),
            nn.Linear(hidden, hidden),
            nn.ReLU(),
            nn.Linear(hidden, n_actions),
        )

    def forward(self, x):
        return self.net(x)


class DQNSolver:
    """
    Deep Q-Network for SMDP with experience replay and target network.
    SMDP discount: gamma^tau instead of gamma.
    """
    def __init__(self, spec, gamma=1.0, lr=1e-3, hidden=128,
                 buffer_size=50000, batch_size=64, target_update=100,
                 epsilon_start=1.0, epsilon_end=0.05, epsilon_decay=0.995):
        self.spec = spec
        self.gamma = gamma
        self.feat = FeatureExtractor(spec)
        self.device = torch.device("cpu")

        self.q_net = QNetwork(self.feat.state_dim, self.feat.n_actions, hidden).to(self.device)
        self.target_net = QNetwork(self.feat.state_dim, self.feat.n_actions, hidden).to(self.device)
        self.target_net.load_state_dict(self.q_net.state_dict())
        self.optimizer = optim.Adam(self.q_net.parameters(), lr=lr)

        self.buffer = deque(maxlen=buffer_size)
        self.batch_size = batch_size
        self.target_update = target_update
        self.epsilon = epsilon_start
        self.epsilon_end = epsilon_end
        self.epsilon_decay = epsilon_decay
        self.steps = 0

    def _select_action(self, state_feat, mask, actions, env):
        if random.random() < self.epsilon:
            valid = [i for i in range(self.feat.n_actions) if mask[i] > 0]
            return random.choice(valid) if valid else 0
        with torch.no_grad():
            q = self.q_net(torch.tensor(state_feat, device=self.device).unsqueeze(0))[0]
            q = q.cpu().numpy()
            q[mask == 0] = -1e9
            return int(np.argmax(q))

    def train(self, n_episodes=500, verbose=True):
        losses = []
        rewards_history = []

        for ep in range(n_episodes):
            env = SMDPEnv(spec_dict=self.spec)
            env.reset(seed=ep)
            state_feat = self.feat.state_features(env)
            prev_time = env.model.problem.clock
            ep_reward = 0.0

            while not env.done:
                actions = env.get_actions()
                if not actions:
                    break
                mask = self.feat.available_mask(actions, env)
                if mask.sum() == 0:
                    break

                action_idx = self._select_action(state_feat, mask, actions, env)
                concrete = self.feat.index_to_concrete(action_idx, actions, env)
                if concrete is None:
                    break

                _, reward, done, info = env.step(concrete)
                current_time = env.model.problem.clock
                tau = current_time - prev_time

                next_feat = self.feat.state_features(env)
                next_actions = env.get_actions() if not env.done else []
                next_mask = self.feat.available_mask(next_actions, env) if next_actions else np.zeros(self.feat.n_actions, dtype=np.float32)

                self.buffer.append((state_feat, action_idx, reward, next_feat,
                                    next_mask, tau, env.done or not next_actions))

                if len(self.buffer) >= self.batch_size:
                    loss = self._update()
                    losses.append(loss)

                self.steps += 1
                if self.steps % self.target_update == 0:
                    self.target_net.load_state_dict(self.q_net.state_dict())

                if not info.get("same_time", False):
                    prev_time = current_time

                state_feat = next_feat
                ep_reward += reward

            rewards_history.append(ep_reward)
            self.epsilon = max(self.epsilon_end, self.epsilon * self.epsilon_decay)

            if verbose and (ep + 1) % 50 == 0:
                avg_r = sum(rewards_history[-50:]) / min(50, len(rewards_history))
                avg_l = sum(losses[-100:]) / max(1, min(100, len(losses)))
                print(f"  DQN ep {ep+1}/{n_episodes} | avg_r={avg_r:.1f} | "
                      f"loss={avg_l:.4f} | eps={self.epsilon:.3f} | "
                      f"buf={len(self.buffer)}")

        return rewards_history

    def _update(self):
        batch = random.sample(list(self.buffer), self.batch_size)
        states, actions, rewards, next_states, next_masks, taus, dones = zip(*batch)

        states_t = torch.tensor(np.array(states), device=self.device)
        actions_t = torch.tensor(actions, dtype=torch.long, device=self.device)
        rewards_t = torch.tensor(rewards, dtype=torch.float32, device=self.device)
        next_states_t = torch.tensor(np.array(next_states), device=self.device)
        next_masks_t = torch.tensor(np.array(next_masks), device=self.device)
        taus_t = torch.tensor(taus, dtype=torch.float32, device=self.device)
        dones_t = torch.tensor(dones, dtype=torch.float32, device=self.device)

        q_values = self.q_net(states_t).gather(1, actions_t.unsqueeze(1)).squeeze(1)

        with torch.no_grad():
            next_q = self.target_net(next_states_t)
            next_q[next_masks_t == 0] = -1e9
            max_next_q = next_q.max(dim=1)[0]
            max_next_q[dones_t == 1] = 0.0
            discounts = self.gamma ** taus_t
            targets = rewards_t + discounts * max_next_q

        loss = F.mse_loss(q_values, targets)
        self.optimizer.zero_grad()
        loss.backward()
        nn.utils.clip_grad_norm_(self.q_net.parameters(), 10.0)
        self.optimizer.step()
        return loss.item()

    def policy(self):
        feat = self.feat
        q_net = self.q_net

        def policy_fn(state, actions, env):
            sf = feat.state_features(env)
            mask = feat.available_mask(actions, env)
            with torch.no_grad():
                q = q_net(torch.tensor(sf).unsqueeze(0))[0].numpy()
            q[mask == 0] = -1e9
            best_idx = int(np.argmax(q))
            return feat.index_to_concrete(best_idx, actions, env)

        return policy_fn


# ===========================================================================
# PPO — Proximal Policy Optimization
# ===========================================================================

class ActorCritic(nn.Module):
    def __init__(self, state_dim, n_actions, hidden=128):
        super().__init__()
        self.shared = nn.Sequential(
            nn.Linear(state_dim, hidden),
            nn.ReLU(),
        )
        self.actor = nn.Sequential(
            nn.Linear(hidden, hidden),
            nn.ReLU(),
            nn.Linear(hidden, n_actions),
        )
        self.critic = nn.Sequential(
            nn.Linear(hidden, hidden),
            nn.ReLU(),
            nn.Linear(hidden, 1),
        )

    def forward(self, x, mask=None):
        h = self.shared(x)
        logits = self.actor(h)
        if mask is not None:
            logits = logits + (1 - mask) * (-1e9)
        value = self.critic(h).squeeze(-1)
        return logits, value


class PPOSolver:
    """
    PPO with action masking for SMDP.
    Collects rollouts, computes GAE with SMDP discount, updates via clipped objective.
    """
    def __init__(self, spec, gamma=1.0, lr=3e-4, hidden=128,
                 clip_eps=0.2, epochs_per_update=4, minibatch_size=64,
                 gae_lambda=0.95, entropy_coef=0.01, vf_coef=0.5):
        self.spec = spec
        self.gamma = gamma
        self.feat = FeatureExtractor(spec)
        self.device = torch.device("cpu")

        self.ac = ActorCritic(self.feat.state_dim, self.feat.n_actions, hidden).to(self.device)
        self.optimizer = optim.Adam(self.ac.parameters(), lr=lr)

        self.clip_eps = clip_eps
        self.epochs_per_update = epochs_per_update
        self.minibatch_size = minibatch_size
        self.gae_lambda = gae_lambda
        self.entropy_coef = entropy_coef
        self.vf_coef = vf_coef

    def train(self, n_episodes=500, update_every=10, verbose=True):
        rewards_history = []
        rollout = []

        for ep in range(n_episodes):
            env = SMDPEnv(spec_dict=self.spec)
            env.reset(seed=ep)
            prev_time = env.model.problem.clock
            ep_reward = 0.0

            while not env.done:
                actions = env.get_actions()
                if not actions:
                    break

                sf = self.feat.state_features(env)
                mask = self.feat.available_mask(actions, env)
                if mask.sum() == 0:
                    break

                sf_t = torch.tensor(sf, device=self.device).unsqueeze(0)
                mask_t = torch.tensor(mask, device=self.device).unsqueeze(0)

                with torch.no_grad():
                    logits, value = self.ac(sf_t, mask_t)
                    dist = torch.distributions.Categorical(logits=logits[0])
                    action_idx = dist.sample().item()
                    log_prob = dist.log_prob(torch.tensor(action_idx)).item()
                    val = value.item()

                concrete = self.feat.index_to_concrete(action_idx, actions, env)
                if concrete is None:
                    break

                _, reward, done, info = env.step(concrete)
                current_time = env.model.problem.clock
                tau = current_time - prev_time

                rollout.append({
                    "state": sf, "mask": mask, "action": action_idx,
                    "log_prob": log_prob, "value": val,
                    "reward": reward, "tau": tau,
                    "done": env.done or not env.get_actions(),
                })

                if not info.get("same_time", False):
                    prev_time = current_time

                ep_reward += reward

            rewards_history.append(ep_reward)

            if (ep + 1) % update_every == 0 and len(rollout) > self.minibatch_size:
                self._ppo_update(rollout)
                rollout = []

            if verbose and (ep + 1) % 50 == 0:
                avg_r = sum(rewards_history[-50:]) / min(50, len(rewards_history))
                print(f"  PPO ep {ep+1}/{n_episodes} | avg_r={avg_r:.1f}")

        return rewards_history

    def _ppo_update(self, rollout):
        advantages, returns = self._compute_gae(rollout)

        states = torch.tensor(np.array([t["state"] for t in rollout]), device=self.device)
        masks = torch.tensor(np.array([t["mask"] for t in rollout]), device=self.device)
        actions = torch.tensor([t["action"] for t in rollout], dtype=torch.long, device=self.device)
        old_log_probs = torch.tensor([t["log_prob"] for t in rollout], device=self.device)
        advantages_t = torch.tensor(advantages, dtype=torch.float32, device=self.device)
        returns_t = torch.tensor(returns, dtype=torch.float32, device=self.device)

        advantages_t = (advantages_t - advantages_t.mean()) / (advantages_t.std() + 1e-8)

        n = len(rollout)
        for _ in range(self.epochs_per_update):
            indices = list(range(n))
            random.shuffle(indices)

            for start in range(0, n, self.minibatch_size):
                end = min(start + self.minibatch_size, n)
                mb_idx = indices[start:end]

                mb_states = states[mb_idx]
                mb_masks = masks[mb_idx]
                mb_actions = actions[mb_idx]
                mb_old_lp = old_log_probs[mb_idx]
                mb_adv = advantages_t[mb_idx]
                mb_ret = returns_t[mb_idx]

                logits, values = self.ac(mb_states, mb_masks)
                dist = torch.distributions.Categorical(logits=logits)
                new_lp = dist.log_prob(mb_actions)
                entropy = dist.entropy().mean()

                ratio = torch.exp(new_lp - mb_old_lp)
                clip_ratio = torch.clamp(ratio, 1 - self.clip_eps, 1 + self.clip_eps)
                policy_loss = -torch.min(ratio * mb_adv, clip_ratio * mb_adv).mean()
                value_loss = F.mse_loss(values, mb_ret)

                loss = policy_loss + self.vf_coef * value_loss - self.entropy_coef * entropy

                self.optimizer.zero_grad()
                loss.backward()
                nn.utils.clip_grad_norm_(self.ac.parameters(), 0.5)
                self.optimizer.step()

    def _compute_gae(self, rollout):
        n = len(rollout)
        advantages = np.zeros(n, dtype=np.float32)
        returns = np.zeros(n, dtype=np.float32)
        last_gae = 0.0
        last_val = 0.0

        for t in reversed(range(n)):
            r = rollout[t]
            disc = self.gamma ** r["tau"] if r["tau"] > 0 else 1.0
            if r["done"]:
                next_val = 0.0
                last_gae = 0.0
            else:
                next_val = rollout[t + 1]["value"] if t + 1 < n else 0.0

            delta = r["reward"] + disc * next_val - r["value"]
            last_gae = delta + disc * self.gae_lambda * last_gae
            advantages[t] = last_gae
            returns[t] = advantages[t] + r["value"]

        return advantages, returns

    def policy(self):
        feat = self.feat
        ac = self.ac

        def policy_fn(state, actions, env):
            sf = feat.state_features(env)
            mask = feat.available_mask(actions, env)
            sf_t = torch.tensor(sf).unsqueeze(0)
            mask_t = torch.tensor(mask).unsqueeze(0)
            with torch.no_grad():
                logits, _ = ac(sf_t, mask_t)
                probs = F.softmax(logits[0], dim=0).numpy()
            probs[mask == 0] = 0.0
            total = probs.sum()
            if total <= 0:
                return random.choice(actions)
            best_idx = int(np.argmax(probs))
            return feat.index_to_concrete(best_idx, actions, env)

        return policy_fn
