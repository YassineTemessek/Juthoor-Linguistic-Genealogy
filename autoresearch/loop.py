"""
loop.py — Hill-Climbing Orchestrator

Runs the autoresearch loop:
  1. Read program.md + experiment.py + recent log
  2. Ask an LLM agent to propose ONE change to experiment.py
  3. Write the proposed experiment.py
  4. Run prepare.py → result.json
  5. Accept (commit) or reject (revert) based on z-score
  6. Update program.md log
  7. Repeat

Usage:
    python loop.py --max-iterations 100 --model claude-sonnet-4-5-20250514
    python loop.py --max-iterations 50 --model gpt-4o --screen-permutations 20
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXPERIMENT_PY = ROOT / "experiment.py"
PROGRAM_MD = ROOT / "program.md"
BASELINE_JSON = ROOT / "baseline.json"
RESULTS_DIR = ROOT / "results"
RESULTS_DIR.mkdir(exist_ok=True)
LOGS_DIR = ROOT / "logs"
LOGS_DIR.mkdir(exist_ok=True)
LOG_FILE = LOGS_DIR / "agent.log"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def log(msg: str):
    """Append a timestamped message to the log file and print it."""
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def run_evaluation(permutations: int = 100) -> dict:
    """Run prepare.py and parse the JSON result."""
    cmd = [sys.executable, str(ROOT / "prepare.py"),
           "--permutations", str(permutations)]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

    if result.returncode != 0:
        log(f"  prepare.py FAILED: {result.stderr[:500]}")
        return {"error": result.stderr[:500], "z_best": -999}

    # Parse the last JSON object from stdout
    stdout = result.stdout.strip()
    # Find the last { ... } block
    brace_depth = 0
    json_start = -1
    for i in range(len(stdout) - 1, -1, -1):
        if stdout[i] == "}":
            if brace_depth == 0:
                json_end = i + 1
            brace_depth += 1
        elif stdout[i] == "{":
            brace_depth -= 1
            if brace_depth == 0:
                json_start = i
                break

    if json_start < 0:
        log(f"  Could not parse JSON from prepare.py output")
        return {"error": "No JSON in output", "z_best": -999}

    return json.loads(stdout[json_start:json_end])


def git_commit(message: str):
    """Commit experiment.py with the given message."""
    subprocess.run(["git", "add", "experiment.py"], cwd=ROOT)
    subprocess.run(["git", "commit", "-m", message], cwd=ROOT)


def git_revert():
    """Revert experiment.py to the last committed version."""
    subprocess.run(["git", "checkout", "experiment.py"], cwd=ROOT)


def load_baseline() -> dict:
    """Load the current baseline from baseline.json."""
    if BASELINE_JSON.exists():
        return json.loads(BASELINE_JSON.read_text())
    return {"z_best": 0.0, "real_count": 0, "iteration": 0}


def save_baseline(data: dict):
    BASELINE_JSON.write_text(json.dumps(data, indent=2))


def append_to_program_log(entry: str):
    """Append an entry to the ### Log section of program.md."""
    content = PROGRAM_MD.read_text(encoding="utf-8")
    content = content.rstrip() + f"\n{entry}\n"
    PROGRAM_MD.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# LLM Agent Call
# ---------------------------------------------------------------------------
def call_agent(model: str, iteration: int, baseline: dict) -> str | None:
    """Ask the LLM to propose a change to experiment.py.

    Returns the proposed new content of experiment.py, or None on failure.
    """
    program = PROGRAM_MD.read_text(encoding="utf-8")
    experiment = EXPERIMENT_PY.read_text(encoding="utf-8")

    prompt = f"""You are an autoresearch agent optimizing a linguistic scoring pipeline.

## Current state
- Iteration: {iteration}
- Baseline z-score: {baseline.get('z_best', 0):.4f}
- Baseline real_count: {baseline.get('real_count', 0)}
- Target: z >= 3.29

## Instructions (from program.md)
{program}

## Current experiment.py
```python
{experiment}
```

## Your task
Propose exactly ONE targeted change to experiment.py to improve the z-score.

Rules:
1. Change only 1-3 parameters at a time to isolate what works.
2. Respect all constraints listed in program.md.
3. Explain your hypothesis in 1-2 sentences BEFORE the code.
4. Output the COMPLETE new experiment.py file (not a diff).

Format your response as:

HYPOTHESIS: <your reasoning>

```python
<complete experiment.py file>
```
"""

    # Try Anthropic first, then OpenAI
    api_key_anthropic = os.environ.get("ANTHROPIC_API_KEY")
    api_key_openai = os.environ.get("OPENAI_API_KEY")

    if api_key_anthropic and "claude" in model.lower():
        return _call_anthropic(prompt, model, api_key_anthropic)
    elif api_key_openai:
        return _call_openai(prompt, model, api_key_openai)
    elif api_key_anthropic:
        return _call_anthropic(prompt, "claude-sonnet-4-5-20250514", api_key_anthropic)
    else:
        log("ERROR: No API key found. Set ANTHROPIC_API_KEY or OPENAI_API_KEY.")
        return None


def _call_anthropic(prompt: str, model: str, api_key: str) -> str | None:
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=model,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
        return _extract_python(response.content[0].text)
    except Exception as e:
        log(f"  Anthropic API error: {e}")
        return None


def _call_openai(prompt: str, model: str, api_key: str) -> str | None:
    try:
        import openai
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=model,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
        return _extract_python(response.choices[0].message.content)
    except Exception as e:
        log(f"  OpenAI API error: {e}")
        return None


def _extract_python(text: str) -> str | None:
    """Extract the python code block from the LLM response."""
    # Extract hypothesis
    if "HYPOTHESIS:" in text:
        hyp_line = text.split("HYPOTHESIS:")[1].split("\n")[0].strip()
        log(f"  Hypothesis: {hyp_line}")

    # Extract code between ```python and ```
    if "```python" in text:
        code = text.split("```python")[1].split("```")[0]
        return code.strip()
    elif "```" in text:
        code = text.split("```")[1].split("```")[0]
        return code.strip()
    return None


# ---------------------------------------------------------------------------
# Acceptance criteria
# ---------------------------------------------------------------------------
def should_accept(candidate: dict, baseline: dict) -> tuple[bool, str]:
    """Decide whether to accept the candidate.

    Returns (accept: bool, reason: str).
    """
    z_cand = candidate.get("z_best", -999)
    z_base = baseline.get("z_best", 0)
    rc_cand = candidate.get("real_count", 0)
    rc_base = baseline.get("real_count", 0)

    if "error" in candidate:
        return False, f"Error: {candidate['error']}"

    if z_cand < z_base - 0.01:  # allow tiny float noise
        return False, f"z regressed: {z_cand:.4f} < {z_base:.4f}"

    if z_cand > z_base + 0.05:
        return True, f"z improved: {z_cand:.4f} > {z_base:.4f} (+{z_cand - z_base:.4f})"

    if rc_cand > rc_base and z_cand >= z_base - 0.01:
        return True, f"count improved: {rc_cand} > {rc_base} (z stable at {z_cand:.4f})"

    return False, f"No improvement: z={z_cand:.4f} (base={z_base:.4f}), count={rc_cand} (base={rc_base})"


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Autoresearch hill-climbing loop")
    parser.add_argument("--max-iterations", type=int, default=100)
    parser.add_argument("--model", type=str, default="claude-sonnet-4-5-20250514")
    parser.add_argument("--screen-permutations", type=int, default=20,
                        help="Quick permutation count for screening (default 20)")
    parser.add_argument("--full-permutations", type=int, default=100,
                        help="Full permutation count for acceptance (default 100)")
    parser.add_argument("--run-baseline", action="store_true",
                        help="Run baseline evaluation and exit")
    args = parser.parse_args()

    log(f"=== Autoresearch Loop Starting ===")
    log(f"  Model: {args.model}")
    log(f"  Max iterations: {args.max_iterations}")
    log(f"  Screen permutations: {args.screen_permutations}")
    log(f"  Full permutations: {args.full_permutations}")

    # ---- Establish baseline ----
    baseline = load_baseline()
    if args.run_baseline or baseline.get("z_best", 0) == 0:
        log("Running baseline evaluation...")
        result = run_evaluation(permutations=args.full_permutations)
        if "error" in result:
            log(f"Baseline failed: {result['error']}")
            sys.exit(1)
        baseline = {
            "z_best": result["z_best"],
            "z_count": result["z_count"],
            "z_mean": result["z_mean"],
            "real_count": result["real_count"],
            "real_mean": result["real_mean"],
            "iteration": 0,
        }
        save_baseline(baseline)
        log(f"Baseline: z={baseline['z_best']:.4f}, count={baseline['real_count']}")
        if args.run_baseline:
            return

    # ---- Hill-climbing loop ----
    accepted = 0
    rejected = 0

    for iteration in range(1, args.max_iterations + 1):
        log(f"\n--- Iteration {iteration}/{args.max_iterations} ---")
        log(f"  Baseline: z={baseline['z_best']:.4f}, count={baseline['real_count']}")

        # 1. Ask agent for a proposal
        log("  Calling LLM agent...")
        proposed_code = call_agent(args.model, iteration, baseline)
        if proposed_code is None:
            log("  Agent returned no proposal. Skipping.")
            rejected += 1
            continue

        # 2. Backup and write proposed experiment.py
        backup = EXPERIMENT_PY.read_text(encoding="utf-8")
        EXPERIMENT_PY.write_text(proposed_code, encoding="utf-8")

        # 3. Quick screen (few permutations)
        log(f"  Running quick screen ({args.screen_permutations} permutations)...")
        screen_result = run_evaluation(permutations=args.screen_permutations)

        if screen_result.get("z_best", -999) < baseline["z_best"] - 0.5:
            log(f"  Quick screen REJECT: z={screen_result.get('z_best', -999):.4f}")
            EXPERIMENT_PY.write_text(backup, encoding="utf-8")
            rejected += 1
            append_to_program_log(
                f"- exp-{iteration:03d}: ❌ quick-reject "
                f"(z={screen_result.get('z_best', -999):.4f})"
            )
            continue

        # 4. Full evaluation
        log(f"  Running full evaluation ({args.full_permutations} permutations)...")
        result = run_evaluation(permutations=args.full_permutations)

        # Save result
        result_path = RESULTS_DIR / f"exp-{iteration:03d}.json"
        result_path.write_text(json.dumps(result, indent=2))

        # 5. Accept or reject
        accept, reason = should_accept(result, baseline)

        if accept:
            accepted += 1
            baseline = {
                "z_best": result["z_best"],
                "z_count": result["z_count"],
                "z_mean": result["z_mean"],
                "real_count": result["real_count"],
                "real_mean": result["real_mean"],
                "iteration": iteration,
            }
            save_baseline(baseline)
            git_commit(f"exp-{iteration:03d}: {reason}")
            append_to_program_log(
                f"- exp-{iteration:03d}: ✅ {reason}"
            )
            log(f"  ✅ ACCEPTED: {reason}")
        else:
            rejected += 1
            EXPERIMENT_PY.write_text(backup, encoding="utf-8")
            append_to_program_log(
                f"- exp-{iteration:03d}: ❌ {reason}"
            )
            log(f"  ❌ REJECTED: {reason}")

        # Check if we've crossed the gate
        if baseline["z_best"] >= 3.29:
            log(f"\n🎉 GATE CROSSED! z = {baseline['z_best']:.4f} >= 3.29")
            log(f"  Null model validated at p < 0.001 after {iteration} iterations.")
            break

    # ---- Summary ----
    log(f"\n{'=' * 70}")
    log(f"LOOP COMPLETE")
    log(f"  Iterations: {accepted + rejected}")
    log(f"  Accepted: {accepted}")
    log(f"  Rejected: {rejected}")
    log(f"  Final z: {baseline['z_best']:.4f}")
    log(f"  Final count: {baseline['real_count']}")
    log(f"{'=' * 70}")


if __name__ == "__main__":
    main()
