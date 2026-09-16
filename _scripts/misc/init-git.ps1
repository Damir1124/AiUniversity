# =====================================================================
# _scripts/misc/init-git.ps1 — Разовая инициализация Vault как Git-репозитория
# =====================================================================
# Запуск:
#   powershell -ExecutionPolicy Bypass -File _scripts\misc\init-git.ps1
#
# Делает:
#   1. git init (если ещё нет)
#   2. Проверяет git config user.name/user.email
#   3. Первый коммит
#   4. Инструкцию по подключению GitHub remote
# =====================================================================

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)   # корень (AiUniversity)

Set-Location $root

Write-Host "== Инициализация Git-репозитория Vault ==" -ForegroundColor Cyan

if (-not (Test-Path ".git")) {
    Write-Host "git init..."
    git init -b main
} else {
    Write-Host "Репозиторий уже инициализирован."
}

# --- Проверка identity ---
$name = git config user.name
$email = git config user.email
if (-not $name -or -not $email) {
    Write-Host ""
    Write-Host "Не настроен user.name / user.email." -ForegroundColor Yellow
    $n = Read-Host "Введите ваше имя (для Git)"
    $e = Read-Host "Введите email"
    git config user.name $n
    git config user.email $e
    Write-Host "Настроено: $n <$e>" -ForegroundColor Green
}

# --- Первый коммит ---
Write-Host ""
Write-Host "Первый коммит..."
git add -A
git commit -m "Инициализация Vault AiUniversity" 2>&1 | Out-Host

Write-Host ""
Write-Host "== Готово базово ==" -ForegroundColor Green
Write-Host "Чтобы связать с GitHub, выполните:"
Write-Host "  git remote add origin https://github.com/<вас>/<ваш-репозиторий>.git"
Write-Host "  git push -u origin main"
Write-Host ""
Write-Host "Затем используйте _scripts/misc/sync.ps1 для регулярной синхронизации."
