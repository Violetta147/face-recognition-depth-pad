# Colab Pro runbook

The code is Colab-compatible, but GPU jobs are deliberately user-started. An hourly
local automation may improve code and configs; it must not consume Colab credits.

## Setup

In a Colab notebook, select a GPU only when a real experiment is ready, then run:

```bash
!git clone https://github.com/Violetta147/face-recognition-depth-pad.git
%cd face-recognition-depth-pad
!python -m pip install -e .
```

Until the local implementation is pushed manually, upload a zip of this working tree
or mount Drive and use a private working copy. Never put the licensed dataset, face
frames, pseudo-depth cache, or checkpoints in Git.

Mount Drive and keep data and artifacts outside the repository:

```python
from google.colab import drive
drive.mount('/content/drive')
```

Update `data.root`, `data.manifest`, and `runs_dir` in a copied config. Store `runs_dir`
on Drive so a runtime disconnect can be recovered.

## Credit budget

Use the 300 credits in gates:

1. CPU only: validate the manifest and run unit tests.
2. GPU smoke test: one small subset, one seed, one epoch.
3. Screening: E0-E4 with one seed, validation only.
4. Confirmation: E1 and the best modified configuration with three seeds.
5. Test: one final evaluation after choices and threshold rules are frozen.

Do not keep an idle GPU runtime attached. Do not start a full run when the manifest,
pseudo-depth QA, checkpoint resume path, or validation export is missing.

## Commands

```bash
python scripts/validate_manifest.py data/manifests/all.csv --data-root /content/data
python scripts/run_experiment.py configs/e0_mobilenet.yaml
python scripts/generate_depth.py data/manifests/all.csv --data-root /content/data --output-root /content/data/depth
python scripts/materialize_depth_manifest.py data/manifests/all.csv --ledger /content/data/depth/depth_status.csv --data-root /content/data --output data/manifests/all-with-depth.csv
python scripts/verify_depth_provenance.py --source data/manifests/all.csv --ledger /content/data/depth/depth_status.csv --derived data/manifests/all-with-depth.csv
python scripts/validate_manifest.py data/manifests/all-with-depth.csv --data-root /content/data --require-depth
python scripts/audit_depth.py data/manifests/all-with-depth.csv --data-root /content/data --report reports/depth-qa.json
python scripts/run_experiment.py configs/e1_cdcn.yaml
```

Run queue preparation and validation on CPU. The external 3DDFA worker and E1 command
are intentionally manual credit-consuming steps; start them only after inspecting the
pending queue, ledger, and depth QA report. The derived manifest is resumable and is
used by E1, E3, and E4, while the official source manifest remains unchanged. Keep
its `.provenance.json` sidecar and re-run the verification command after a Drive copy
or runtime resume so byte-level changes to the source, ledger, or derived manifest
are caught before training. The E1, E3, and E4 config files also declare the source
manifest and ledger; `run_experiment.py` repeats this verification automatically and
fails before creating a run directory if either file or the derived manifest changed.
It then audits the current depth files themselves and also fails closed if a bona
fide map is unreadable, non-finite, or empty, or if an explicit attack map is non-zero.
Keep the standalone audit command in the workflow because its JSON output is the QA
artifact used to report reconstruction failures and depth statistics.

Before E2, copy the successful E1 checkpoint path into
`configs/e2_head_frozen.yaml`. Each run writes an immutable config copy, environment,
manifest checksum, training log, checkpoint, raw validation scores, locked threshold,
and metrics under `runs/`. E1, E3, and E4 also write `depth_input_snapshot.json`,
containing the verified materialization provenance, QA report, and checksum of every
explicit depth map as it existed when preflight passed. Keep this small JSON file with
the run when copying artifacts from Colab; it does not contain image or depth pixels.
