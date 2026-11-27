#!/usr/bin/env python3
"""Paired circular moving-block bootstrap of frozen annual COUP scores."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAIRS = (("country_constrained", "global_recent"),
         ("prior5_constrained", "global_recent"),
         ("prior5_constrained", "country_constrained"))
METRICS = ("brier", "log_loss")
SEED = 27012026
DRAWS = 20000

def evaluate(folds):
    if [f["year"] for f in folds] != list(range(1980, 2025)):
        raise ValueError("Unexpected evaluation years")
    if sum(f["n"] for f in folds) != 8241 or sum(f["positives"] for f in folds) != 186:
        raise ValueError("Unexpected evaluation denominators")
    if any(f["n"] <= 0 or not 0 <= f["positives"] <= f["n"] for f in folds):
        raise ValueError("Invalid denominators")
    n_years = len(folds)
    weights = [f["n"] for f in folds]
    diffs = {(m, ref, metric): [f["n"] * (f["scores"][ref][metric] -
              f["scores"][m][metric]) for f in folds]
             for m, ref in PAIRS for metric in METRICS}
    results = []
    for length in (1, 3, 5):
        state = SEED
        samples = {key: [] for key in diffs}
        for _ in range(DRAWS):
            idx = []
            while len(idx) < n_years:
                state = (state * 1664525 + 1013904223) & 0xffffffff
                start = state * n_years // 4294967296
                idx.extend((start + j) % n_years
                           for j in range(min(length, n_years - len(idx))))
            den = sum(weights[i] for i in idx)
            for key, values in diffs.items():
                samples[key].append(sum(values[i] for i in idx) / den)
        for model, reference in PAIRS:
            row = {"block": length, "model": model, "reference": reference}
            for metric in METRICS:
                v = sorted(samples[model, reference, metric])
                row[metric] = {"lo": round(v[499], 9), "hi": round(v[19499], 9),
                               "fraction_positive": sum(x > 0 for x in v) / DRAWS}
            results.append(row)
    return results

def main():
    source = json.loads((ROOT / "data/coup-mean-constraint.json").read_text())
    frozen = json.loads((ROOT / "data/coup-temporal-uncertainty.json").read_text())
    if source["status"] != "EXPLORATORY_POST_BENCHMARK_NOT_INDEPENDENT_TEST":
        raise ValueError("Unexpected source status")
    results = evaluate(source["folds"])
    if "--check" in sys.argv and results != frozen["results"]:
        raise ValueError("Frozen bootstrap results differ")
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()
