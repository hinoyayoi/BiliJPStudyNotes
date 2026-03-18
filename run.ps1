param(
  [Parameter(Mandatory = $true)]
  [string]$Url,
  [string]$Model = "base",
  [switch]$UseBrowserCookies
)

$python = ".\.venv\Scripts\python.exe"
if (!(Test-Path $python)) {
  Write-Host "[setup] creating venv..."
  py -3 -m venv .venv
  & $python -m pip install -U pip
  & $python -m pip install -r requirements.txt
}

$videoIdMatch = [regex]::Match($Url, "BV[0-9A-Za-z]+")
if ($videoIdMatch.Success) {
  $videoId = $videoIdMatch.Value
} else {
  $videoId = "run_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
}

$outputDir = ".\outputs\$videoId"
New-Item -ItemType Directory -Force -Path $outputDir | Out-Null
Write-Host "[run] output directory: $outputDir"

$cmd = @(
  ".\scripts\bilibili_jp_study_pipeline.py",
  $Url,
  "--output-dir", $outputDir,
  "--model", $Model
)
if ($UseBrowserCookies) { $cmd += "--use-browser-cookies" }

& $python $cmd
