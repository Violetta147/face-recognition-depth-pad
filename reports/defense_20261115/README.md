# DUT slide generator

The generator builds an 11-slide Vietnamese review of the Face PAD experiments on CASIA-FASD and OULU-NPU Protocol 1. It uses the DUT backgrounds and figures already available in the repository. The OULU-NPU tables contain aggregate results from completed team runs. The generator does not train a model.

Run from the repository root in PowerShell with the Codex desktop runtime installed.

```powershell
$node = Join-Path $env:USERPROFILE '.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe'
& $node reports/defense_20261115/build_dut_review.mjs
```

Open `outputs/defense_20261115/public-slide-preview/Xem slide DUT.html`. After reviewing the slides, pass a destination ending in `.pptx` as the sole argument to export an editable PowerPoint.

This public version uses placeholder presenter names and summarizes the feedback. The separate classroom submission is kept in the course's submission folder.
