# INCdeep-LLM

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://github.com/AIWN-ICT/INCdeep-LLM/blob/main/LICENSE)
![Status](https://img.shields.io/badge/Status-Research%20Prototype-orange)

INCdeep-LLM is a two-stage workflow for adaptive network coding:

1. **LLM reward generation + cross-model evaluation**
2. **RL training with the selected reward function**

Primary KPI: **`avg_s_f`** (lower is better).

---

## TL;DR

```bash
pip install -r requirements.txt
python main.py train
python main.py test --model-dir ./models/examples/best_by_avg_source_send
```

LLM pipeline users must configure `.env` first.

---

## Table of Contents

- [Environment setup](#environment-setup)
- [Quick start](#quick-start)
- [Recommended end-to-end workflow](#recommended-end-to-end-workflow)
- [LLM reward pipeline](#llm-reward-pipeline)
- [RL training and evaluation](#rl-training-and-evaluation)
- [Key configuration](#key-configuration)
- [Repository structure](#repository-structure)
- [Checkpoints policy](#checkpoints-policy)
- [Minimal success checklist](#minimal-success-checklist)
- [FAQ](#faq)
- [Citation](#citation)
- [Reproducibility notes](#reproducibility-notes)

---

## Environment setup

1. Copy `.env.example` to `.env`.
2. Fill in:
   - `API_KEY`
   - `BASE_URL`
3. Install dependencies:

```bash
pip install -r requirements.txt
```

Windows (PowerShell):

```powershell
Copy-Item .env.example .env
```

Linux/macOS:

```bash
cp .env.example .env
```

---

## Quick start

Train:

```bash
python main.py train
```

Train with temporary evaluation interval override:

```bash
python main.py train --eval-interval 5
```

Test with example checkpoint:

```bash
python main.py test --model-dir ./models/examples/best_by_avg_source_send
```

Direct `test.py` usage:

```bash
python test.py --model-dir models/best_by_avg_source_send --best-state models/best_by_avg_source_send/best_epoch.pkl
```

If `torch.compile` is unstable, add `--skip-compile`.

---

## Recommended end-to-end workflow

1. Run two-stage reward pipeline:

```bash
python reward_pipeline_cli.py --mode both
```

2. Inspect ranking and consistency:
   - `result/LLM_reward/auto_eval_reward_function_ranking.csv`
   - `result/LLM_reward/auto_eval_scores_by_reward_function.csv`
3. Integrate selected reward into `simulator.py` (`forward_data(...)`, optional `calculate_reward(...)`).
4. Train RL:

```bash
python main.py train
```

5. Check KPI in `result/evaluation_avg_source_sends.txt`.

---

## LLM reward pipeline

### Core files

- `reward_pipeline_cli.py` (CLI)
- `reward_pipeline_runner.py` (orchestration)
- `reward_generation_runner.py` (stage 1 generation)
- `reward_eval_runner.py` (stage 2 evaluation/reporting)
- `reward_config.py` (models/config)
- `reward_prompt_templates.py` / `reward_prompt_assets.py`

### Pipeline summary

- **Stage 1 (generation):** Generate reward candidates and save:
  - `reward_generation_results.json`
  - `reward_generation_functions.csv`
- **Stage 2 (cross-model evaluation):** Each candidate is scored by other models (no self-eval) across five dimensions:
  - Goal Consistency
  - Exploration Effectiveness
  - Dynamic Reward Weighting
  - Mathematical Consistency
  - Robustness
- Final score = per-evaluator total (sum of 5 fields), then average across evaluators.
- Best candidate is exported to `best_reward_function.py`.

### CLI

```bash
python reward_pipeline_cli.py --mode both
python reward_pipeline_cli.py --mode stage1
python reward_pipeline_cli.py --mode stage2
```

Optional args:

- `--output-dir` (default `result/LLM_reward`)
- `--generation-output`
- `--generation-csv-output`
- `--best-output`
- `--summary-output`

### Stage 2 outputs

- `auto_eval_reward_function_ranking.csv`
- `auto_eval_scores_by_reward_function.csv`
- `auto_eval_response_times_by_reward_function.csv`
- `auto_eval_average_response_time_by_model.csv`
- `best_reward_function.py`
- `two_stage_summary.json`

---

## RL training and evaluation

- Best checkpoint criterion: **minimize `avg_s_f`**.
- Best checkpoint path:
  - `models/checkpoints/best_by_avg_source_send/`

Main result files:

- `result/evaluation_avg_source_sends.txt`
- `data_INCdeep_LLM/decode_probability_overhead_summary.csv`

Reward logging (`evaluate.py`) in short:

- Episode `total_reward` = sum of forwarding/coding rewards.
- Episode normalized reward = `total_reward / source_send_count` (with zero protection).
- `evaluation_reward.txt` stores mean normalized reward.
- `evaluation_avg_source_sends.txt` stores `avg_s_f`.

---

## Key configuration

Edit `config.py` and `config_topology.py` before experiments.

Most impactful parameters:

- `K`, `generation_size`
- `M`, `relay_memory_rows`
- `num_episodes` (`EPISODES`)
- `num_eval_episodes` (`Max_test`)
- `eval_interval` (`Eval_interval`)
- `force_eval_at_end` (`Force_eval_at_end`)
- `max_source_sends_per_episode` (`Max_s_f`)
- `epsilon_decay_episodes`

Recommended settings:

- Training: `EPISODES = 10000`, `Max_test = 100` (faster) or `1000` (more stable)
- Inference-only test: `Max_test = 1000`

---

## Repository structure

```text
INCdeep-LLM/
├─ main.py                        # unified train/test entry
├─ train.py                       # RL training loop
├─ test.py                        # standalone inference/evaluation entry
├─ evaluate.py                    # KPI computation and report writing
├─ simulator.py                   # environment dynamics + reward logic
├─ node.py                        # source/relay node behavior
├─ config.py                      # core experiment hyperparameters
├─ config_topology.py             # network topology settings
├─ data_processor.py              # data cleaning/file-name helpers
├─ reward_pipeline_cli.py         # stage1/stage2 pipeline CLI
├─ reward_pipeline_runner.py      # two-stage orchestration
├─ reward_generation_runner.py    # reward candidate generation
├─ reward_eval_runner.py          # cross-model scoring + CSV export
├─ reward_config.py               # LLM model list and API config
├─ reward_prompt_templates.py     # evaluation prompt templates
├─ reward_prompt_assets.py        # built-in reward function assets
├─ utils/
│  ├─ dqn_S.py                    # DQN for source agent
│  ├─ dqn_R.py                    # DQN for relay agent
│  └─ ReplayBuffer.py             # replay buffer implementation
├─ models/
│  ├─ checkpoints/                # local training outputs (untracked)
│  └─ examples/                   # tracked demo checkpoints
└─ result/                        # evaluation and pipeline artifacts
```

---

## Checkpoints policy

- `models/examples/`: tracked demo checkpoints for quick verification.
- `models/checkpoints/`: local training outputs, should remain untracked.
- Prefer Git LFS for large `.pt/.pkl` files.

---

## Minimal success checklist

After a successful training run:

- `models/checkpoints/best_by_avg_source_send/dqn_agent_s_min.pt`
- `models/checkpoints/best_by_avg_source_send/dqn_agent_r_min.pt`
- `models/checkpoints/best_by_avg_source_send/best_epoch.pkl`
- `models/checkpoints/best_by_avg_source_send/best_metric.txt`
- `result/evaluation_avg_source_sends.txt`

---

## FAQ

### Q1: `test` cannot find model files

- Run training at least once.
- Verify files in [Minimal success checklist](#minimal-success-checklist).
- Use a valid `--model-dir`.

### Q2: When should I use `--skip-compile`?

Use it if `torch.compile` crashes/hangs or has backend compatibility issues.

### Q3: Can I reuse old checkpoints after changing config?

Usually no. Changes in state/action dimensions typically invalidate old checkpoints. Retrain.

### Q4: Why is generated reward function not identical to the paper?

Expected. LLM outputs are probabilistic. Compare objective-level performance (especially `avg_s_f`) under fixed evaluation settings rather than string-level identity.

---

## Citation

Official open-source implementation of:

Wang, Q., Li, J., Xu, Y., *INCdeep-LLM: Deep reinforcement learning for network coding with large language model-generated reward functions*, **Computer Networks**, 285:112390, 2026.

```bibtex
@article{wang2026incdeep,
  title={INCdeep-LLM: Deep reinforcement learning for network coding with large language model-generated reward functions},
  author={Wang, Qi and Li, Jinmou and Xu, Yongjun},
  journal={Computer Networks},
  pages={112390},
  year={2026},
  publisher={Elsevier}
}
```

---

## Reproducibility notes

- Default random seed: `555`
- Record for comparisons:
  - Python / PyTorch / CUDA versions
  - full config values
  - training/evaluation episode counts
  - checkpoint directory used in testing
- LLM generation variance is expected; evaluate consistency by downstream metrics, not exact text match.
