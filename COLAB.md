# Colab Pro runbook

The code is Colab-compatible, but GPU jobs are deliberately user-started. An hourly
local automation may improve code and configs; it must not consume Colab credits.

## Setup

In a Colab notebook, select a GPU only when a real experiment is ready, then run:

```bash
!git clone https://github.com/Violetta147/face-recognition-depth-pad.git
%cd face-recognition-depth-pad
%pip install -e ".[dev]"
```

Restart the runtime only if Colab requests it, then verify that the notebook kernel
sees the editable package:

```python
import deepface_pad
print(deepface_pad.__file__)
```

Never put the licensed dataset, face frames, pseudo-depth cache, or checkpoints in Git.

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

## Consolidated CASIA midterm run

These commands finish the remaining Lượt 1 to Lượt 3 artifacts. Run them from
`/content/face-recognition-depth-pad` after the Kaggle data exists at
`/content/datasets/casia-fasd`.

```bash
python scripts/prepare_casia_fasd.py \
  --data-root /content/datasets/casia-fasd \
  --output-dir data/manifests \
  --frames-per-video 20

python scripts/visualize_manifest_batch.py \
  data/manifests/casia_fasd_debug.csv \
  --data-root /content/datasets/casia-fasd \
  --split val \
  --output /content/drive/MyDrive/face-pad/reports/casia-val-batch.png

python scripts/generate_depth.py \
  data/manifests/casia_fasd_debug.csv \
  --data-root /content/datasets/casia-fasd \
  --output-root /content/datasets/casia-fasd/depth
```

Install the official MIT-licensed 3DDFA V2 implementation and build its extensions:

```bash
cd /content
git clone https://github.com/cleardusk/3DDFA_V2.git
cd /content/3DDFA_V2
git checkout 1b6c67601abffc1e9f248b291708aef0e43b55ae
python -m pip install -r requirements.txt
sh ./build.sh
git rev-parse HEAD
cd /content/face-recognition-depth-pad
```

The worker writes `depth_status.csv.worker.json` with this exact commit, config hash,
backend, mode and output size. A resumed queue refuses a different worker definition,
and materialization includes this metadata checksum in the provenance sidecar.

First process only 50 bona fide frames. The ledger is saved after every sample:

```bash
python scripts/run_3ddfa_worker.py \
  --pending /content/datasets/casia-fasd/depth/3ddfa_pending.csv \
  --ledger /content/datasets/casia-fasd/depth/depth_status.csv \
  --3ddfa-root /content/3DDFA_V2 \
  --mode gpu \
  --limit 50 \
  --failure-report /content/datasets/casia-fasd/depth/3ddfa_failures.csv

python scripts/visualize_depth_targets.py \
  --ledger /content/datasets/casia-fasd/depth/depth_status.csv \
  --count 12 \
  --output /content/drive/MyDrive/face-pad/reports/casia-depth-smoke.png
```

Inspect `casia-depth-smoke.png`. The live face region must have non-zero structure;
attack targets must be zero; RGB and target must remain spatially consistent. If the
gate passes, rerun the worker command without `--limit`. A failed row remains failed
and is never replaced by a zero target. After reviewing failures, explicitly retry
them with:

```bash
python scripts/generate_depth.py \
  data/manifests/casia_fasd_debug.csv \
  --data-root /content/datasets/casia-fasd \
  --output-root /content/datasets/casia-fasd/depth \
  --retry-failed
```

Then rerun the worker and finish materialization, provenance and QA:

```bash
python scripts/materialize_depth_manifest.py \
  data/manifests/casia_fasd_debug.csv \
  --ledger /content/datasets/casia-fasd/depth/depth_status.csv \
  --data-root /content/datasets/casia-fasd \
  --output data/manifests/casia_fasd_debug_with_depth.csv

python scripts/validate_manifest.py \
  data/manifests/casia_fasd_debug_with_depth.csv \
  --data-root /content/datasets/casia-fasd \
  --require-depth

python scripts/audit_depth.py \
  data/manifests/casia_fasd_debug_with_depth.csv \
  --data-root /content/datasets/casia-fasd \
  --report /content/drive/MyDrive/face-pad/reports/casia-depth-qa.json

E1_SMOKE_RUN=$(python scripts/run_experiment.py configs/casia_e1_smoke.yaml)
echo "E1 smoke: $E1_SMOKE_RUN"

E1_RUN=$(python scripts/run_experiment.py configs/casia_e1_cdcn.yaml)
echo "E1 full: $E1_RUN"

python scripts/visualize_depth_cases.py \
  --run-dir "$E1_RUN" \
  --split val \
  --count 10 \
  --output-dir /content/drive/MyDrive/face-pad/reports/e1-depth-cases

python scripts/score_checkpoint.py \
  --run-dir "$E1_RUN" \
  --split test
```

Do not run E1 full training until the depth audit reports `valid: true`. Do not open
the CASIA test split again for E1 before the E1 configuration and validation
threshold are frozen.

The final two commands reuse the validation-derived threshold. They export at least
ten auditable RGB/target/mask/prediction cases and then create frozen test frame
scores, video scores and metrics inside the E1 run directory. If no validation
mistakes exist, the case exporter fills the set with the closest correct cases and
reports zero errors instead of inventing failure examples.

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
