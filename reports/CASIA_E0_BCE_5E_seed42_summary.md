# CASIA E0 BCE 5 epoch result

This report records the first complete engineering baseline. It uses the temporary
CASIA-FASD Kaggle development split, not the final OULU-NPU or Replay-Attack
protocol. The numbers below came from immutable artifacts under the matching Google
Drive run directory and were copied into this repository without images, scores or
checkpoints.

| Field | Value |
|---|---|
| Run ID | `CASIA_E0_BCE_5E_seed42_20260920T082941Z` |
| Config | `configs/casia_e0_bce_5e.yaml` |
| GPU | NVIDIA A100-SXM4-40GB |
| Seed | 42 |
| Epochs | 5 |
| Selection split | Validation |
| Locked threshold | 0.9900876432657242 |

## Validation

| APCER | BPCER | ACER | EER | AUC |
|---:|---:|---:|---:|---:|
| 0.0000 | 0.0000 | 0.0000 | 0.0000 | 1.0000 |

## Test using the locked validation threshold

| APCER | BPCER | ACER | EER | AUC |
|---:|---:|---:|---:|---:|
| 0.0000 | 0.1111 | 0.0556 | 0.0241 | 0.99798 |

- False accepts: 0 of 270 attack videos.
- False rejects: 10 of 90 bona fide videos.
- Highest attack score: 0.9463753312826156.
- Lowest bona fide score: 0.0019060372604144504.
- Separation at the fixed threshold is negative: -0.9444692940222011.

The ranking is strong, but the validation threshold rejects some unseen bona fide
subjects. This test result is frozen. It must not be used to retune E0 or select E1
hyperparameters.
