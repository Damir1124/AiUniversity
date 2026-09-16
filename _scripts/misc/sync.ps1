# =====================================================================
# _scripts/misc/sync.ps1 — Синхронизация Vault с GitHub (pull + push)
# =====================================================================
# Запуск:
#   powershell -ExecutionPolicy Bypass -File _scripts\misc\sync.ps1
#
# Поведение:
#   1. git pull origin <branch>  (забираем изменения)
#   2. git add -A
#   3. git commit (если есть изменения)
#   4. git push origin <branch>
#
# Ветка и remote берутся из _config/dsh_process.yaml -> git:
#   remote: origin, default_branch: main
# =====================================================================

param(
    [string]$Branch = "",   # переопределить ветку
    [switch]$NoPull,         # пропустить pull
    [switch]$NoPush          # только закоммитить локально
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $root

# Попытка прочитать config (ветка/remote)
$branch = $Branch
$remote = "origin"
$cfg = Join-Path $root "_config\dsh_process.yaml"
if (Test-Path $cfg) {
    $y = Get-Content $cfg -Raw
    if ($y -match 'remote:\s*[[''"?]([\w-]+)') { $remote = $Matches[1] }
    if (-not $branch -and $y -match 'default_branch:\s*[[''"?]([\w-]+)') { $branch = $Matches[1] }
}
if (-not $branch) { $branch = "main" }

Write-Host "== Синхронизация: $remote / $branch ==" -ForegroundColor Cyan

# Проверка наличия git
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Error "Git не установлен. Установите Git for Windows."
}
if (-not (Test-Path ".git")) {
    Write-Error "Не репозиторий. Сначала запустите init-git.ps1"
}

if (-not $NoPull) {
    Write-Host "[1/4] git pull..."
    git pull $remote $branch 2>&1 | Out-Host
}

Write-Host "[2/4] git add -A..."
git add -A

$status = git status --porcelain
if (-not $status) {
    Write-Host "Нет изменений — коммитить нечего." -ForegroundColor Yellow
} else {
    $msg = "Vault sync: " + (Get-Date -Format "yyyy-MM-dd HH:mm")
    Write-Host "[3/4] git commit - m '$msg'"
    git commit -m $msg | Out-Host
}

if ($NoPush) {
    Write-Host "Push пропущен (-NoPush)."
} else {
    Write-Host "[4/4] git push..."
    git push $remote $branch 2>&1 | Out-Host
}

Write-Host "== Синхронизация завершена ==" -ForegroundColor Green
