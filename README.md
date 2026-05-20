# INCdeep-LLM

A two-stage workflow for adaptive network coding:

1. **LLM generation + cross-model evaluation of reward functions**
2. **RL training with the selected reward function** (two DQN agents for source/relay decisions)

Primary downstream KPI: **`avg_s_f`** (lower is better).

---

## Quick Start

Install dependencies:

```bash
pip install -r requirements.txt
```

Train:

```bash
python main.py train
```

Temporarily override the evaluation interval (without modifying `config.py`):

```bash
python main.py train --eval-interval 5
```

Test with example checkpoint:

```bash
python main.py test --model-dir ./models/examples/best_by_avg_source_send
```

If you run `test.py` directly, you can explicitly point to a training output directory:

```bash
python test.py --model-dir models/best_by_avg_source_send --best-state models/best_by_avg_source_send/best_epoch.pkl
```

If these arguments are not provided, `test.py` falls back to its default paths.

> If `torch.compile` is unstable in your environment, add `--skip-compile`.

---

## End-to-end workflow (recommended)

Use this path for the full pipeline (LLM reward evaluation -> RL training):

1. Run LLM-based reward evaluation:

```bash
python reward_pipeline_cli.py --mode both
```

2. Select a reward candidate:
   - `auto_eval_reward_function_ranking.csv` (overall ranking)
   - `auto_eval_scores_by_reward_function.csv` (per-evaluator consistency)

3. Integrate selected reward logic into `simulator.py` (`forward_data(...)`, optionally `calculate_reward(...)`).
4. Train RL agents:

```bash
python main.py train
```

5. Evaluate KPI:
   - `result/evaluation_avg_source_sends.txt`
   - compare with **`avg_s_f`** (lower is better)

---

## LLM reward pipeline

### Related files

- CLI entry: `reward_pipeline_cli.py`
- Two-stage orchestration: `reward_pipeline_runner.py`
- Stage1 generation: `reward_generation_runner.py`
- Stage2 evaluation/reporting: `reward_eval_runner.py`
- Config and model routing: `reward_config.py`
- Prompt templates: `reward_prompt_templates.py`
- Built-in candidate assets: `reward_prompt_assets.py`

### Workflow summary

1. **Stage1 (generation)**
   - Iterates models from `EVALUATION_MODELS` in `reward_config.py`.
   - Selects Chinese/English prompts via `MODEL_LANGUAGE_OVERRIDES`.
   - Calls each model through `ChatOpenAI`, extracts function code, and writes:
     - `reward_generation_results.json`

2. **Stage2 (cross-model evaluation)**
   - Uses successful Stage1 candidates (requires at least 2).
   - Cross-scores each candidate with other evaluator models (no self-evaluation).
   - Uses strict JSON format and 5 dimensions:
     - `Goal Consistency`
     - `Exploration Effectiveness`
     - `Dynamic Reward Weighting`
     - `Mathematical Consistency`
     - `Robustness`
   - Per-evaluator total = sum of the 5 integer fields.
   - Final ranking = average total score.

3. **Best-candidate export**
   - Exports best candidate to `best_reward_function.py`.
   - Writes summary to `two_stage_summary.json`.

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

- `--generation-output` (default: `reward_generation_results.json`)
- `--best-output` (default: `best_reward_function.py`)
- `--summary-output` (default: `two_stage_summary.json`)

### Environment variables (validated at startup)

Required:

- `GROUP1_API_KEY`, `GROUP1_BASE_URL`
- `GROUP2_API_KEY`, `GROUP2_BASE_URL`
- `HUNYUAN_API_KEY`, `HUNYUAN_BASE_URL`
- `DOUBAO_API_KEY`, `DOUBAO_BASE_URL`

Model-to-env routing:

- default -> `GROUP1_*`
- `qwq-plus` -> `GROUP2_*`
- `doubao-1-5-thinking-pro-250415` -> `DOUBAO_*`

### Stage2 output files

- `auto_eval_reward_function_ranking.csv`
- `auto_eval_scores_by_reward_function.csv`
- `auto_eval_response_times_by_reward_function.csv`
- `auto_eval_average_response_time_by_model.csv`
- `best_reward_function.py`
- `two_stage_summary.json`

---

## RL training and evaluation

### Reward logging

During evaluation (`evaluate.py`), reward and packet metrics use the following consistent definitions:

1. In each evaluation episode, rewards from all forwarding/coding actions (source + relays, across all time steps) are accumulated into `total_reward`.
2. Let `source_send_count` denote the episode source-send count (the same per-episode quantity used for **`avg_s_f`**).
3. The episode reward is normalized by this `source_send_count`:
   - `normalized_reward = total_reward / source_send_count` (with zero-protection in code).
4. `evaluation_reward.txt` records the mean `normalized_reward` over all evaluation episodes.
5. `evaluation_avg_source_sends.txt` records **`avg_s_f`**, i.e., the mean `source_send_count` over all evaluation episodes.

Best checkpoint is selected by minimizing **`avg_s_f`**.

Best files are saved to:

`models/checkpoints/best_by_avg_source_send/`

- `dqn_agent_s_min.pt`
- `dqn_agent_r_min.pt`
- `best_epoch.pkl`
- `best_metric.txt`

Main result files:

- `result/evaluation_avg_source_sends.txt`
- `data_INCdeep_LLM/decode_probability_overhead_summary.csv`

---

## Key configuration knobs

Edit `config.py` and `config_topology.py` before experiments.

Most impactful parameters:

- `K` / `generation_size`: symbols per generation
- `M` / `relay_memory_rows`: relay coding-memory depth
- `num_episodes`: training episodes
- `Eval_interval`: run test every N training episodes
- `Force_eval_at_end`: if tail episodes are fewer than `Eval_interval`, force one final test at the end
- `max_source_sends_per_episode` (`Max_s_f`): per-episode source-send cap
- `epsilon_decay_episodes`: exploration decay length

### `config_topology.py` (network graph + link reliability)

Defines the forwarding topology and channel assumptions:

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

## Repository structure (core files)

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

## Example checkpoints and repository policy

- `models/examples/` is for demo checkpoints committed for quick testing/documentation.
- `models/checkpoints/` is for local training outputs and should remain untracked.
- For large `.pt/.pkl` files, use Git LFS when possible.

Recommended quick test command:

```bash
python main.py test --model-dir ./models/examples/best_by_avg_source_send
```

---

## Minimal success checklist

After a successful train run, you should see:

- `models/checkpoints/best_by_avg_source_send/dqn_agent_s_min.pt`
- `models/checkpoints/best_by_avg_source_send/dqn_agent_r_min.pt`
- `models/checkpoints/best_by_avg_source_send/best_epoch.pkl`
- `models/checkpoints/best_by_avg_source_send/best_metric.txt`
- `result/evaluation_avg_source_sends.txt`

---

## FAQ

### 1) `test` cannot find model files

Run training first, then confirm `--model-dir` contains:

- `dqn_agent_s_min.pt`
- `dqn_agent_r_min.pt`
- `best_epoch.pkl`

### 2) When should I use `--skip-compile`?

Use it when `torch.compile` has compatibility/stability issues on your platform.

### 3) Can I reuse old models after changing config?

Usually no, if changes affect state/action dimensions (e.g., `K`, `R`, `parallel_path`, `max_nb`, `action_size`). Retraining is recommended.

---

## Reproducibility notes

- Default random seed in code: `555`
- For reproducible comparisons, record:
  - Python / PyTorch / CUDA versions
  - full config values
  - episode/evaluation counts
  - checkpoint directory used for testing
