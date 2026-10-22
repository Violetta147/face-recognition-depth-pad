param([string]$Root = (Split-Path -Parent $PSScriptRoot))
$ErrorActionPreference = 'Stop'
$source = Join-Path $Root 'artifacts/marp-report-20261016/DUT-backgrounds-only.pptx'
$destination = Join-Path $Root 'reports/slides_round5/assets'
if (!(Test-Path -LiteralPath $source)) { throw 'Run scripts/prepare_marp_report.py first.' }
$ppt = New-Object -ComObject PowerPoint.Application
try {
    $deck = $ppt.Presentations.Open($source, $true, $false, $false)
    $deck.Slides.Item(1).Export((Join-Path $destination 'dut-cover.png'), 'PNG', 1920, 1080)
    $deck.Slides.Item(6).Export((Join-Path $destination 'dut-content.png'), 'PNG', 1920, 1080)
    $deck.Slides.Item(15).Export((Join-Path $destination 'dut-closing.png'), 'PNG', 1920, 1080)
    $deck.Close()
} finally { $ppt.Quit() }
Write-Output "Exported three DUT background variants to $destination"
