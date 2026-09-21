"""Verify the local CDCN port numerically against a pinned official checkout."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

import torch

from deepface_pad.models import OFFICIAL_CDCN_PROVENANCE, OfficialCDCN


def _load_official(source: Path):
    spec = importlib.util.spec_from_file_location("official_cdcn_source", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load official CDCN source: {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.CDCN(theta=0.7)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--official-root", required=True)
    args = parser.parse_args()

    root = Path(args.official_root)
    source = root / OFFICIAL_CDCN_PROVENANCE["source_file"]
    actual_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    expected_hash = OFFICIAL_CDCN_PROVENANCE["source_sha256"]
    print(f"official source SHA256: {actual_hash}", flush=True)
    if actual_hash != expected_hash:
        raise SystemExit(
            f"official source checksum mismatch: {actual_hash} != {expected_hash}"
        )

    official = _load_official(source).eval()
    port = OfficialCDCN(theta=0.7).eval()
    print("loaded upstream and local models", flush=True)
    official_state = official.state_dict()
    port_state = port.state_dict()
    remapped = {}
    for key in port_state:
        official_key = key
        for local, upstream in (
            ("block1.", "Block1."),
            ("block2.", "Block2."),
            ("block3.", "Block3."),
        ):
            if key.startswith(local):
                official_key = upstream + key[len(local) :]
                break
        remapped[key] = official_state[official_key]
    port.load_state_dict(remapped, strict=True)
    print(f"matched {len(remapped)} state tensors", flush=True)

    torch.manual_seed(42)
    # CDCN is fully convolutional before its fixed 32x32 fusion. A 64x64
    # equivalence input exercises every layer while avoiding unnecessary peak
    # memory in a separate Colab CPU subprocess.
    sample = torch.randn(1, 3, 64, 64)
    with torch.no_grad():
        official_depth = official(sample)[0][:, None]
        port_depth = port(sample)["depth"]
    max_abs_error = float((official_depth - port_depth).abs().max())
    if not torch.allclose(official_depth, port_depth, atol=1e-6, rtol=1e-5):
        raise SystemExit(f"CDCN port output mismatch: max_abs_error={max_abs_error}")

    print(
        json.dumps(
            {
                "verified": True,
                "git_commit": OFFICIAL_CDCN_PROVENANCE["git_commit"],
                "source_sha256": actual_hash,
                "max_abs_error": max_abs_error,
                "output_shape": list(port_depth.shape),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
