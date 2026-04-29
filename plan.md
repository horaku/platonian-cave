# Doc3 Executor на базе LangGraph — план перед разработкой

## Цель
Подготовить строгую спецификацию исполнения (Executor Spec), чтобы реализация в LangGraph была **phase-governed capability loop**, а не скрытой factory-пайплайновой автоматизацией.

## Порядок действий

1. Зафиксировать `Doc3 Executor Spec v0` (без кода):
   - phase contracts (7 фаз);
   - gate rules;
   - lifecycle записей (proposal → validated → gate-reviewed → promoted → verified);
   - invariants и контрольные запреты;
   - criteria готовности к synthesis.

2. Описать модель состояния и типы записей:
   - `RunState`;
   - `ProblemSurfaceRecord`;
   - `VocabularyCandidateSet`;
   - `WorkingLexicon`;
   - `HypothesisLattice`;
   - `SourceDiscoveryPlan`;
   - `TriageRecord`/`ExtractionRecord`;
   - `VerificationLedger` + `DecisionEvent`.

3. Спроектировать gates как отдельные узлы графа:
   - каждый gate возвращает только `PROMOTE | REVISE | REJECT`;
   - каждый gate обязан писать событие решения в ledger.

4. Зафиксировать capability API (минимум для MVP):
   - `state.read`, `state.propose`, `state.promote`;
   - `search.run`;
   - `source.fetch`, `source.enrich`;
   - `extract.claims`;
   - `validate.claim`;
   - `compare.contradictions`.

5. Спроектировать LangGraph как управляемый цикл, а не линейный pipeline:
   - `phase -> gate -> next/revise/reopen`;
   - переоткрытие ранних фаз при выявлении пробелов на поздних;
   - append-only decision history;
   - downstream invalidation при изменении promoted-записей.

6. Внедрить persistent verification memory:
   - все claims с provenance (source + locator + extraction_id);
   - validation status (factual/citation/semantic);
   - фиксировать contradictions, не сглаживать их в prose.

7. Определить authority boundaries:
   - worker/agent outputs — только proposal;
   - authoritative state формируется только через gate/promotion;
   - human/validator роли и правила override.

8. Подготовить acceptance tests уровня протокола (до полноценного retrieval):
   - A: zero-knowledge input;
   - B: запрет retrieval до promoted SourceDiscoveryPlan;
   - C: разделение source groups и их epistemic roles;
   - D: сохранение противоречий;
   - E: отказ synthesis без provenance/validation;
   - F: контроль leakage (PICO/UI/backend).

9. Этапы реализации:
   - v0: фазы 1–5 + gates + structured state, без автономного retrieval по умолчанию;
   - v1: retrieval + triage + extraction;
   - v2: validation + contradiction tracking + synthesis-readiness.

## Определение готовности к старту разработки
Разработка начинается только после того, как:
- утверждены схемы записей и transition logic;
- определены gate-политики и роль человека;
- пройдены protocol-tests на state machine;
- зафиксированы invariants и leakage guards как обязательные проверки.
