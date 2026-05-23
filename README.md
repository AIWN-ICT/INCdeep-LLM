# INCdeep-LLM

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://github.com/AIWN-ICT/INCdeep-LLM/blob/main/LICENSE)
![Status](https://img.shields.io/badge/Status-Research%20Prototype-orange)

INCdeep-LLM is a two-stage workflow for adaptive network coding:

1. **LLM reward generation + cross-model evaluation**
2. **RL training with the selected reward function** (two DQN agents for source/relay decisions)

Primary KPI: **`avg_s_f`** (lower is better).

---

## TL;DR

```bash
pip install -r requirements.txt
python main.py train
python main.py test --model-dir ./models/examples/best_by_avg_source_send
```

If you only want the RL baseline, you can skip the LLM pipeline.

For LLM reward generation/evaluation, configure `.env` first (see [Environment setup](#environment-setup)).

---

## Table of Contents

- [Environment setup](#environment-setup)
- [Quick start](#quick-start)
- [End-to-end workflow (recommended)](#end-to-end-workflow-recommended)
- [LLM reward pipeline](#llm-reward-pipeline)
- [RL training and evaluation](#rl-training-and-evaluation)
- [Key configuration](#key-configuration)
- [Repository structure](#repository-structure)
- [Checkpoints and repository policy](#checkpoints-and-repository-policy)
- [Minimal success checklist](#minimal-success-checklist)
- [FAQ](#faq)
- [Citation](#citation)
- [Reproducibility notes](#reproducibility-notes)

---

## Environment setup

Before running any LLM reward pipeline command:

1. Copy `.env.example` to `.env`
2. Fill in:
   - `API_KEY`
   - `BASE_URL`

Windows (PowerShell):

```powershell
Copy-Item .env.example .env
```

Linux/macOS (bash):

```bash
cp .env.example .env
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Quick start

Train:

```bash
python main.py train
```

Override evaluation interval temporarily (without editing `config.py`):

```bash
python main.py train --eval-interval 5
```

Test with the example checkpoint:

```bash
python main.py test --model-dir ./models/examples/best_by_avg_source_send
```

If you run `test.py` directly, you can pass explicit paths:

```bash
python test.py --model-dir models/best_by_avg_source_send --best-state models/best_by_avg_source_send/best_epoch.pkl
```

If these arguments are omitted, `test.py` falls back to default paths.

> If `torch.compile` is unstable in your environment, add `--skip-compile`.

---

## End-to-end workflow (recommended)

Recommended full path: **LLM reward evaluation → reward integration → RL training**.

1. Run LLM-based reward evaluation:

```bash
python reward_pipeline_cli.py --mode both
```

2. Select a reward candidate from:
   - `result/LLM_reward/auto_eval_reward_function_ranking.csv` (overall ranking)
   - `result/LLM_reward/auto_eval_scores_by_reward_function.csv` (per-evaluator consistency)

3. Integrate the selected reward logic into `simulator.py` (`forward_data(...)`, optionally `calculate_reward(...)`).
4. Train RL agents:

```bash
python main.py train
```

5. Evaluate KPI (`avg_s_f`, lower is better):
   - `result/evaluation_avg_source_sends.txt`

---

## LLM reward pipeline

### Related files

- CLI entry: `reward_pipeline_cli.py`
- Two-stage orchestration: `reward_pipeline_runner.py`
- Stage 1 generation: `reward_generation_runner.py`
- Stage 2 evaluation/reporting: `reward_eval_runner.py`
- Config and model routing: `reward_config.py`
- Prompt templates: `reward_prompt_templates.py`
- Built-in candidate assets: `reward_prompt_assets.py`

### Workflow summary

1. **Stage 1: generation**
   - Iterates models from `EVALUATION_MODELS` in `reward_config.py`.
   - Selects Chinese/English prompts via `MODEL_LANGUAGE_OVERRIDES`.
   - Calls each model through `ChatOpenAI`, extracts function code, and writes (default: `result/LLM_reward/`):
     - `reward_generation_results.json`
     - `reward_generation_functions.csv`

2. **Stage 2: cross-model evaluation**
   - Uses successful Stage 1 candidates (requires at least 2).
   - Cross-scores each candidate with other evaluator models (no self-evaluation).
   - Uses strict JSON format and five dimensions:
     - `Goal Consistency`
     - `Exploration Effectiveness`
     - `Dynamic Reward Weighting`
     - `Mathematical Consistency`
     - `Robustness`
   - Per-evaluator total = sum of the five integer fields.
   - Final ranking = average total score.

3. **Best-candidate export**
   - Exports the top candidate to `result/LLM_reward/best_reward_function.py`.
   - Writes summary to `result/LLM_reward/two_stage_summary.json`.

### CLI usage

Run full two-stage flow:

```bash
python reward_pipeline_cli.py --mode both
```

Run generation only:

```bash
python reward_pipeline_cli.py --mode stage1
```

Run evaluation only:

```bash
python reward_pipeline_cli.py --mode stage2
```

Optional arguments:

- `--output-dir` (default: `result/LLM_reward`)
- `--generation-output` (default: `<output-dir>/reward_generation_results.json`)
- `--generation-csv-output` (default: `<output-dir>/reward_generation_functions.csv`)
- `--best-output` (default: `<output-dir>/best_reward_function.py`)
- `--summary-output` (default: `<output-dir>/two_stage_summary.json`)

### Environment variables

Same required variables as [Environment setup](#environment-setup): `API_KEY`, `BASE_URL`.

All configured generation/evaluation models share the same API credential and endpoint.

### Stage 2 output files

Default location: `result/LLM_reward/` (or the directory passed via `--output-dir`).

- `auto_eval_reward_function_ranking.csv`
- `auto_eval_scores_by_reward_function.csv`
- `auto_eval_response_times_by_reward_function.csv`
- `auto_eval_average_response_time_by_model.csv`
- `best_reward_function.py`
- `two_stage_summary.json`

---

## RL training and evaluation

### Reward logging

In `evaluate.py`, metrics are defined as follows:

1. For each evaluation episode, rewards from all forwarding/coding actions (source + relays across all time steps) are accumulated into `total_reward`.
2. `source_send_count` is the episode source-send count (the same quantity used for `avg_s_f`).
3. Episode reward is normalized by `source_send_count`:
   - `normalized_reward = total_reward / source_send_count` (with zero protection in code).
4. `evaluation_reward.txt` stores the mean `normalized_reward` over all evaluation episodes.
5. `evaluation_avg_source_sends.txt` stores `avg_s_f` (mean `source_send_count` over all evaluation episodes).

Best checkpoint selection criterion: minimize `avg_s_f`.

Best checkpoint directory:

`models/checkpoints/best_by_avg_source_send/`

- `dqn_agent_s_min.pt`
- `dqn_agent_r_min.pt`
- `best_epoch.pkl`
- `best_metric.txt`

Main result files:

- `result/evaluation_avg_source_sends.txt`
- `data_INCdeep_LLM/decode_probability_overhead_summary.csv`

For the complete expected checkpoint file list, see [Minimal success checklist](#minimal-success-checklist).

---

## Key configuration

Edit `config.py` and `config_topology.py` before experiments.

Most impactful parameters:

- `K` / `generation_size`: symbols per generation
- `M` / `relay_memory_rows`: relay coding-memory depth
- `num_episodes` (EPISODES): training episodes
- `num_eval_episodes` (`Max_test` in evaluation call): number of test/evaluation episodes executed each time evaluation runs
- `eval_interval` (`Eval_interval` in code): run evaluation every N training episodes
- `force_eval_at_end` (`Force_eval_at_end` in code): if tail episodes are fewer than `Eval_interval`, force one final evaluation
- `max_source_sends_per_episode` (`Max_s_f`): per-episode source-send cap
- `epsilon_decay_episodes`: exploration decay length

### Recommended EPISODES / Max_test settings

- **Training (recommended default)**:
  - `EPISODES = 10000`
  - `Max_test = 100` (faster) **or** `1000` (more stable but significantly longer training time)
- **Testing (inference-only run)**:
  - When running pure test/inference, `num_episodes` is not used.
  - Use `Max_test = 1000` for more stable statistics.

Notes:

- In the current code path (`train.py`), evaluation is periodically triggered during training (`run_evaluate(...)`), and model selection is based on test/evaluation results.
- The best checkpoint is selected by minimizing `avg_s_f` (average source-send count), and saved under `models/checkpoints/best_by_avg_source_send/`.

### `config_topology.py` (network graph and link reliability)

Defines forwarding topology and channel assumptions:

- `node_num`
- `parallel_path`
- `max_nb`
- `neighbor_matrix`
- `links`

### `data_processor.py` (post-processing and metric export)

Provides evaluation statistics/CSV helpers:

- source-send standard deviation
- per-episode source-send CSV
- decode probability curve: \(P(\text{source sends} \le t)\), `t = 1..60`
- summary CSV with decode probability, average overhead, std deviation, and `avg_s_f`

---

## Repository structure

```text
INCdeep-LLM/
├─ main.py                    # Unified CLI entry (`train` / `test`)
├─ train.py                   # Training loop
├─ test.py                    # Testing with saved checkpoints
├─ evaluate.py                # Shared evaluation logic
├─ simulator.py               # Forwarding/coding environment dynamics
├─ node.py                    # Node state and behavior
├─ config.py                  # RL and coding hyperparameters
├─ config_topology.py         # Topology and link reliability
├─ data_processor.py          # Metrics/statistics export
├─ utils/
│  ├─ dqn_S.py                # Source-side DQN
│  ├─ dqn_R.py                # Relay-side DQN
│  └─ ReplayBuffer.py         # Replay buffer
├─ models/
│  ├─ checkpoints/            # local training outputs (ignored)
│  └─ examples/               # tracked demo checkpoints
│     └─ best_by_avg_source_send/
└─ result/
```

---

## Checkpoints and repository policy

- `models/examples/` stores demo checkpoints for quick testing/documentation.
- `models/checkpoints/` stores local training outputs and should remain untracked.
- For large `.pt/.pkl` files, use Git LFS when possible.

For the recommended quick test command, see [Quick start](#quick-start).

---

## Minimal success checklist

After a successful training run, you should see:

- `models/checkpoints/best_by_avg_source_send/dqn_agent_s_min.pt`
- `models/checkpoints/best_by_avg_source_send/dqn_agent_r_min.pt`
- `models/checkpoints/best_by_avg_source_send/best_epoch.pkl`
- `models/checkpoints/best_by_avg_source_send/best_metric.txt`
- `result/evaluation_avg_source_sends.txt`

---

## FAQ

### Q1: `test` cannot find model files

**Symptoms**
- Missing checkpoint errors when running `python main.py test ...`

**Checklist**
- Confirm training has completed at least once.
- Verify required files exist (see [Minimal success checklist](#minimal-success-checklist)).

**Recommended action**
- Re-run training, then test again with a valid `--model-dir`.

### Q2: When should I use `--skip-compile`?

**Symptoms**
- `torch.compile` crashes, hangs, or shows backend compatibility errors.

**Recommended action**
- Add `--skip-compile` for stable execution on your platform.

### Q3: Can I reuse old models after changing config?

**Short answer**
- Usually no.

**Why**
- Changes to state/action dimensions (e.g., `K`, `R`, `parallel_path`, `max_nb`, `action_size`) typically invalidate old checkpoints.

**Recommended action**
- Retrain and generate new checkpoints for the new configuration.

---

## Citation

If you find this project useful, please cite:

```bibtex
@article{WANG2026112390,
  title   = {INCdeep-LLM: Deep reinforcement learning for network coding with large language model-generated reward functions},
  author  = {Wang, Q. and Li, J. and Xu, Y.},
  journal = {Computer Networks},
  volume  = {285},
  pages   = {112390},
  year    = {2026},
  issn    = {1389-1286},
  doi     = {https://doi.org/10.1016/j.comnet.2026.112390},
  url     = {https://www.sciencedirect.com/science/article/pii/S1389128626004020}
}
```

---

## Reproducibility notes

- Default random seed in code: `555`
- For reproducible comparisons, record:
  - Python / PyTorch / CUDA versions
  - full config values
  - episode/evaluation counts
  - checkpoint directory used for testing
