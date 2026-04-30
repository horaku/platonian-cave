# Doc3 Executor

`Doc3 Executor` — прототип протокольно-управляемого research workflow (Phase 1→8) с gate-решениями, verification memory и markdown output contract.

## Что уже реализовано
- Фазы `1..8` (intent → vocabulary → lexicon → hypotheses → source design → triage/extraction → verification memory → finalizer).
- Gate-валидации для каждой фазы (`PROMOTE|REVISE|REJECT`).
- Read-only `ledger_interpreter` для операторской диагностики.
- Output contract:
  - `report_markdown`
  - `report_filename`
  - `report_type`
  - `report_envelope`
  - `terminal_error_return` ветка
- Интеграционные и контрактные тесты (`F*`, `IT*`, `OC*`).

## Быстрый старт

### 1) Прогон всех тестов
```bash
pytest -q
```

### 2) Запуск только сквозных интеграционных тестов
```bash
pytest -q tests/test_integration.py
```

### 3) Проверка output contract
```bash
pytest -q tests/test_output_contract.py
```

## Минимальный runtime flow (без CLI)

1. Создать `RunState`.
2. Последовательно вызвать `run_phase1` … `run_phase8`.
3. Построить отчёт:
   - `build_terminal_report(run_state)`
4. При необходимости записать artifact:
   - `deliver_report(..., write_to_file=True)`

Подробный операционный порядок, команды и сценарии диагностики — в `RUNBOOK.md`.

## Как читать репозиторий
- `ARCHITECTURE.md` — as-built архитектура, инварианты и data-flow.
- `RUNBOOK.md` — эксплуатация, диагностика, сценарии и проверочные команды.
- `tasks.md` — трекинг задач/тестов по workstream’ам.
- `plan.md` — эволюция протокола и проектные контракты.

## Test Execution Lifecycle (Dev/CI vs Runtime)

| Контур | Когда запускается | Что запускается | Блокирует релиз |
|---|---|---|---|
| Runtime execution | При обычном использовании workflow | Только Phase/Gate loop + finalizer/output | Нет |
| Dev quick checks | При локальной разработке | Таргетные фазовые/контрактные тесты | Да (для PR) |
| Pre-merge / CI | Перед merge/release | `F*` + `IT*` + `OC*` | Да |

Практическое правило:
- runtime-код не должен автоматически запускать test-suite;
- test-suite — это quality gate для изменений протокола.
