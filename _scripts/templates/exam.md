---
id: "{{id}}"
title: "{{title}}"
type: "exam"
mode: "exam"
status: "done"
created: "{{created}}"
source:
  path: "{{source_path}}"
  file: "{{source_file}}"
  sha: "{{source_sha}}"
questions: {{questions}}
cheatsheet: true
subjects: [{{subjects}}]
---

# {{title}} — Экзамен

> **Режим:** Экзаменационный. Источник: `[[{{source_basename}}]]`

## Вопросы и точные короткие ответы

### Q1. {{question}}
**A:** {{short_answer}}

### Q2. {{question}}
**A:** {{short_answer}}

<!-- По одному вопросу на каждого пункта исходника. Ответ — 1-3 строки -->

## Шпаргалка

<!-- Компактная выжимка: формулы, определения, ключевые положения на одной раздаче -->

---

*Обработано [[{{source_basename}}|{{source_basename}}]].*