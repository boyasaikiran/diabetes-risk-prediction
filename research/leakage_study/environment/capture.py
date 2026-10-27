"""Capture the environment: package versions, hardware, git state, data hash. Run before any experiment (gate G1)."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
from datetime import UTC, datetime
from importlib import metadata
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PKGS = ["numpy", "pandas", "scipy", "scikit-learn", "joblib", "PyYAML", "pytest"]


def git(*args: str) -> str:
    try:
        return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, timeout=30).stdout.strip()
    except Exception:  # noqa: BLE001
        return ""


info = {
    "captured_utc": datetime.now(UTC).isoformat(timespec="seconds"),
    "python": sys.version.split()[0],
    "platform": platform.platform(),
    "processor": platform.processor(),
    "cpu_count": os.cpu_count(),
    "packages": {p: metadata.version(p) for p in PKGS},
    "git_commit": git("rev-parse", "HEAD"),
    "git_tags_at_head": git("tag", "--points-at", "HEAD"),
    "prereg_tag_commit": git("rev-list", "-n", "1", "prereg-v1"),
    "git_dirty_files": len(git("status", "--porcelain").splitlines()),
    "data_sha256": hashlib.sha256((ROOT / "data" / "raw" / "pima_diabetes.csv").read_bytes()).hexdigest(),
}
(HERE / "environment.json").write_text(json.dumps(info, indent=1), encoding="utf-8")
print(json.dumps(info, indent=1))
