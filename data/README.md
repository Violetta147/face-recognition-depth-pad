# Dataset and protocol decision for the PAD study

The two-person project uses **one mandatory benchmark**. A second dataset is optional and must not delay the primary experiment table.

Raw videos, extracted face frames and pseudo-depth maps are not committed to Git.

## Primary choice

### Option A OULU NPU Protocol 1

Use OULU-NPU Protocol 1 if institutional access is approved by the decision deadline recorded below.

Why it is preferred:

- It provides an official video protocol.
- CDCN and UCDCN report results on OULU-NPU.
- APCER, BPCER and ACER support a paper-style comparison.
- Protocol 1 is narrow enough for a two-person reproduction study.

Access requires the dataset EULA. Do not redistribute the data.

Official page: <https://sites.google.com/site/oulunpudatabase/>

### Option B Replay Attack

Switch to Replay-Attack if OULU-NPU access is not approved by the deadline. Use the official train, development and test protocol; do not create a random frame split.

Why it is a practical fallback:

- It is smaller and suitable for building the experimental pipeline quickly.
- It contains bona fide, print and replay presentations.
- CDCN, UCDCN and recent Face PAD work include this benchmark.

Official page: <https://www.idiap.ch/dataset/replayattack>

## Decision record

The midterm uses CASIA-FASD as an explicitly temporary engineering benchmark while
the licensed datasets are awaiting approval. The final benchmark decision is due one
week after this record; this prevents access approval from blocking E0 and E1.

| Field | Value |
|---|---|
| Decision deadline | 27 September 2026 |
| Selected dataset | CASIA-FASD for the midterm; OULU-NPU preferred for the final study |
| Selected protocol | Project-defined subject-disjoint CASIA development split; not an official comparison protocol |
| Access approved by | CASIA Kaggle copy is available; OULU-NPU and Replay-Attack requests are pending |
| Dataset root outside Git | `/content/datasets/casia-fasd` |
| Protocol source | Kaggle `immada/casia-fasd` plus the certified CASIA video mapping documented below |
| Evaluation unit | Video |
| Main metrics | APCER, BPCER, ACER, EER, ROC AUC |

If OULU-NPU is approved by the deadline, the final E0 through E4 table will use
OULU-NPU Protocol 1. Otherwise the team will use Replay-Attack once its access is
approved. CASIA results remain midterm development evidence and will never be mixed
into the final official-protocol comparison table.

## Temporary engineering dataset

While access approval for OULU-NPU and Replay-Attack is pending, the project may use
the `immada/casia-fasd` Kaggle copy for pipeline development only. It is not the
locked primary benchmark and its scores are not directly comparable with OULU-NPU
Protocol 1.

The downloaded copy contains extracted frames rather than the original videos. Its
folder labels have two known issues that the project parser handles explicitly:

- `HR_1` is high-quality bona fide according to the certified CASIA-FASD mapping,
  although this Kaggle copy places it under `spoof`.
- `bs...` and `fs...` train/live images are precomputed derivatives. They are
  excluded; only original `s...` frames enter the manifest.

Build the fixed debug manifest with 20 uniformly distributed frames per video:

```bash
python scripts/prepare_casia_fasd.py \
  --data-root ../datasets/extracted/casia-fasd \
  --frames-per-video 20
```

The parser restores the certified 20-subject training and 30-subject test identity
numbering, then reserves source training subjects 4, 9, 14, and 19 for a temporary
subject-disjoint validation set. This validation choice is project-defined, not an
official CASIA-FASD protocol, so resulting metrics are development evidence only.
The test split remains untouched and must not be used to tune the pipeline.

## Required manifests

```text
data/
├── README.md
└── manifests/
    ├── train.csv
    ├── val.csv
    └── test.csv
```

Minimum schema:

```csv
sample_id,split,subject_id,video_id,frame_index,image_path,depth_path,label,attack_type
```

Conventions:

- `label = 1` for bona fide.
- `label = 0` for presentation attack.
- Higher model score means more likely bona fide.
- Paths are relative to a configured data root.
- `depth_path` may be empty before pseudo-depth generation.
- Before E1, E3, or E4, run the validator with `--require-depth`; every bona fide
  row must then reference an existing pseudo-depth target. Attack rows may retain an
  empty `depth_path`, which the dataset maps to the protocol-defined zero target.

## Leakage rules

- Follow the official split.
- All frames from one video remain in one split.
- Subjects remain separated when required by the protocol.
- Do not use resized, recompressed or augmented copies of a test video in training.
- Do not tune thresholds, augmentation, epochs or architecture on the test set.
- Record a checksum for each manifest used by an experiment.

The validator must fail on duplicate sample IDs, missing files, invalid labels, video overlap and subject overlap when applicable.

## Frame sampling

- Sample a fixed number of training frames per video, distributed over time.
- Use one fixed validation/test sampling rule for all models.
- Aggregate frame scores into one video score before reporting benchmark metrics.
- Choose mean or median aggregation on validation, then lock it.

## Pseudo depth generation

For bona fide frames:

1. Detect the largest face consistently.
2. Run 3DDFA V2 offline.
3. Render an image-aligned depth map with zero background; the QA mask is derived
   from non-zero rendered pixels.
4. Normalize valid rendered depth to `[0, 1]`.
5. Resize the aligned target to the CDCN output size.

The temporary CASIA development run keeps the same full-frame input convention as
E0 so E0 and E1 differ by supervision/model rather than by an untracked crop change.
The smoke-test contact sheet must confirm that the detected face occupies enough of
the frame and that RGB/depth remain aligned. Before locking the final licensed
benchmark, the group must decide whether its official protocol requires a persistent
face-crop preprocessing stage; if it does, E0 and E1 must both be rerun with that same
crop rule. The derived binary mask is an inspection artifact and is not consumed by
the current loss.

For print and replay frames, use a zero map according to the selected depth-supervision protocol.

Prepare or resume the generation queue before running the external 3DDFA V2 worker:

```bash
python scripts/generate_depth.py data/manifests/all.csv \
  --data-root /content/data \
  --output-root /content/data/depth
```

The command writes `3ddfa_pending.csv` and an atomic `depth_status.csv` ledger. It
reuses valid completed maps and does not overwrite invalid existing outputs. If the
worker reports failures, save `sample_id,error` rows to a CSV and pass it with
`--failure-report`. Failed bona fide samples remain visible and are excluded from the
queue until an intentional `--retry-failed`; they are never converted to zero maps.
Keep the depth output under the configured data root so it can be represented by a
portable relative manifest path. Once every ledger row is complete, create a derived
manifest rather than modifying the official protocol manifest:

```bash
python scripts/materialize_depth_manifest.py data/manifests/all.csv \
  --ledger /content/data/depth/depth_status.csv \
  --data-root /content/data \
  --output data/manifests/all-with-depth.csv
```

The command revalidates every map and fails before writing if the ledger is stale,
has pending or failed rows, or references an artifact outside the data root. Both
bona fide maps and explicit attack zero maps are written as relative `depth_path`
values in the derived manifest. It also writes
`all-with-depth.csv.provenance.json`, recording SHA-256 checksums of the exact source
manifest, ledger, and derived manifest bytes. After any transfer or Colab resume,
verify them before consuming the derived manifest:

```bash
python scripts/verify_depth_provenance.py \
  --source data/manifests/all.csv \
  --ledger /content/data/depth/depth_status.csv \
  --derived data/manifests/all-with-depth.csv
```

The E1, E3, and E4 configs repeat the source manifest and ledger paths. Their
training preflight automatically runs the same byte-level verification before a run
directory is created. Keep those config paths synchronized if the ledger is moved;
use `data.depth_provenance` only when the sidecar is stored at a custom path. The
preflight also re-reads and audits every referenced depth map, so a valid sidecar
cannot hide an artifact that was changed in place after materialization.
After those checks pass, each depth-supervised run persists
`depth_input_snapshot.json` beside its config. The snapshot records the provenance and
QA result plus the SHA-256 and byte size of every explicit depth artifact, without
copying any biometric image or pseudo-depth pixel data into the run directory.

Quality assurance must report:

- 3DDFA failure rate by split.
- Empty, NaN or infinite maps.
- Live and spoof depth statistics.
- Visual alignment of RGB, mask and depth.
- Examples of both successful and failed generation.

Run the standalone machine-checkable audit before E1, E3 or E4 when a persistent
JSON QA report is needed:

```bash
python scripts/audit_depth.py data/manifests/all-with-depth.csv \
  --data-root /content/data \
  --report reports/depth-qa.json
```

The command fails on a missing, unreadable, non-finite or all-zero bona fide map,
and on a non-zero explicit attack map. Empty attack `depth_path` values are counted
as protocol-defined implicit zero targets. The JSON report includes bona fide
failure rates per split plus live and spoof depth statistics. E1, E3, and E4 repeat
the same content checks automatically before allocating a run directory.

## Comparison discipline

External results are copied only after confirming the exact dataset, protocol, split, metric and threshold rule. Results with incompatible settings are labelled contextual rather than direct.

Core references:

- CDCN: <https://openaccess.thecvf.com/content_CVPR_2020/html/Yu_Searching_Central_Difference_Convolutional_Networks_for_Face_Anti-Spoofing_CVPR_2020_paper.html>
- UCDCN: <https://link.springer.com/article/10.1007/s40747-024-01397-0>
- CASO-PAD: <https://www.nature.com/articles/s41598-026-67944-6>

