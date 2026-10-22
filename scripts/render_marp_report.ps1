param([string]$Root = (Split-Path -Parent $PSScriptRoot))
$ErrorActionPreference = 'Stop'
$cli = Join-Path $Root 'artifacts/marp-report-20261016/tooling/node_modules/@marp-team/marp-cli/marp-cli.js'
$folder = Join-Path $Root 'reports/slides_round5'
$markdown = Join-Path $folder 'Bao_cao_DeepFace_PAD.md'
if (!(Test-Path -LiteralPath $cli)) { throw 'Install @marp-team/marp-cli in artifacts/marp-report-20261016/tooling first.' }
New-Item -ItemType Directory -Force -Path (Join-Path $folder 'exports') | Out-Null
& node $cli --allow-local-files $markdown -o (Join-Path $folder 'Bao_cao_DeepFace_PAD.html')
if ($LASTEXITCODE -ne 0) { throw 'HTML export failed.' }
& node $cli --allow-local-files --pdf $markdown -o (Join-Path $folder 'exports/Bao_cao_DeepFace_PAD.pdf')
if ($LASTEXITCODE -ne 0) { throw 'PDF export failed.' }
& node $cli --allow-local-files --pptx $markdown -o (Join-Path $folder 'exports/Bao_cao_DeepFace_PAD.pptx')
if ($LASTEXITCODE -ne 0) { throw 'PPTX export failed.' }
