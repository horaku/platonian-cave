# ARCHITECTURE — Doc3 Executor

## Архитектурная цель
Реализовать `phase-governed capability loop` с явными gate-переходами и persistent verification memory.

## Компонентная модель (целевая)
- LangGraph phase nodes (1–7).
- Gate nodes (`PROMOTE|REVISE|REJECT`).
- Capability layer (`state.*`, `search.*`, `source.*`, `extract.*`, `validate.*`, `compare.*`).
- State store для proposal/promoted/verified сущностей.
- Append-only verification ledger.

## Ключевые инварианты
- Нельзя начинать retrieval до promoted SourceDiscoveryPlan.
- Нельзя начинать synthesis до provenance + validation.
- Worker output никогда не authoritative напрямую.
- Противоречия claims сохраняются явно.

## Связь с планированием
- Предразработочный план: `plan.md`.
- Детализированный backlog и тесты: `tasks.md`.
