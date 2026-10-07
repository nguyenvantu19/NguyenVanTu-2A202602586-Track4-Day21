"""Recreate every submitted CSV/figure and run the lab checks on CPU.

Run from the repository root: python -m src.run_lab.
Does not download data, modify original data or run Git commands.
"""
import argparse
import os
from pathlib import Path
import subprocess
import sys


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[1]
    commands = [
        ["tools/verify_data.py", "--data-root", "data/kitti_mini"],
        ["tools/verify_data.py", "--data-root", "data/nuscenes_mini_subset"],
        ["-m", "starter.data_health", "--data-root", "data/synthetic", "--out", "results/data_health.csv"],
        ["-m", "starter.data_health", "--data-root", "data/kitti_mini", "--out", "results/data_health_kitti.csv"],
        ["-m", "starter.data_health", "--data-root", "data/nuscenes_mini_subset", "--out", "results/data_health_nusc.csv"],
        ["-m", "src.validate_projection"],
        ["-m", "starter.projection", "--data-root", "data/synthetic", "--frame", "000000"],
        *[["-m", "starter.projection", "--data-root", "data/kitti_mini", "--frame", frame]
          for frame in ("000019", "000011", "000004")],
        ["-m", "starter.projection", "--data-root", "data/nuscenes_mini_subset", "--frame", "scene-0103_010"],
        ["-m", "src.benchmark_projection"],
        ["-m", "src.failure_case_demo"],
        ["tools/check_submission.py"],
    ]
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    for command in commands:
        print("RUN python " + " ".join(command), flush=True)
        result = subprocess.run([sys.executable, *command], cwd=root, env=env,
                                capture_output=True, text=True, encoding="utf-8")
        if result.returncode:
            print(result.stdout)
            print(result.stderr, file=sys.stderr)
            raise SystemExit(result.returncode)
        if command == ["tools/check_submission.py"] or command == ["-m", "src.validate_projection"]:
            print(result.stdout.rstrip())
        else:
            lines = result.stdout.rstrip().splitlines()
            print(lines[-1] if lines else "PASS")
    print("PASS: all 14 steps completed")


if __name__ == "__main__":
    main()
