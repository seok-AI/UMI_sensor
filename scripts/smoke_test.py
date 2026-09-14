#!/usr/bin/env python3
"""Dependency/config smoke test. Does not require sensors to be connected."""

import importlib.metadata
from pathlib import Path

packages = ["anyskin", "numpy", "matplotlib", "pyserial", "onnxruntime"]
failed = False
for pkg in packages:
    try:
        print(f"{pkg:12s} {importlib.metadata.version(pkg)}")
    except Exception as e:
        failed = True
        print(f"{pkg:12s} ERROR: {e}")

root = Path(__file__).resolve().parents[1]
for rel in [
    "coinft/hardware_configs/CFT24_MLP.onnx",
    "coinft/hardware_configs/CFT24_norm.json",
]:
    p = root / rel
    print(f"{rel:55s} {'OK' if p.exists() else 'MISSING'}")
    failed |= not p.exists()

if failed:
    raise SystemExit(1)
print("\nRuntime smoke test passed.")
