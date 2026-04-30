# ARCHITECTURE — Doc3 Executor (as-built)

## 1) Назначение
Doc3 Executor реализует `phase-governed capability loop`: каждое решение проходит через фазу + gate и фиксируется в состоянии (`proposals`, `events`, `promoted`) с audit-friendly историей.

## 2) Компоненты (реализованные)

### 2.1 Graph orchestration (`src/doc3_executor/graph`)
- `executor.py` — Phase 1 runner.
- `phase2.py ... phase8.py` — runners фаз 2–8.
- `output_contract.py` — построение и доставка terminal markdown report.

### 2.2 Gates (`src/doc3_executor/gates`)
- `phase1_gate.py ... phase8_gate.py` — инварианты и решения `PROMOTE|REVISE|REJECT`.

### 2.3 Phase logic (`src/doc3_executor/phases`)
- трансформации payload для фаз 1–7 (surface, vocabulary, lexicon, lattice, source-design, triage/extraction, verification memory).

### 2.4 Capabilities (`src/doc3_executor/capabilities`)
- `state_capabilities.py` — read/propose primitives.
- `ledger_interpreter.py` — read-only интерпретация verification ledger для оператора.

### 2.5 State model (`src/doc3_executor/schemas` + `state`)
- `RunState`: `proposals`, `promoted`, `events`.
- `InMemoryStateStore`: propose/promote/event append/read.

## 3) Протокольный data-flow

`user input`  
→ `phase1..phase8` (каждая фаза пишет proposal)  
→ `gate decision event`  
→ `promote only on PROMOTE`  
→ `phase8_finalizer` outcome (`authoritative|limited|blocked`)  
→ `output_contract.build_terminal_report`  
→ optional `deliver_report` (filesystem/stdout/API payload).

## 4) Ключевые runtime-инварианты
- Retrieval запрещён до promoted Phase 5 (`SourceDiscoveryDesign`).
- Synthesis запрещён до evidence/provenance readiness.
- Authoritative finalization запрещён при `unchecked|disputed`.
- `finalization_status` должен соответствовать report-type mapping.
- `terminal_error_return` взаимоисключающ с markdown report веткой.
- Для blocked отчёта обязательна фраза:
  - `No synthesis was produced because finalization is blocked.`
- `ledger_interpreter` read-only и не мутирует `RunState`.

## 5) Тестовые контуры качества
- Фазовые: `tests/test_phase1.py ... tests/test_phase8.py`
- Сквозные: `tests/test_integration.py` (`IT.A ... IT.J`)
- Контракт отчёта: `tests/test_output_contract.py` (`OC.*`)
- Interpreter: `tests/test_ledger_interpreter.py`

## 6) Документы по эксплуатации и эволюции
- `RUNBOOK.md` — операционные процедуры, диагностика, команды запуска.
- `tasks.md` — трекинг реализации/тестов по workstream’ам.
- `plan.md` — исходные контракты и проектные решения.
