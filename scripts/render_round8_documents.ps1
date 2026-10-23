param(
    [ValidateSet('report','paper','both')][string]$Kind = 'both',
    [Parameter(Mandatory=$true)][string]$Attempt
)
$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
$package = Join-Path $taskRoot 'reports/round8_documents_20261023'
$qaRoot = Join-Path $taskRoot 'artifacts/round8-documents-20261023'
if ($Attempt -notmatch '^attempt[0-9]{2}$') { throw 'Use a fresh attemptNN name' }
$qaPath = Join-Path $qaRoot $Attempt
if (Test-Path -LiteralPath $qaPath) { throw 'Preserve earlier render attempts' }
New-Item -ItemType Directory -Path $qaPath | Out-Null
$targets = @{
    report = 'Nhom1_Bao_cao_DeepFace_PAD_20261023.docx'
    paper = 'Nhom1_Paper_CDCN_IEEE_VI_20261023.docx'
}
$modes = if ($Kind -eq 'both') { @('report','paper') } else { @($Kind) }
$word = $null
$receipt = [ordered]@{ renderer='Microsoft Word COM hidden and Poppler'; documents=@() }
try {
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = 0
    $word.AutomationSecurity = 3
    foreach ($mode in $modes) {
        $inputPath = Join-Path $package $targets[$mode]
        if (-not (Test-Path -LiteralPath $inputPath -PathType Leaf)) { throw "Missing $inputPath" }
        $doc = $null
        try {
            $doc = $word.Documents.Open($inputPath,$false,$false)
            $doc.Fields.Update() | Out-Null
            foreach ($toc in $doc.TablesOfContents) { $toc.Update() }
            $doc.Repaginate()
            $doc.Fields.Update() | Out-Null
            foreach ($toc in $doc.TablesOfContents) { $toc.Update() }
            $doc.Repaginate()
            $count = $doc.ComputeStatistics(2)
            $pages = [ordered]@{}
            if ($mode -eq 'report') {
                foreach ($name in @('Chuong1','Chuong2','Chuong3','KetLuan','TaiLieu')) {
                    $pages[$name] = $doc.Bookmarks.Item($name).Range.Information(3)
                }
            }
            $doc.Save()
            $pdfPath = Join-Path $qaPath ($mode+'.pdf')
            $doc.ExportAsFixedFormat($pdfPath,17)
            $doc.Close(0)
            [Runtime.InteropServices.Marshal]::ReleaseComObject($doc) | Out-Null
            $doc = $null
            $item = [ordered]@{ kind=$mode; word_pages=$count; starts=$pages; docx_sha256=(Get-FileHash -LiteralPath $inputPath -Algorithm SHA256).Hash.ToLower(); pdf=$pdfPath }
            if ($mode -eq 'report') {
                $item['chapter_pages'] = @(($pages.Chuong2 - $pages.Chuong1),($pages.Chuong3 - $pages.Chuong2),($pages.KetLuan - $pages.Chuong3))
                $item['main_including_conclusion'] = $pages.TaiLieu - $pages.Chuong1
                if ($item.main_including_conclusion -gt 50 -or $item.chapter_pages[0] -gt 15 -or $item.chapter_pages[1] -gt 25 -or $item.chapter_pages[2] -gt 20) { throw 'Report exceeds teacher page limits' }
            }
            $receipt.documents += $item
            $provPath = [IO.Path]::ChangeExtension($inputPath,'.provenance.json')
            $prov = Get-Content -LiteralPath $provPath -Raw | ConvertFrom-Json
            $prov | Add-Member -Force NoteProperty output_sha256 $item.docx_sha256
            $prov | Add-Member -Force NoteProperty render $item
            $prov | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $provPath -Encoding utf8
        }
        finally {
            if ($null -ne $doc) { $doc.Close(0); [Runtime.InteropServices.Marshal]::ReleaseComObject($doc) | Out-Null }
        }
    }
}
finally {
    if ($null -ne $word) { $word.Quit(0); [Runtime.InteropServices.Marshal]::ReleaseComObject($word) | Out-Null }
}
$receipt | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath (Join-Path $qaPath 'render.json') -Encoding utf8
$poppler = (Get-Command pdftoppm.exe -ErrorAction Stop).Source
foreach ($mode in $modes) {
    $pngDir = Join-Path $qaPath $mode
    New-Item -ItemType Directory -Path $pngDir | Out-Null
    & $poppler -r 110 -png (Join-Path $qaPath ($mode+'.pdf')) (Join-Path $pngDir 'page')
    if ($LASTEXITCODE -ne 0) { throw "Poppler failed for $mode" }
}
$receipt | ConvertTo-Json -Depth 20
