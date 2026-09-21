# Official CDCN E1 correction runbook

## Scope

This run reuses the frozen CASIA manifest, 3DDFA V2 pseudo-depth ledger, depth
artifacts, E0 result, evaluator, and threshold policy. It replaces only the E1
model branch.

The previous `CASIA_E1_CDCN_seed42_20260921T024300Z` run is retained as
`E1-Lite Pilot`. It must not be renamed or overwritten on Drive.

## Upstream provenance

- Repository: `https://github.com/ZitongYu/CDCN`
- Commit: `fd8370e8f32bdd090a3552f5a1fe4c301fa99f2b`
- Source: `CVPR2020_paper_codes/models/CDCNs.py`
- Source canonical-LF SHA256: `396b5c093b8f5af9ad1454257b583e75c3b846cc5da1379d84197e68c9828a45`
- License notice: research use only; commercial use is not allowed by the
  upstream repository notice.

The local port preserves the official CDCN layer topology and official
MSE-plus-contrast-MSE loss. It adapts the data, pseudo-depth source, frame
sampling, scoring normalization, artifact layout, and metrics to this project's
CASIA development protocol. It is therefore an architecture reproduction under
our protocol, not a claim to reproduce the paper's published OULU numbers.

The frozen CASIA samples are already face-centric. The 3DDFA worker renders the
mesh back into the original frame coordinate system before downsampling the target,
so RGB and pseudo-depth remain aligned. The correction run intentionally does not
introduce a new crop: doing so would change preprocessing relative to frozen E0.
The existing face-crop contact sheet is QA/demo evidence, not a hidden training
transform.

## New configurations

- Smoke: `configs/casia_e1_cdcn_official_smoke.yaml`
- Full: `configs/casia_e1_cdcn_official.yaml`

Both use input size 256, official `[-1, 1]` normalization, Adam, learning rate
`1e-4`, weight decay `5e-5`, and the official depth loss. The smoke run is one
epoch. The registered full run is 30 epochs. Do not change the full config after
viewing any test output.

## Gates

1. Fresh-clone unit tests pass.
2. `verify_official_cdcn_port.py` reports numerical equivalence to the pinned
   upstream architecture.
3. Existing depth preflight and QA pass; do not regenerate valid pseudo-depth.
4. Smoke loss is finite and predicted depth is not NaN or a constant map.
5. Full-run checkpoint is selected only by validation loss.
6. If validation loss is still materially decreasing at epoch 30, register a
   new validation-only extension before opening test. Never make this decision
   from test results.
7. Freeze config, checkpoint, and validation threshold before scoring test once.

## Required evidence

- `model_provenance.json`
- `depth_input_snapshot.json`
- `train_log.csv`
- `best.ckpt`
- validation frame/video scores and metrics
- at least 12 predicted-depth validation cases
- locked test frame/video scores and metrics
- E0 versus official-E1 comparison
- official E1 error analysis by attack type and quality

## Human actions

The user only needs to provide a Colab GPU runtime and review the two manual
gates. Dataset, depth generation, model integration, configs, provenance, tests,
and scoring scripts are handled by the repository.
