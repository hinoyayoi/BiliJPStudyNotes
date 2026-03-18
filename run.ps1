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

$cmd = @(
  ".\scripts\bilibili_jp_study_pipeline.py",
  $Url,
  "--output-dir", ".\outputs",
  "--model", $Model
)
if ($UseBrowserCookies) { $cmd += "--use-browser-cookies" }

& $python $cmd
