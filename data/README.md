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

Fill this table during the first research report.

| Field | Value |
|---|---|
| Decision deadline | |
| Selected dataset | |
| Selected protocol | |
| Access approved by | |
| Dataset root outside Git | |
| Protocol source | |
| Evaluation unit | Video |
| Main metrics | APCER, BPCER, ACER, EER, ROC AUC |

Once selected, the benchmark and protocol remain fixed for E0 through E4.

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

1. Detect and crop the face consistently.
2. Run 3DDFA V2 offline.
3. Render a depth map and face mask.
4. Normalize depth inside the mask to `[0, 1]`.
5. Resize to the CDCN output size.

For print and replay frames, use a zero map according to the selected depth-supervision protocol.

Quality assurance must report:

- 3DDFA failure rate by split.
- Empty, NaN or infinite maps.
- Live and spoof depth statistics.
- Visual alignment of RGB, mask and depth.
- Examples of both successful and failed generation.

## Comparison discipline

External results are copied only after confirming the exact dataset, protocol, split, metric and threshold rule. Results with incompatible settings are labelled contextual rather than direct.

Core references:

- CDCN: <https://openaccess.thecvf.com/content_CVPR_2020/html/Yu_Searching_Central_Difference_Convolutional_Networks_for_Face_Anti-Spoofing_CVPR_2020_paper.html>
- UCDCN: <https://link.springer.com/article/10.1007/s40747-024-01397-0>
- CASO-PAD: <https://www.nature.com/articles/s41598-026-67944-6>

