#!/usr/bin/env python3
"""
benchmark.py – Fully automated MSSP benchmark harness.

Runs omp_mssp, pth_mssp, mpi_mssp on both datasets for
thread/process counts {1,2,4,8,12,16}, collects elapsed time,
writes per-run distance files and a summary CSV.
"""

import subprocess
import os
import sys
import csv
import re
import time

BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR     = os.path.join(BASE_DIR, "src")
RESULT_DIR  = os.path.join(BASE_DIR, "result")
DATA_DIR    = os.path.join(BASE_DIR, "data")

DATASETS = [
    ("flower", os.path.join(DATA_DIR, "updated_flower.csv")),
    ("mouse",  os.path.join(DATA_DIR, "updated_mouse.csv")),
]

FRAMEWORKS = [
    ("omp",  os.path.join(SRC_DIR, "omp_mssp"),  False),
    ("pth",  os.path.join(SRC_DIR, "pth_mssp"),  False),
    ("mpi",  os.path.join(SRC_DIR, "mpi_mssp"),  True),
]

THREAD_COUNTS = [1, 2, 4, 8, 12, 16]

os.makedirs(RESULT_DIR, exist_ok=True)

# MPI root override (this is WSL2 single-node, safe)
MPI_ENV = os.environ.copy()
MPI_ENV["OMPI_ALLOW_RUN_AS_ROOT"] = "1"
MPI_ENV["OMPI_ALLOW_RUN_AS_ROOT_CONFIRM"] = "1"


def run_omp_pth(binary, dataset_path, nthreads, prefix):
    """Run OpenMP / Pthreads binary, return elapsed seconds."""
    cmd = [binary, dataset_path, str(nthreads), prefix]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if proc.returncode != 0:
        print(f"  ERROR (rc={proc.returncode}): {proc.stderr[:300]}")
        return None
    m = re.search(r"TIME:\s*([\d.]+)", proc.stdout)
    if m:
        return float(m.group(1))
    print(f"  WARNING: could not parse TIME from stdout:\n{proc.stdout[:200]}")
    return None


def run_mpi(binary, dataset_path, nprocs, prefix):
    """Run MPI binary via mpirun, return elapsed seconds."""
    cmd = ["mpirun", "--oversubscribe", "-np", str(nprocs),
           binary, dataset_path, prefix]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600,
                          env=MPI_ENV)
    if proc.returncode != 0:
        print(f"  ERROR (rc={proc.returncode}): {proc.stderr[:300]}")
        return None
    m = re.search(r"TIME:\s*([\d.]+)", proc.stdout)
    if m:
        return float(m.group(1))
    print(f"  WARNING: could not parse TIME from stdout:\n{proc.stdout[:200]}")
    return None


def main():
    results = []

    for ds_tag, ds_path in DATASETS:
        print(f"\n{'='*60}")
        print(f"  Dataset: {ds_tag}  ({ds_path})")
        print(f"{'='*60}")

        for fw_tag, fw_bin, is_mpi in FRAMEWORKS:
            print(f"\n  --- {fw_tag} ---")

            for n in THREAD_COUNTS:
                prefix = f"{ds_tag}_{fw_tag}_{n:02d}"
                print(f"    Running {prefix} ...", end=" ", flush=True)

                if is_mpi:
                    elapsed = run_mpi(fw_bin, ds_path, n, prefix)
                else:
                    elapsed = run_omp_pth(fw_bin, ds_path, n, prefix)

                if elapsed is not None:
                    print(f"  {elapsed:.6f} s")
                    results.append({
                        "dataset":    ds_tag,
                        "framework":  fw_tag,
                        "threads":    n,
                        "time_sec":   elapsed,
                    })
                else:
                    print("  FAILED")
                    results.append({
                        "dataset":    ds_tag,
                        "framework":  fw_tag,
                        "threads":    n,
                        "time_sec":   None,
                    })

    # ---- Write summary CSV ----
    csv_path = os.path.join(RESULT_DIR, "benchmark_metrics.csv")
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["dataset","framework","threads","time_sec"])
        writer.writeheader()
        writer.writerows(results)
    print(f"\nSummary written to {csv_path}")

    # ---- Quick correctness check ----
    print("\n--- Correctness Verification ---")
    for ds_tag, _ in DATASETS:
        ref_file = None
        for fw_tag, _, _ in FRAMEWORKS:
            fpath = os.path.join(RESULT_DIR, f"{ds_tag}_{fw_tag}_01_distance.txt")
            if os.path.exists(fpath):
                if ref_file is None:
                    ref_file = fpath
                    continue
                with open(ref_file) as a, open(fpath) as b:
                    la = a.readlines()
                    lb = b.readlines()
                if la == lb:
                    print(f"  {ds_tag}: {fw_tag}_01 == reference  ✓")
                else:
                    print(f"  {ds_tag}: {fw_tag}_01 MISMATCH  ✗")
                    for i, (x, y) in enumerate(zip(la, lb)):
                        if x != y:
                            print(f"    line {i}: ref={x.strip()}, got={y.strip()}")
                            break


if __name__ == "__main__":
    main()
