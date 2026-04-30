# Doc3 Executor на базе LangGraph — план перед разработкой

## Итерация 1: Protocol-driven state machine

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

## Расширение спецификации (без имплементации): Ledger Interpreter + Phase 8 Finalizer

Ниже добавляются две сущности протокола. Это только design-уровень для `Doc3 Executor Spec`, без изменения текущей реализации.

### 1) `ledger_interpreter` (надстройка над verification memory)

**Purpose:** рендер `VerificationLedger` в человеко-читаемые представления для оператора/валидатора.

#### Принципы проектирования в текущей архитектуре
- Источник истины: только `run_state.promoted["phase7_verification_memory"]`.
- Interpreter — read-only capability-поверхность (аналог `state.read`), не часть gate-chain.
- Выход interpreter — производные view-модели (snapshots), не authoritative state.
- Любая метка “готово/неготово” должна вычисляться из ledger-данных, а не задаваться вручную.

#### Предлагаемый контракт данных
- `LedgerInterpretationView`:
  - `run_id`
  - `claims_by_status`:
    - `proposed[]`
    - `accepted[]`
    - `rejected[]`
    - `needs_review[]`
    - `verified[]`
  - `source_link_index[]` (claim_id -> source links)
  - `open_contradictions[]` (только неразрешённые конфликты)
  - `synthesis_readiness`:
    - `authoritative_ready: bool`
    - `blocking_reasons: [string]`
  - `next_actions[]` (рекомендации оператору по закрытию блокеров)

#### Allowed / Forbidden поведение
- `may`:
  - группировать claims по статусам;
  - показывать accepted/rejected/needs_review/verified;
  - показывать source links;
  - показывать unresolved contradictions;
  - показывать synthesis readiness;
  - предлагать next actions.
- `must_not`:
  - promote claims;
  - mark claims verified;
  - скрывать contradictions;
  - превращать `unchecked` в выводы;
  - выпускать authoritative synthesis.

#### Интеграция в проект
- Размещать как отдельную capability/adapter-плоскость, не как phase.
- Использовать в `RUNBOOK` и операторских сценариях диагностики.
- Добавить acceptance checks:
  - interpreter не мутирует `run_state`;
  - contradictions всегда видимы в view;
  - readiness=false при любом `unchecked`/`disputed`.

---

### 2) `phase_8_finalizer` (новая терминальная фаза протокола)

**Purpose:** формировать терминальный результат workflow после Phase 7 и после завершения необходимых проверок.

#### Почему это отдельная фаза
Текущая Phase 7 проектно отвечает за построение verification memory и traceability, а не за финальную авторитетную выдачу. Поэтому финализация должна быть отдельным протокольным шагом с собственным gate.

#### Предусловия запуска Phase 8
- Есть promoted `phase7_verification_memory`.
- Выполнены минимальные проверки finalization-policy:
  - все обязательные claim validation поля не `unchecked` для authoritative режима;
  - contradictions либо разрешены, либо явно отражены в результате как открытые.

#### Вход / выход
- **Input:** promoted ledger Phase 7 + decision history + contradiction records.
- **Output:** `FinalizationRecord` одного из типов:
  - `authoritative_synthesis`
  - `limited_synthesis`
  - `blocked_finalization_report`

#### Gate логика Phase 8 (концепт)
- `PROMOTE authoritative_synthesis`, если:
  - нет `unchecked` по критичным claims;
  - provenance полный;
  - нет “тихо сглаженных” contradictions.
- `PROMOTE limited_synthesis`, если:
  - есть частично валидированный корпус,
  - ограничения/риски явно раскрыты,
  - выводы ограничены validated подмножеством.
- `REJECT/REVISE -> blocked_finalization_report`, если:
  - остаются критические блокеры (unchecked/disputed без adjudication, отсутствующий provenance, нарушения authority boundary).

#### Allowed / Forbidden поведение
- `may`:
  - валидировать claims (через capability-события);
  - сравнивать contradictions;
  - продвигать/отклонять claims только через gate;
  - эмитить authoritative или limited synthesis;
  - эмитить blocked finalization report.
- `must_not`:
  - молча игнорировать `unchecked`;
  - переписывать историю ledger (append-only);
  - схлопывать contradictions в нейтральную прозу;
  - делать worker-output финальной authority без gate.

#### Интеграция в state machine
- Phase order становится: `1..7 -> 8(finalizer)`.
- Phase 8 читает только promoted records (как и другие фазы).
- Phase 8 пишет proposal + decision event + conditional promote.
- Вводится `finalization_status` в promoted-state (terminal marker):
  - `authoritative`
  - `limited`
  - `blocked`

#### Новые acceptance tests (design-level)
- `F8.Authoritative.Readiness`: authoritative невозможен при `unchecked`.
- `F8.Limited.AllowedWithDisclosure`: limited допустим только с явным disclosure ограничений.
- `F8.Blocked.Report`: при блокерах формируется blocked report с actionable next steps.
- `F8.Contradiction.Preservation`: contradictions не теряются и не маскируются.
- `F8.AuthorityBoundary`: worker не может финализировать без gate decision.

---

## Output contract: как пользователь получает отчёт (Markdown)

Независимо от внутреннего состояния `RunState`, наружу executor возвращает **только один** терминальный markdown-отчёт по схеме ниже.

### 1) Типы терминального отчёта
- `authoritative_synthesis_report.md`
- `limited_synthesis_report.md`
- `blocked_finalization_report.md`

### 2) Единый envelope (metadata + sections)

```yaml
report_envelope:
  report_type: authoritative | limited | blocked
  run_id: string
  generated_at_utc: string
  protocol_version: string
  finalization_status: authoritative | limited | blocked
  based_on:
    promoted_records:
      - phase1_intent_surface
      - phase2_vocabulary_bootstrap
      - phase3_terminology_normalization
      - phase4_hypothesis_lattice
      - phase5_source_discovery_design
      - phase6_triage_and_extraction
      - phase7_verification_memory
      - phase8_finalizer
    decision_event_ids: [string]
```

Правило supersede для аудита:
- `phase2_vocabulary_bootstrap` может быть опущен из `promoted_records` **только если**
  1) он полностью superseded `phase3_terminology_normalization`,
  2) все решения Phase 2 доступны в `decision_event_ids` / history,
  3) отчёт содержит явную пометку `phase2_superseded_by_phase3: true`.

### 3) Markdown-структура (обязательные разделы)

```md
---
report_type: authoritative | limited | blocked
run_id: <string>
generated_at_utc: <string>
protocol_version: <string>
finalization_status: authoritative | limited | blocked
based_on:
  promoted_records: [...]
  decision_event_ids: [...]
---
```

YAML front matter обязателен: он должен содержать тот же `report_envelope`, который возвращается executor-ом.

```md
# Doc3 Executor Report

## 1. Report Metadata
- Report type: {authoritative|limited|blocked}
- Run ID: {run_id}
- Generated at (UTC): {timestamp}
- Protocol version: {version}
- Finalization status: {authoritative|limited|blocked}

## 2. Executive Outcome
- Краткий итог (2–6 пунктов, без потери квалификаторов уверенности)
- Scope и границы применимости

## 3. Claim Status Summary
- Proposed: N
- Accepted: N
- Rejected: N
- Needs review: N
- Verified: N

## 4. Evidence Backbone (Provenance)
Для каждого ключевого утверждения:
- Claim ID
- Claim text
- Status
- Source links (source_id, extraction_id, locator)
- Validation status (factual/citation/semantic)

## 5. Contradictions and Tensions
- Список конфликтов (claim_id ↔ claim_id)
- Статус конфликта: open | resolved
- Комментарий/основание adjudication (если resolved)

## 6. Synthesis
### 6.1 Main synthesis
- Только выводы, разрешённые policy для данного report_type
### 6.2 Limitations
- Явный список ограничений корпуса и валидации

## 7. Readiness and Gate Decision
- Authoritative readiness: true|false
- Blocking reasons (если есть)
- Последнее gate-решение и reason

## 8. Next Actions
- Конкретные шаги для продвижения к authoritative состоянию
```

### 4) Правила наполнения по типам отчёта
- **authoritative**:
  - раздел `Synthesis` может включать окончательные выводы;
  - `Validation status` по критичным claims не содержит `unchecked`.
- **limited**:
  - синтез ограничен validated-подмножеством;
  - обязательно раздел `Limitations` с явным disclosure.
- **blocked**:
  - финальные выводы не формируются;
  - основной акцент на `Blocking reasons` + `Next Actions`.
  - секция `## 6.1 Main synthesis` MUST содержать явную фразу:
    - `No synthesis was produced because finalization is blocked.`

### 5) Жёсткие запреты output contract
- Нельзя скрывать contradictions или удалять их из отчёта.
- Нельзя выводить authoritative формулировки при `unchecked` в обязательных полях.
- Нельзя ссылаться на claims без provenance (`source_id/extraction_id/locator`).
- Нельзя переписывать историю решений; отчёт всегда трассируется к `DecisionEvent`.
- Если YAML front matter и возвращаемый `report_envelope` расходятся, run считается `invalid` и MUST NOT трактоваться как completed.

### 6) Delivery contract

Executor MUST return:
- `report_markdown: string`
- `report_filename: authoritative_synthesis_report.md | limited_synthesis_report.md | blocked_finalization_report.md`
- `report_type: authoritative | limited | blocked`
- `report_envelope: ReportEnvelope`

For unrecoverable finalization failures, executor MUST return:
- `terminal_error_return`:
  - `error_type: terminal_error`
  - `run_id: string | null`
  - `reason: string`
  - `diagnostic_event_id: string | null`
  - `safe_to_retry: boolean`

If filesystem output is enabled, executor MUST also write the same content to:
- `runs/{run_id}/reports/{report_filename}`

Допустимые способы доставки:
- API/SDK: возврат `report_markdown` + metadata;
- CLI: печать markdown в `stdout` и/или запись в artifact path (в зависимости от флагов запуска).

### 7) Invariant: ровно один терминальный отчёт

- Executor MUST emit exactly one terminal markdown report per completed run.
- Executor MUST NOT emit multiple terminal reports for the same finalization event.
- `terminal_error_return` взаимоисключающ с markdown-отчётом (либо report, либо terminal_error).

### 8) Mapping результата Phase 8 к типу отчёта

```yaml
report_type_mapping:
  authoritative_synthesis: authoritative_synthesis_report.md
  limited_synthesis: limited_synthesis_report.md
  blocked_finalization_report: blocked_finalization_report.md
```

`finalization_status` и `report_filename` обязаны быть согласованы с этим mapping.

### 9) Политика при protocol error

- Protocol violations during finalization MUST produce `blocked_finalization_report.md`,
  unless run state cannot be safely reconstructed.
- Если безопасная реконструкция невозможна, система обязана:
  1) вернуть machine-readable error envelope,
  2) записать диагностический event в history,
  3) пометить run как `terminal_error` (без ложной synthesis-выдачи).

### 10) Output contract tests (обязательные)

- `OC.ExactlyOneReport`:
  - для completed run эмитится ровно один terminal markdown report.
- `OC.ReportEnvelopePresent`:
  - в ответе присутствуют все поля `report_envelope` (или `terminal_error_return` для terminal_error ветки).
- `OC.MarkdownEnvelopeConsistency`:
  - markdown metadata согласован с envelope (`run_id`, `report_type`, `finalization_status`, timestamps).
  - любое расхождение переводит run в `invalid` (не completed).
- `OC.Phase8MappingConsistency`:
  - outcome Phase 8 строго соответствует `report_filename` по `report_type_mapping`.
- `OC.BlockedReportNoSynthesis`:
  - blocked report не содержит authoritative/limited synthesis секций как финальных утверждений;
  - `## 6.1 Main synthesis` явно содержит фразу про blocked finalization.
- `OC.ProtocolErrorNoFalseReport`:
  - при unrecoverable protocol error возвращается только `terminal_error_return`, без ложного markdown report.

---

## Итерация 2: Agentic deep-research workflow

## Цель
Перейти от protocol-driven state machine к **capability-based agentic execution under protocol gates**, где агент:
- выбирает действия на основе gaps/contradictions;
- использует инструменты как расширение мышления, а не скрытый pipeline;
- стабильно доводит run до terminal результата (`authoritative|limited|blocked`) без ручного редактирования кода запуска.

## Порядок действий

1. Зафиксировать agentic runtime contract (без кода):
   - что считается agent step;
   - какие capability-вызовы разрешены по фазам;
   - какие действия требуют human approval;
   - как фиксируется rationale выбора следующего шага.

2. Расширить capability layer до рабочего deep-research surface:
   - `search.run` (query families, source group routing);
   - `source.fetch`, `source.enrich` (metadata/provenance);
   - `extract.claims` (schema-bound extraction proposals);
   - `validate.claim` (factual/citation/semantic checks);
   - `compare.contradictions` (conflict graph updates).

3. Встроить deliberation loop в runner:
   - `PROMOTE` -> next phase;
   - `REVISE` -> recovery strategy (retry/reopen/ask-human);
   - `REJECT` -> controlled stop + blocked/error branch;
   - bounded attempts + deterministic escalation policy.

4. Реализовать explicit recovery policies:
   - revise-classification (input ambiguity / term mismatch / evidence insufficiency / gate policy violation);
   - strategy mapping для каждого класса;
   - audit trail для каждого recovery шага.

5. Добавить human-in-the-loop checkpoints:
   - approve/reject critical transitions;
   - explicit override records;
   - прозрачное разделение agent recommendation vs human decision.

6. Усилить synthesis engine:
   - формировать содержательный synthesis из validated subset;
   - обязательно рендерить limitations, contradictions, unresolved items;
   - запрещать “neutral smoothing” конфликтов.

7. Довести output contract до пользовательского качества:
   - report sections заполняются из run state, а не шаблонными строками;
   - для каждого report type фиксируются обязательные content thresholds;
   - `terminal_error_return` остаётся machine-readable fallback.

8. Добавить e2e productization контур:
   - CLI/runner Windows-friendly;
   - стабильный artifact path;
   - reproducible runs + replay from ledger.

## Технологический стек и стратегия сшивания (итерация 2)

Целевой стек:
- **LangGraph** — orchestration/state transitions;
- **OpenAI SDK** — LLM/tool execution;
- **LangSmith** — tracing/observability.

Принцип разделения ответственности:
- LangGraph не выполняет бизнес-логику инструментов, а управляет phase/gate flow.
- OpenAI SDK не управляет фазами, а исполняет capability-вызовы внутри phase/tool nodes.
- LangSmith не влияет на решения раннера, а фиксирует telemetry/debug traces.

Контрактные швы между слоями:
1. `GraphState` (единая модель состояния run-а для graph nodes и gates).
2. `CapabilityRequest/CapabilityResponse` (единый envelope для всех tool-вызовов).
3. `TraceAdapter` (стандартизированный экспорт событий в LangSmith).

Безопасная стратегия внедрения (без big-bang):
1. Ввести tracing hooks и capability envelopes без смены default runner.
2. Перенести в LangGraph сначала ограниченный контур (Phase 1–3), сохранить legacy fallback.
3. Расширить перенос на Phase 4–8 после parity-тестов между legacy и graph путями.
4. Переключить default engine только после стабильного прохождения `F*`, `IT*`, `OC*`, `A2.*` тестов.

Ограничение на миграцию:
- Никаких массовых рефакторов “за один PR”.
- Один change-set = одна целевая гипотеза + проверка тестами + rollback-safe поведение.

## Acceptance tests (итерация 2)
- **A2.Tool-Use.Traceability**: каждый capability-вызов имеет rationale, provenance и decision linkage.
- **A2.Revise.Recovery**: revise не приводит к silent stop; runner завершает run через recovery или blocked branch.
- **A2.Contradiction.Adjudication**: contradictions сохраняются и явно отражаются в synthesis/output.
- **A2.HITL.Override.Audit**: человеческие overrides записываются как first-class decision events.
- **A2.Synthesis.Quality.MinBar**: отчет содержит содержательные разделы evidence/limitations/next actions без template-only output.
- **A2.Windows.CLI.E2E**: запуск через CLI на Windows даёт terminal payload и artifact без ручных workaround.

## Этапы реализации
- v3: capability execution + deliberation loop (без полноценного retrieval breadth).
- v4: full research capabilities + contradiction adjudication + HITL checkpoints.
- v5: production-grade reporting quality + observability + reliability hardening.

## Определение готовности к завершению итерации 2
Итерация 2 считается завершённой, когда:
- агент принимает последовательность действий через capabilities, а не через жёсткий hidden pipeline;
- revise/reject path управляемо завершаются без ручного редактирования исходников;
- synthesis опирается на validated evidence core и сохраняет contradictions;
- CLI/runner обеспечивает предсказуемый terminal output для пользовательских сценариев;
- e2e acceptance tests итерации 2 проходят стабильно.
