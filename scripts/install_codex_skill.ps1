param()

$RepoRoot = Split-Path $PSScriptRoot -Parent
$Sync = Join-Path $RepoRoot "scripts\sync.py"
python $Sync --tool codex
exit $LASTEXITCODE
