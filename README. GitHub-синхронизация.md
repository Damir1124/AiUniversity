---
id: "guide-git-001"
title: "README. GitHub-синхронизация"
type: "guide"
status: "done"
created: "2025-01-01"
---

# GitHub-синхронизация Vault

Vault синхронизируется с GitHub, чтобы было резервное копирование и перенос между устройствами.

> ⚠️ Obsidian сам по себе не синхронизирует с GitHub. Ниже — как это делаем скриптами.

---

## 1. Создать репозиторий на GitHub

1. Создайте на [github.com](https://github.com) новый **пустой** репозиторий.
2. Скопируйте URL (HTTPS или SSH), например `https://github.com/<вас>/<репозиторий>.git`.

---

## 2. Разовая инициализация (первый запуск)

В PowerShell в корне проекта (`AiUniversity`):

```powershell
powershell -ExecutionPolicy Bypass -File _scripts\misc\init-git.ps1
```

Скрипт:
- делает `git init`;
- спрашивает `user.name` / `user.email`, если их нет;
- делает первый коммит;
- выведет команды для подключения remote.

Затем подключите remote (например HTTPS):

```powershell
git remote add origin https://github.com/<вас>/<репозиторий>.git
git push -u origin main
```

---

## 3. Регулярная синхронизация

Когда внесли изменения (Obsidian или скриптами обработки):

```powershell
powershell -ExecutionPolicy Bypass -File _scripts\misc\sync.ps1
```

Что делает `sync.ps1`:
1. `git pull origin main` — забрать чужие изменения.
2. `git add -A`.
3. `git commit` — сообщение `Vault sync: <дата>`.
4. `git push origin main`.

Флаги:
- `-NoPull` — не тянуть, только запушить.
- `-NoPush` — закоммитить локально, не пушить.
- `-Branch main` — указать другую ветку.

---

## 4. Авторизация при push

Клоудес HTTPS попросит логин/пароль. Лучше использовать **PAT** (Personal Access Token):
- GitHub → Settings → Developer settings → Personal access tokens → generate;
- scope: `repo`;
- введите как пароль при pushatе.

Или настройте **SSH-ключ** (рекомендуется). После этого `sync.ps1` работает без ввода пароля.

---

## 5. Что исключено (.gitignore)

- `.obsidian/` — локальные настройки Obsidian (тема, плагины) на каждом ПК свои.
- временные `.log`, `.DS_Store`, `Thumbs.db`.
- закомментированные в `.gitignore` папки с большими/бинарными исходниками (`raw/binaries`, `*.dat` и т.п.) — раскомментируйте при необходимости.

---

## 6. Два устройства

- На втором устройстве: `git clone https://github.com/<вас>/<репозиторий>.git`.
- Откройте как Obsidian vault.
- Периодически запускайте `sync.ps1` на обоих устройствах, чтобы не было расхождений.

---

## 7. Конфликты

Если изменений пересекаются, Git предложит разрешить конфликт. В них вручную объединяйте текст (в Obsidian откройте файл, поправьте маркеры `<<<<<<<`/`=======`/`>>>>>>>`) и снова запустите `sync.ps1`.

---

_См. также: [[README]], [[Навигация в Obsidian]]_