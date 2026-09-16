# =====================================================================
# process.ps1 — Главная точка входа обработки Vault (dsh <-> Obsidian)
# =====================================================================
# Запуск (PowerShell):
#   powershell -ExecutionPolicy Bypass -File _scripts\process.ps1 -Mode dry
#   powershell -ExecutionPolicy Bypass -File _scripts\process.ps1 -Mode exam -OutDir "03_Экзамены"
#
# Режементы:
#   dry  | exam | plain | links
# =====================================================================

param(
    [ValidateSet("dry", "exam", "plain", "links")]
    [string]$Mode,
    [string]$InputDir = "raw",
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot

function Write-Log {
    param([string]$Msg)
    Write-Host ("[{0}] {1}" -f (Get-Date -Format "HH:mm:ss"), $Msg) -ForegroundColor Cyan
}

function Get-Sha256 {
    param([string]$path)
    $bytes = [System.IO.File]::ReadAllBytes((Resolve-Path $path))
    $sha = [System.Security.Cryptography.SHA256]::Create()
    $hash = $sha.ComputeHash($bytes)
    return ([System.BitConverter]::ToString($hash)).Replace("-", "").ToLower().Substring(0, 12)
}

function New-GuidShort {
    return ([guid]::NewGuid().ToString()).Substring(0, 8)
}

if (-not $Mode) {
    Write-Error "Требуется параметр -Mode: dry|exam|plain|links"
}

# --- Карта: режим -> папка вывода + шаблон ---
$modeMap = @{
    dry   = @{ dir = "02_Знания";      template = "_scripts/templates/dry.md" }
    exam  = @{ dir = "03_Экзамены";     template = "_scripts/templates/exam.md" }
    plain = @{ dir = "02_Знания";      template = "_scripts/templates/plain.md" }
    links = @{ dir = "04_Термины";      template = "_scripts/templates/links.md" }
}

$cfg = $modeMap[$Mode]
$outDir = Join-Path $root $cfg.dir
$template = Join-Path $root $cfg.template

Write-Log "Режим: $Mode"
Write-Log "Вход: $InputDir  |  Выход: $($cfg.dir)"

# --- Входная директория ---
$inPath = Join-Path $root $InputDir
if (-not (Test-Path $inPath)) {
    Write-Warning "Папка '$InputDir' не найдена. Создаю..."
    New-Item -ItemType Directory -Force -Path $inPath | Out-Null
}
$files = Get-ChildItem -Path $inPath -Recurse -Filter *.md -File
if ($files.Count -eq 0) {
    Write-Warning "Нет .md-файлов в '$InputDir'. Положите исходники и повторите."
    exit 0
}

# --- Читаем шаблон ---
if (-not (Test-Path $template)) {
    Write-Error "Шаблон не найден: $template"
}
$tpl = Get-Content -Path $template -Raw -Encoding UTF8

Write-Log "Найдено файлов: $($files.Count)"

$count = 0
foreach ($f in $files) {
    $baseName = [System.IO.Path]::GetFileNameWithoutExtension($f.Name)
    $sha = Get-Sha256 $f.FullName
    $body = Get-Content -Path $f.FullName -Raw -Encoding UTF8

    # --- Упрощённая генерация заголовка из первого # или имени файла ---
    $title = $baseName
    if ($body -match '^\s*#\s+(.+?)\s*$') { $title = $Matches[1] }

    $props = @{
        id             = (New-GuidShort)
        title          = $title
        created        = (Get-Date -Format "yyyy-MM-dd")
        source_file    = $f.Name
        source_path    = ($f.FullName.Substring($root.Length).TrimStart('\'))
        source_sha     = $sha
        subjects       = ""
        key_concepts   = ""
        formulas       = ""
        links          = ""
        questions      = "0"
        question       = ""
        short_answer   = ""
        terms          = ""
        source_basename= $baseName
    }

    $content = $tpl
    foreach ($k in $props.Keys) {
        $content = $content.Replace("{{$k}}", $props[$k])
    }

    $outRel = ($f.FullName.Substring($inPath.Length).TrimStart('\'))
    $subDir = Split-Path -Parent $outRel
    $targetDir = Join-Path $outDir $subDir
    if (-not (Test-Path $targetDir)) { New-Item -ItemType Directory -Force -Path $targetDir | Out-Null }

    $outFile = Join-Path $targetDir ($title + ".md")
    if ((Test-Path $outFile) -and -not $Force) {
        Write-Log "Пропуск (уже есть): $outFile"
        continue
    }

    [System.IO.File]::WriteAllText($outFile, $content, (New-Object System.Text.UTF8Encoding $false))
    Write-Log "Создано: $outFile"
    $count++
}

Write-Log "Готово. Создано/обновлено заметок: $count"
Write-Log "ВНИМАНИЕ: Это каркас генерации по шаблону. Для настоящей НЕЙРОСЕТЕВОЙ фильтрации используйте dsh-prompt-режимы (см. _scripts/prompts/README.md)."
