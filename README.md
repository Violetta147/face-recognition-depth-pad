# DeepFace PAD

Greenfield research project for RGB face presentation attack detection using pseudo-depth supervision.

The repository has intentionally been reset. Previous detector, ArcFace, enrollment, gallery, scripts, tests, model downloads and local environment have been removed. Implementation will restart from the research protocol instead of from a product-style recognition pipeline.

## Research question

> Can a lightweight classifier learned on a predicted depth map improve CDCN over fixed mean-depth scoring without materially increasing inference cost?

## Documents

- [Research specification](DAC_TA_HE_THONG_NHAN_DIEN_KHUON_MAT_PAD_DEPTH_MAP.md)
- [Two-person alternating report plan](KE_HOACH_THUC_HIEN_THEO_BUOI_HOC.md)
- [Dataset and protocol decision](data/README.md)

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
- [x] Previous implementation and artifacts removed.
- [ ] Dataset and protocol selected.
- [ ] Clean Python environment created.
- [ ] Repository skeleton created from the new specification.
- [ ] E0 implemented.
- [ ] E1 implemented.
- [ ] CDCN MT Lite implemented.

## Immediate deliverables

1. Prepare the three required slides on modern methods, the selected method and evaluation against recent work.
2. Lock OULU-NPU Protocol 1 or switch to Replay-Attack by the decision deadline.
3. Create manifests and leakage validation.
4. Implement metric tests before model training.
5. Build E0 and then reproduce E1.

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

