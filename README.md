# DeepFace PAD

Greenfield research project for RGB face presentation attack detection using pseudo-depth supervision.

The implementation follows the research protocol rather than a product-style recognition pipeline.

## Research question

> Can a lightweight classifier learned on a predicted depth map improve CDCN over fixed mean-depth scoring without materially increasing inference cost?

## Documents

- [Research specification](DAC_TA_HE_THONG_NHAN_DIEN_KHUON_MAT_PAD_DEPTH_MAP.md)
- [Two-person alternating report plan](KE_HOACH_THUC_HIEN_THEO_BUOI_HOC.md)
- [Dataset and protocol decision](data/README.md)
- [Colab execution runbook](COLAB.md)
- [Literature matrix for round 1](reports/LITERATURE_MATRIX.md)
- [Frozen CASIA E0 result](reports/CASIA_E0_BCE_5E_seed42_summary.md)
- [Audit of rounds 1-3](reports/MIDTERM_ROUNDS_1_3_AUDIT.md)
- [Midterm handoff and required Colab evidence](reports/MIDTERM_ROUNDS_1_3_HANDOFF.md)

## Mandatory study

| ID | Configuration | Purpose |
|---|---|---|
| E0 | MobileNetV3 with BCE | Lightweight binary baseline |
| E1 | CDCN depth-only with mean-depth scoring | Depth-supervised baseline |
| E2 | CDCN plus frozen learned depth head with BCE | Isolate learned scoring |
| E3 | CDCN MT Lite trained end-to-end with BCE | Test joint optimization |
| E4 | CDCN MT Lite with staged training and Focal Loss | Proposed configuration |

The project uses one public PAD benchmark and one official protocol. Primary metrics are video-level APCER, BPCER, ACER, EER and ROC AUC. It also reports parameter count, model size, latency and FPS.

## Build order

```text
Literature and protocol
    -> dataset manifests and leakage checks
    -> PAD metrics
    -> E0 binary baseline
    -> pseudo-depth generation
    -> E1 CDCN reproduction
    -> E2 to E4 controlled modifications
    -> multiple seeds and paper comparison
    -> error analysis
    -> optional webcam and ArcFace integration
```

## Current status

- [x] Research scope rewritten for a two-person lean study.
- [x] Alternating A/B report schedule defined.
- [x] Recent related work and evaluation rules documented.
- [x] Three-slide core briefing retained as a reference; the final midterm deck is deferred until rounds 1-3 have complete evidence.
- [x] Previous implementation and artifacts removed.
- [x] Temporary midterm dataset and subject-disjoint CASIA development protocol recorded.
- [ ] Final licensed benchmark locked; OULU-NPU and Replay-Attack approval is pending until 27 September 2026.
- [x] Reproducible Python package and experiment configs created.
- [x] Manifest leakage validator and metric tests implemented.
- [x] Resumable pseudo-depth queue, status ledger, QA audit, and failure reporting implemented.
- [x] E0 MobileNetV3 baseline implemented.
- [x] E1 compact CDCN-style depth baseline and resumable 3DDFA V2 worker implemented.
- [x] E1-to-E2 checkpoint transfer and staged-training code covered by unit tests.
- [x] E1 completed a 30-epoch pseudo-depth run, validation threshold selection,
      locked test evaluation, depth-case inspection, and E0-E1 comparison.
- [ ] E2-E4 have completed end-to-end integration runs.
- [ ] Official dataset manifest created and validated.
- [x] Temporary CASIA-FASD debug manifest created and leakage-validated (600 videos,
      12,000 uniformly sampled frames).
- [x] CASIA E0 five-epoch baseline completed and test result frozen.
- [ ] Full E0-E4 runs completed.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
pytest -q
python scripts/validate_manifest.py data/manifests/all.csv --data-root /content/data
python scripts/generate_depth.py data/manifests/all.csv --data-root /content/data --output-root /content/data/depth
python scripts/run_3ddfa_worker.py --pending /content/data/depth/3ddfa_pending.csv --ledger /content/data/depth/depth_status.csv --3ddfa-root /content/3DDFA_V2 --mode gpu
python scripts/visualize_depth_targets.py --ledger /content/data/depth/depth_status.csv --output reports/depth-smoke.png
python scripts/materialize_depth_manifest.py data/manifests/all.csv --ledger /content/data/depth/depth_status.csv --data-root /content/data --output data/manifests/all-with-depth.csv
python scripts/verify_depth_provenance.py --source data/manifests/all.csv --ledger /content/data/depth/depth_status.csv --derived data/manifests/all-with-depth.csv
python scripts/validate_manifest.py data/manifests/all-with-depth.csv --data-root /content/data --require-depth
python scripts/audit_depth.py data/manifests/all-with-depth.csv --data-root /content/data --report reports/depth-qa.json
python scripts/run_experiment.py configs/e0_mobilenet.yaml
# After an E1 run is frozen:
python scripts/visualize_depth_cases.py --run-dir runs/<E1_RUN_ID> --split val --count 10
python scripts/score_checkpoint.py --run-dir runs/<E1_RUN_ID> --split test
```

All configurations use validation data to select the operating threshold. Test scores
must only be evaluated after the configuration is frozen. E2 requires the E1 checkpoint
path in `training.init_checkpoint`; it fails instead of silently training a head on a
random frozen backbone.
Depth-supervised runs also perform manifest preflight before creating a run: every
bona fide sample must reference an existing pseudo-depth target. Empty attack depth
paths remain valid because their protocol target is an all-zero map.
E1, E3, and E4 additionally require `data.source_manifest` and `data.depth_ledger`
in their configs. Training verifies the derived manifest provenance sidecar against
those exact files before creating a run directory, so the byte-level check cannot be
accidentally skipped when starting a paid run. `data.depth_provenance` may point to a
non-default sidecar path when needed. The same preflight then audits every referenced
depth artifact before creating a run directory, so a map changed in place after
materialization cannot bypass validation. Bona fide maps must be readable, finite,
two-dimensional and non-zero, while explicit attack maps must be zero. Each accepted
depth-supervised run stores `depth_input_snapshot.json` with the verified provenance,
full QA result, and SHA-256 plus byte size of every explicit depth target. This makes
the exact pseudo-depth state used at startup auditable even if the shared cache later
changes. Run the
standalone audit before E1 when a JSON report is needed; it records the bona fide
reconstruction failure rate by split and class-level depth statistics.
Pseudo-depth preparation is resumable: `depth_status.csv` records pending, complete,
and failed samples, while `3ddfa_pending.csv` contains only work still requiring
3DDFA V2. Import a worker failure CSV with `--failure-report`; failed bona fide rows
stay failed until `--retry-failed` is explicitly requested and are never replaced by
zero maps.
After the ledger is complete, materialize a separate manifest with verified depth
paths. The command refuses pending or failed rows, invalid artifacts, stale ledger
entries, and outputs outside the configured data root; it never edits the official
source manifest. It also writes `<output>.provenance.json` with SHA-256 checksums for
the exact source manifest, ledger, and derived manifest bytes. Verify that sidecar
after copying or resuming in Colab, then use the derived manifest for the depth audit
and E1/E3/E4 configs.

For Colab Pro setup and the 300-credit budget guardrails, see [COLAB.md](COLAB.md).

## Next deliverables

Rounds 1-3 are technically complete. The clean, output-free Colab notebook is
`notebooks/Face_PAD_Midterm_L1_L2_L3.ipynb`; the executed copy and all biometric
artifacts remain private on Google Drive.

1. Commit the clean notebook and synchronized closeout documents.
2. Write the midterm report and build the deck from the frozen artifacts.
3. Lock OULU-NPU Protocol 1 or Replay-Attack after the 27 September access deadline.
4. Continue with E2-E4 only as new experiments selected on validation.

## Scope limits

The following are postponed until the experiment table is complete:

- Face-recognition UI and enrollment.
- ArcFace integration.
- Web, mobile, API, cloud or database work.
- Complex tracking.
- Transformer, rPPG and temporal-network experiments.
- Cross-dataset evaluation.

Webcam and ArcFace may be added at the end as a small integration demo. They are not the research contribution.

## Data and privacy

- Do not commit raw datasets, extracted biometric frames, pseudo-depth caches or model weights.
- Follow the official dataset license and protocol.
- Pseudo-depth is not sensor depth.
- Zero-depth spoof labels apply to the selected print/replay setting and do not support claims about 3D masks.
- Test data is used only after configuration and threshold selection are frozen.

