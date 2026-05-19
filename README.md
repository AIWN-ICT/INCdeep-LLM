<<<<<<< HEAD
# INCdeep-LLM

A two-stage workflow for adaptive network coding:

1. **LLM generation + cross-model evaluation of reward functions** (`reward_pipeline_cli.py` / `reward_pipeline_runner.py`)
2. **RL training with the selected reward function** (two DQN agents for source/relay decisions)

In short, this project first uses multiple LLMs to generate reward-function candidates and evaluate them with structured scoring, then exports the best candidate and integrates it into RL training, with `avg_s_f` as the primary downstream KPI.

## Quick Start

Install dependencies:

```bash
pip install -r requirements.txt
```

Train:

```bash
python main.py train
```

Test with example checkpoint:

```bash
python main.py test --model-dir ./models/examples/best_by_avg_source_send
```

> If `torch.compile` is unstable in your environment, add `--skip-compile`.

### 30-second workflow (recommended)

Use this checklist if you want the full two-stage pipeline (LLM reward evaluation → RL training):

1. **Stage A — Run LLM-based reward evaluation**

```bash
python reward_pipeline_cli.py --mode both
```

2. **Stage A — Select a reward candidate**
   - Open `auto_eval_reward_function_ranking.csv` (best overall ranking).
   - Cross-check with `auto_eval_scores_by_reward_function.csv` (per-evaluator consistency).

3. **Stage B — Integrate selected reward into simulator**
   - Update reward logic in `simulator.py` (`forward_data(...)`, optionally `calculate_reward(...)`).

4. **Stage B — Train RL agents**

```bash
python main.py train
```

5. **Stage B — Evaluate training KPI**
   - Inspect `result/evaluation_avg_source_sends.txt`.
   - Use `avg_s_f` (lower is better) as the primary comparison metric.

---

## What this project does

`INCdeep-LLM` combines **LLM-based reward engineering** with **RL training** in one pipeline:

- **Stage A (LLM):** generate and evaluate reward-function candidates with multiple evaluator models.
- **Stage B (RL):** integrate one selected reward into `simulator.py` and train two DQN agents:
  - Source-side agent (`agent_s`)
  - Relay-side agent (`agent_r`)

Both agents learn coding/forwarding decisions from local packet-memory states under configurable topology and link-loss settings.

---

## Main KPI

- **`avg_s_f`**: average source transmissions during evaluation (**lower is better**).

Use this as the primary metric when comparing experiments.

---

## LLM reward pipeline (aligned with current code)

This section maps to the following files:

- CLI entry: `reward_pipeline_cli.py`
- Two-stage orchestration: `reward_pipeline_runner.py`
- Stage1 generation: `reward_generation_runner.py`
- Stage2 evaluation/reporting: `reward_eval_runner.py`
- Config and model routing: `reward_config.py`
- Prompt templates: `reward_prompt_templates.py`
- Built-in candidate assets: `reward_prompt_assets.py`

### Workflow overview

This is a two-stage flow: generate candidates, evaluate candidates, then export the best one.

1. **Stage1 (generation)**
   - Iterates models from `EVALUATION_MODELS` in `reward_config.py`.
   - Selects Chinese/English generation prompts per model via `MODEL_LANGUAGE_OVERRIDES` (from `REWARD_FUNCTION_DESIGN_PROMPTS_BY_LANGUAGE`).
   - Calls each model through `ChatOpenAI` and extracts function code from output (priority: fenced code block, then from first `def`).
   - Writes results to `reward_generation_results.json` with fields such as `ok`, `elapsed_seconds`, `reward_function_text`, `raw_response`, or `error`.

2. **Stage2 (cross-model evaluation)**
   - Extracts candidates from successful Stage1 results (requires at least 2 candidates, otherwise exits with error).
   - For each candidate, uses the remaining evaluator models to score it (a model does not score its own candidate).
   - Uses templates from `reward_prompt_templates.py` (`PROMPTS_BY_LANGUAGE`) with strict JSON output constraints (`FORMAT_INSTRUCTION`).
   - Applies 5 scoring dimensions:
     - `Goal Consistency`
     - `Exploration Effectiveness`
     - `Dynamic Reward Weighting`
     - `Mathematical Consistency`
     - `Robustness`
   - Per-evaluator total score is the sum of the 5 integer fields; candidate ranking uses the average total score.

3. **Best-candidate export**
   - Selects the top candidate by average score.
   - Exports it to `best_reward_function.py` (with source model and average-score comments).
   - Writes `two_stage_summary.json` (`best_model`, `best_score`, output paths, etc.).

### CLI usage

Run full two-stage flow (Stage1 -> Stage2):

```bash
python reward_pipeline_cli.py --mode both
```

Run generation only:

```bash
python reward_pipeline_cli.py --mode stage1
```

Run evaluation only (reuse existing generation output):

```bash
python reward_pipeline_cli.py --mode stage2
```

Optional arguments:

- `--generation-output` (default: `reward_generation_results.json`)
- `--best-output` (default: `best_reward_function.py`)
- `--summary-output` (default: `two_stage_summary.json`)

### Environment variables (validated at startup)

`reward_config.py` validates these variables on import; missing values raise an immediate error:

- `GROUP1_API_KEY`, `GROUP1_BASE_URL`
- `GROUP2_API_KEY`, `GROUP2_BASE_URL`
- `HUNYUAN_API_KEY`, `HUNYUAN_BASE_URL`
- `DOUBAO_API_KEY`, `DOUBAO_BASE_URL`

Model-to-env routing:

- default -> `GROUP1_*`
- `qwq-plus` -> `GROUP2_*`
- `doubao-1-5-thinking-pro-250415` -> `DOUBAO_*`

### Evaluation output files

Stage2 writes the following files at project root:

- `auto_eval_reward_function_ranking.csv`: candidates ranked by average score (descending)
- `auto_eval_scores_by_reward_function.csv`: per-candidate scores from each evaluator model
- `auto_eval_response_times_by_reward_function.csv`: per-candidate latency by evaluator model
- `auto_eval_average_response_time_by_model.csv`: average latency by evaluator model
- `best_reward_function.py`: auto-selected best reward function
- `two_stage_summary.json`: two-stage summary

### How this connects to RL training

This pipeline is for reward-function selection, not direct training. Recommended handoff:

1. Run the pipeline to produce `best_reward_function.py` and ranking reports.
2. Integrate the selected reward logic into the reward path in `simulator.py`.
3. Run RL training: `python main.py train`.
4. Compare against baseline using `avg_s_f` (lower is better).
---

## Where to check results

1. `result/evaluation_avg_source_sends.txt`  
   Main KPI curve/value (`avg_s_f`)

2. `models/checkpoints/best_by_avg_source_send/best_metric.txt`  
   Best epoch + best KPI snapshot

3. `data_INCdeep_LLM/decode_probability_overhead_summary.csv`  
   Decode probability and overhead summary

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
│  ├─ checkpoints/             # local training outputs (ignored)
│  └─ examples/                # tracked demo checkpoints
│     └─ best_by_avg_source_send/
└─ result/
```

---

## Key configuration knobs

Edit `config.py` and `config_topology.py` before experiments.

Most impactful parameters:

- `K` / `generation_size`: symbols per generation
- `M` / `relay_memory_rows`: relay coding-memory depth
- `num_episodes`: training episodes
- `max_source_sends_per_episode` (`Max_s_f`): per-episode source-send cap
- `epsilon_decay_episodes`: exploration decay length

---

## Network coding context and important files

### `config_topology.py` (network graph + link reliability)

This file defines the **forwarding topology** used by the simulator:

- `node_num`: total number of nodes in the network.
- `parallel_path`: number of parallel source-to-destination paths expected by the setup.
- `max_nb`: max outgoing neighbors considered in state/action design.
- `neighbor_matrix`: directed connectivity matrix (who can forward to whom).
- `links`: per-link delivery probability matrix (used to model packet loss).

In short, `config_topology.py` determines the physical communication graph and channel quality assumptions under which both DQN agents are trained and evaluated.

### `data_processor.py` (post-processing and metric export)

This file provides helper functions for **evaluation statistics and CSV outputs**:

- Computes standard deviation of source-send counts.
- Saves per-episode source-send counts to CSV.
- Computes decode probability curve: \(P(\text{source sends} \le t)\) for thresholds `t = 1..60`.
- Writes summary CSV including decode probability, average overhead, std deviation, and `avg_s_f`.

In short, `data_processor.py` converts raw evaluation results into reproducible tables/curves for analysis and reporting.

---

## Best model selection

During training, checkpoint selection is based on evaluation performance:

- Minimize `avg_s_f`

When improved, best files are saved to:

`models/checkpoints/best_by_avg_source_send/`

- `dqn_agent_s_min.pt`
- `dqn_agent_r_min.pt`
- `best_epoch.pkl`
- `best_metric.txt`

---

## Example checkpoints and repository policy

- `models/examples/` is for **demo checkpoints** committed to GitHub for quick testing and documentation.
- `models/checkpoints/` is for local training outputs and should remain untracked.
- For large `.pt/.pkl` files, use Git LFS when possible.

Recommended quick test command:

```bash
python main.py test --model-dir ./models/examples/best_by_avg_source_send
```

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
=======
# INCdeep-LLM

A two-stage workflow for adaptive network coding:

1. **LLM generation + cross-model evaluation of reward functions** (`reward_pipeline_cli.py` / `reward_pipeline_runner.py`)
2. **RL training with the selected reward function** (two DQN agents for source/relay decisions)

In short, this project first uses multiple LLMs to generate reward-function candidates and evaluate them with structured scoring, then exports the best candidate and integrates it into RL training, with `avg_s_f` as the primary downstream KPI.

## Quick Start

Install dependencies:

```bash
pip install -r requirements.txt
```

Train:

```bash
python main.py train
```

Test with example checkpoint:

```bash
python main.py test --model-dir ./models/examples/best_by_avg_source_send
```

> If `torch.compile` is unstable in your environment, add `--skip-compile`.

### 30-second workflow (recommended)

Use this checklist if you want the full two-stage pipeline (LLM reward evaluation → RL training):

1. **Stage A — Run LLM-based reward evaluation**

```bash
python reward_pipeline_cli.py --mode both
```

2. **Stage A — Select a reward candidate**
   - Open `auto_eval_reward_function_ranking.csv` (best overall ranking).
   - Cross-check with `auto_eval_scores_by_reward_function.csv` (per-evaluator consistency).

3. **Stage B — Integrate selected reward into simulator**
   - Update reward logic in `simulator.py` (`forward_data(...)`, optionally `calculate_reward(...)`).

4. **Stage B — Train RL agents**

```bash
python main.py train
```

5. **Stage B — Evaluate training KPI**
   - Inspect `result/evaluation_avg_source_sends.txt`.
   - Use `avg_s_f` (lower is better) as the primary comparison metric.

---

## What this project does

`INCdeep-LLM` combines **LLM-based reward engineering** with **RL training** in one pipeline:

- **Stage A (LLM):** generate and evaluate reward-function candidates with multiple evaluator models.
- **Stage B (RL):** integrate one selected reward into `simulator.py` and train two DQN agents:
  - Source-side agent (`agent_s`)
  - Relay-side agent (`agent_r`)

Both agents learn coding/forwarding decisions from local packet-memory states under configurable topology and link-loss settings.

---

## Main KPI

- **`avg_s_f`**: average source transmissions during evaluation (**lower is better**).

Use this as the primary metric when comparing experiments.

---

## LLM reward pipeline (aligned with current code)

This section maps to the following files:

- CLI entry: `reward_pipeline_cli.py`
- Two-stage orchestration: `reward_pipeline_runner.py`
- Stage1 generation: `reward_generation_runner.py`
- Stage2 evaluation/reporting: `reward_eval_runner.py`
- Config and model routing: `reward_config.py`
- Prompt templates: `reward_prompt_templates.py`
- Built-in candidate assets: `reward_prompt_assets.py`

### Workflow overview

This is a two-stage flow: generate candidates, evaluate candidates, then export the best one.

1. **Stage1 (generation)**
   - Iterates models from `EVALUATION_MODELS` in `reward_config.py`.
   - Selects Chinese/English generation prompts per model via `MODEL_LANGUAGE_OVERRIDES` (from `REWARD_FUNCTION_DESIGN_PROMPTS_BY_LANGUAGE`).
   - Calls each model through `ChatOpenAI` and extracts function code from output (priority: fenced code block, then from first `def`).
   - Writes results to `reward_generation_results.json` with fields such as `ok`, `elapsed_seconds`, `reward_function_text`, `raw_response`, or `error`.

2. **Stage2 (cross-model evaluation)**
   - Extracts candidates from successful Stage1 results (requires at least 2 candidates, otherwise exits with error).
   - For each candidate, uses the remaining evaluator models to score it (a model does not score its own candidate).
   - Uses templates from `reward_prompt_templates.py` (`PROMPTS_BY_LANGUAGE`) with strict JSON output constraints (`FORMAT_INSTRUCTION`).
   - Applies 5 scoring dimensions:
     - `Goal Consistency`
     - `Exploration Effectiveness`
     - `Dynamic Reward Weighting`
     - `Mathematical Consistency`
     - `Robustness`
   - Per-evaluator total score is the sum of the 5 integer fields; candidate ranking uses the average total score.

3. **Best-candidate export**
   - Selects the top candidate by average score.
   - Exports it to `best_reward_function.py` (with source model and average-score comments).
   - Writes `two_stage_summary.json` (`best_model`, `best_score`, output paths, etc.).

### CLI usage

Run full two-stage flow (Stage1 -> Stage2):

```bash
python reward_pipeline_cli.py --mode both
```

Run generation only:

```bash
python reward_pipeline_cli.py --mode stage1
```

Run evaluation only (reuse existing generation output):

```bash
python reward_pipeline_cli.py --mode stage2
```

Optional arguments:

- `--generation-output` (default: `reward_generation_results.json`)
- `--best-output` (default: `best_reward_function.py`)
- `--summary-output` (default: `two_stage_summary.json`)

### Environment variables (validated at startup)

`reward_config.py` validates these variables on import; missing values raise an immediate error:

- `GROUP1_API_KEY`, `GROUP1_BASE_URL`
- `GROUP2_API_KEY`, `GROUP2_BASE_URL`
- `HUNYUAN_API_KEY`, `HUNYUAN_BASE_URL`
- `DOUBAO_API_KEY`, `DOUBAO_BASE_URL`

Model-to-env routing:

- default -> `GROUP1_*`
- `qwq-plus` -> `GROUP2_*`
- `doubao-1-5-thinking-pro-250415` -> `DOUBAO_*`

### Evaluation output files

Stage2 writes the following files at project root:

- `auto_eval_reward_function_ranking.csv`: candidates ranked by average score (descending)
- `auto_eval_scores_by_reward_function.csv`: per-candidate scores from each evaluator model
- `auto_eval_response_times_by_reward_function.csv`: per-candidate latency by evaluator model
- `auto_eval_average_response_time_by_model.csv`: average latency by evaluator model
- `best_reward_function.py`: auto-selected best reward function
- `two_stage_summary.json`: two-stage summary

### How this connects to RL training

This pipeline is for reward-function selection, not direct training. Recommended handoff:

1. Run the pipeline to produce `best_reward_function.py` and ranking reports.
2. Integrate the selected reward logic into the reward path in `simulator.py`.
3. Run RL training: `python main.py train`.
4. Compare against baseline using `avg_s_f` (lower is better).
---

## Where to check results

1. `result/evaluation_avg_source_sends.txt`  
   Main KPI curve/value (`avg_s_f`)

2. `models/checkpoints/best_by_avg_source_send/best_metric.txt`  
   Best epoch + best KPI snapshot

3. `data_INCdeep_LLM/decode_probability_overhead_summary.csv`  
   Decode probability and overhead summary

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
│  ├─ checkpoints/             # local training outputs (ignored)
│  └─ examples/                # tracked demo checkpoints
│     └─ best_by_avg_source_send/
└─ result/
```

---

## Key configuration knobs

Edit `config.py` and `config_topology.py` before experiments.

Most impactful parameters:

- `K` / `generation_size`: symbols per generation
- `M` / `relay_memory_rows`: relay coding-memory depth
- `num_episodes`: training episodes
- `max_source_sends_per_episode` (`Max_s_f`): per-episode source-send cap
- `epsilon_decay_episodes`: exploration decay length

---

## Network coding context and important files

### `config_topology.py` (network graph + link reliability)

This file defines the **forwarding topology** used by the simulator:

- `node_num`: total number of nodes in the network.
- `parallel_path`: number of parallel source-to-destination paths expected by the setup.
- `max_nb`: max outgoing neighbors considered in state/action design.
- `neighbor_matrix`: directed connectivity matrix (who can forward to whom).
- `links`: per-link delivery probability matrix (used to model packet loss).

In short, `config_topology.py` determines the physical communication graph and channel quality assumptions under which both DQN agents are trained and evaluated.

### `data_processor.py` (post-processing and metric export)

This file provides helper functions for **evaluation statistics and CSV outputs**:

- Computes standard deviation of source-send counts.
- Saves per-episode source-send counts to CSV.
- Computes decode probability curve: \(P(\text{source sends} \le t)\) for thresholds `t = 1..60`.
- Writes summary CSV including decode probability, average overhead, std deviation, and `avg_s_f`.

In short, `data_processor.py` converts raw evaluation results into reproducible tables/curves for analysis and reporting.

---

## Best model selection

During training, checkpoint selection is based on evaluation performance:

- Minimize `avg_s_f`

When improved, best files are saved to:

`models/checkpoints/best_by_avg_source_send/`

- `dqn_agent_s_min.pt`
- `dqn_agent_r_min.pt`
- `best_epoch.pkl`
- `best_metric.txt`

---

## Example checkpoints and repository policy

- `models/examples/` is for **demo checkpoints** committed to GitHub for quick testing and documentation.
- `models/checkpoints/` is for local training outputs and should remain untracked.
- For large `.pt/.pkl` files, use Git LFS when possible.

Recommended quick test command:

```bash
python main.py test --model-dir ./models/examples/best_by_avg_source_send
```

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
>>>>>>> 7d2f6d8c28f3c5b7e47d00807eec56d14f052984
