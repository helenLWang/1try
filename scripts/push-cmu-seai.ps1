# Force-push this clone's HEAD to the private CMU I2 course repo (main).
# Run from Documents\i2-submit:  powershell -File scripts\push-cmu-seai.ps1
# Log in as lew2-wq if Git asks. This file contains no secrets.
$ErrorActionPreference = 'Stop'
if ($PSScriptRoot) { Set-Location -LiteralPath (Join-Path $PSScriptRoot '..') }

$remote = 'https://github.com/cmu-seai/f26-model-lew2.git'
$sha = git rev-parse HEAD
if ($LASTEXITCODE -ne 0) {
    Write-Host 'FAILED: not a git repo. cd to Documents\i2-submit first.'
    exit 1
}

Write-Host "cwd  = $(Get-Location)"
Write-Host "HEAD = $sha"
Write-Host "Force-pushing HEAD to $remote main ..."
git push --force $remote HEAD:main
if ($LASTEXITCODE -eq 0) {
    Write-Host "SUCCESS: course repo main now matches $sha"
    Write-Host "Canvas: https://github.com/cmu-seai/f26-model-lew2/commit/$sha"
    exit 0
}

Write-Host "FAILED (exit $LASTEXITCODE). Sign in as lew2-wq (not helenLWang), then retry."
Write-Host 'Stuck credentials: git credential-manager github logout'
exit $LASTEXITCODE
