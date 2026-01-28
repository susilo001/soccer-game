# AI Agent Instructions (Soccer ML + Python)

These rules are mandatory for any AI agent contributing to this repository.

---

## 1) Project Goal

This repository predicts or simulates soccer match outcomes using Python + ML.
Primary objectives:

- Correct, leak-free modeling
- Reproducible experiments
- Clear evaluation and baselines
- Minimal, reviewable changes

---

## 2) Hard Boundaries (Scope)

- Only change what is needed for the task.
- Do not refactor unrelated code.
- Touch the fewest files possible.
- If you see an issue unrelated to the task: mention it, do not fix it.

---

## 3) Data Rules (No Leakage)

Treat leakage as a critical bug.

You must ensure:

- No future information is used at training time.
- Splits are time-aware (by match date) unless explicitly stated otherwise.
- Feature engineering uses only information available *before kickoff* (or before the prediction timestamp).
- Any aggregation features (rolling means, form, ELO, team stats) are computed using **past-only windows**.

Prohibited examples:

- Using final score–derived fields as features.
- Calculating season averages using matches after the prediction match.
- Random train/test split on time-series match data (unless the task explicitly requires it).

---

## 4) Reproducibility

All training/evaluation code must be reproducible:

- Set random seeds (numpy, python, and model frameworks used).
- Make dataset versioning explicit (file name/hash/date range).
- Avoid nondeterministic behavior where possible.
- Log config and metrics for each run.

If you add a CLI or config:

- Prefer a single config file (YAML/TOML) or argparse.
- Defaults must be safe and deterministic.

---

## 5) Modeling Expectations

When adding or changing a model:

- Keep a simple baseline (e.g., logistic regression / Poisson goals / ELO-only) available.
- Do not remove baselines.
- Prefer interpretable features unless performance requires otherwise.

When doing match prediction, be explicit about target:

- 1X2 (home/draw/away)
- goals (Poisson / regression)
- both teams to score
- over/under

Targets and labels must be defined in one place.

---

## 6) Evaluation Standards (Required)

Always report metrics with proper splits:

For classification (1X2, BTTS, O/U):

- Log loss (primary)
- Brier score (probability calibration)
- Accuracy as a secondary metric
- Confusion matrix only if useful

For goals modeling:

- Poisson deviance or MAE/RMSE
- Calibration checks if output is probabilistic

Betting-style evaluation (only if requested):

- Expected value and ROI with clear assumptions
- Never imply guaranteed profit

Cross-validation rules:

- Prefer time-series CV (rolling/expanding window) over random K-fold.

---

## 7) Probabilities Must Be Calibrated

If outputs are probabilities:

- Ensure they sum to 1 for mutually exclusive events (e.g., 1X2).
- Add/keep calibration checks (reliability curve / ECE) if available.
- Don’t “clip” probabilities unless clearly justified.

---

## 8) Feature Engineering Guidelines

- Features must be defined and documented in one module.
- Use clear naming: `team_form_5`, `elo_diff`, `home_adv`, `rest_days`.
- Rolling features must specify window and cutoff.
- Avoid target leakage via post-match stats.

If using player data:

- Ensure availability at prediction time (lineups known vs unknown).
- Clearly distinguish “pre-match” vs “in-play” features.

---

## 9) Data & Artifacts Handling

- Do not commit large raw datasets unless the repo already does.
- Store derived artifacts (models, encoders) under `/artifacts` or `/models` with version tags.
- Never overwrite artifacts silently—write to a new path or require an explicit `--overwrite`.

---

## 10) Tests

Minimum expectations:

- Unit tests for feature generation (time cutoff correctness).
- A test that fails if leakage occurs (e.g., using future matches in aggregates).
- A small “smoke” training run on tiny sample data.

Do not change existing tests unless instructed.
If a test fails, fix the implementation rather than weakening the test.

---

## 11) Performance & Engineering

- Prefer pandas vectorization over slow Python loops.
- Keep memory usage reasonable; avoid duplicating huge DataFrames.
- Any optimization must include a before/after measurement.

---

## 12) Documentation

If behavior changes:

- Update README or relevant docs.
  Docs must:
- Explain target(s), splits, metrics, and how to run training/eval.
- Avoid vague claims like “state-of-the-art”.

---

## 13) Honesty Rules (Non-Negotiable)

- Do not claim code was executed unless it actually was.
- Do not invent dataset columns or file paths.
- If unsure, state uncertainty and choose the conservative implementation.
