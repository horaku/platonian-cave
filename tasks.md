# Doc3 Executor — задачи разработки и комплексные тесты фаз

## Принципы тестирования

1. Тесты **не имитируют** работу фаз: каждая фаза выполняется реальными узлами/гейтами LangGraph и реальными capability-вызовами test harness.
2. Каждый фазовый тест проверяет:
   - корректность фазы;
   - соблюдение gate-инвариантов;
   - совместимость с **полным promoted-state всех предыдущих фаз**.
3. Тестовый прогон обязан фиксировать артефакты:
   - входной `RunState`;
   - предложения (`proposal records`);
   - gate-решения (`DecisionEvent`);
   - итоговый `promoted state`;
   - отчёт о нарушениях/инвалидациях.
4. Любой тест считается пройденным только при schema-validation, protocol-validation и cross-phase compatibility validation.

---

## Workstream 0 — Базовый каркас репозитория

### Задачи
- [x] Создать каркас проекта (пакеты, модули, папки для schemas/graph/capabilities/gates/tests).
- [x] Внедрить единый формат record IDs, run IDs, trace IDs.
- [x] Подключить schema validation и contract validation.
- [ ] Настроить CI для запуска всех протокольных и интеграционных тестов.

### Артефакты
- [x] Базовый `RunState` и event log.
- [x] Валидаторы схем и инвариантов.
- [x] Тестовый harness для E2E phase progression.

---

## Workstream 1 — Фаза 1: Intent Surface Extraction

### Задачи
- [x] Реализовать узел фазы 1, создающий только `ProblemSurfaceRecord` proposals.
- [x] Реализовать gate фазы 1 (`PROMOTE|REVISE|REJECT`) с записью `DecisionEvent`.
- [x] Добавить запрет domain lock-in без explicit candidate interpretation.

### Комплексные тесты
- [x] **F1.Core.Functionality**: из бытового запроса формируется валидный `ProblemSurfaceRecord` со всеми обязательными полями.
- [x] **F1.Gate.Invariants**: gate отклоняет записи с solution-hypothesis leakage и unlabeled specialist terms.
- [x] **F1.CrossPhase.Baseline**: promoted output фазы 1 становится единственным допустимым входом для фазы 2 (без скрытых данных).

---

## Workstream 2 — Фаза 2: Vocabulary Bootstrapping

### Задачи
- [x] Реализовать генерацию `VocabularyCandidateSet` только из promoted surface.
- [x] Реализовать gate фазы 2 с проверкой отсутствия преждевременной нормализации.
- [x] Добавить контроль confusable terms и unresolved terminology questions.

### Комплексные тесты
- [x] **F2.Core.Functionality**: фаза производит candidate terms + paraphrases + confusable terms по фрагментам surface.
- [x] **F2.Gate.Invariants**: gate блокирует preferred term selection на фазе 2.
- [x] **F2.CrossPhase.Compatibility**: при изменении promoted surface предыдущая vocabulary-инстанция корректно помечается invalid/revise-required.

---

## Workstream 3 — Фаза 3: Terminology Normalization

### Задачи
- [x] Реализовать `WorkingLexicon` с term families, retrieval roles и reasons.
- [x] Реализовать gate фазы 3 с обязательной связью preferred terms с retrieval precision/fidelity.
- [x] Добавить explicit `terms_to_avoid` и conflict notes.

### Комплексные тесты
- [x] **F3.Core.Functionality**: формируются валидные term families с допустимыми ролями (`seed|expansion|negative_filter|context_only`).
- [x] **F3.Gate.Invariants**: gate отклоняет preferred term без обоснования для retrieval/instruction fidelity.
- [x] **F3.CrossPhase.Compatibility**: все preferred terms трассируются к vocabulary candidates и surface fragments; orphan terms не допускаются.

---

## Workstream 4 — Фаза 4: Hypothesis Lattice

### Задачи
- [x] Реализовать `HypothesisLattice` с differentiable hypotheses.
- [x] Реализовать gate фазы 4 (запрет дубликатов/вариантов одной идеи).
- [x] Добавить связи с intent fragments и lexicon terms.

### Комплексные тесты
- [x] **F4.Core.Functionality**: создаются гипотезы с evidence_needed и falsification conditions.
- [x] **F4.Gate.Invariants**: gate отклоняет недифференцируемые гипотезы.
- [x] **F4.CrossPhase.Compatibility**: каждая гипотеза опирается на promoted surface+lexicon; отсутствие связей приводит к revise.

---

## Workstream 5 — Фаза 5: Source-Discovery Design

### Задачи
- [x] Реализовать `SourceDiscoveryPlan` по каждой активной гипотезе.
- [x] Обязать наличие source groups, query families, negative filters, expected evidence types.
- [x] Реализовать pre-retrieval gate (жёсткий запрет retrieval до promotion плана).

### Комплексные тесты
- [x] **F5.Core.Functionality**: для каждой гипотезы присутствуют source groups с epistemic roles и limitations.
- [x] **F5.Gate.Invariants**: gate отклоняет plan без negative filters или без expected evidence types.
- [x] **F5.CrossPhase.Compatibility**: plan содержит только термины/гипотезы из promoted state; устаревшие ссылки отклоняются.
- [x] **F5.Policy.BlockPrematureRetrieval**: вызов `search.run` до promoted plan завершается проверяемой protocol error.

---

## Workstream 6 — Фаза 6: Triage and Extraction

### Задачи
- [x] Реализовать triage-слой (`accepted/rejected/review_bucket`) с причинами решений.
- [x] Реализовать extraction-слой с provenance locator.
- [x] Вести rejection log и uncertainty flags.

### Комплексные тесты
- [x] **F6.Core.Functionality**: из реальных retrieved records формируются triage и extraction records по схеме.
- [x] **F6.Gate.Invariants**: summary/synthesis запрещены до наличия extraction criteria и evidence matrix.
- [x] **F6.CrossPhase.Compatibility**: каждый extraction связан с hypothesis из promoted lattice и query family из promoted discovery plan.
- [x] **F6.DataIntegrity**: `source_id`/`extraction_id`/locator непротиворечивы и разрешаются в source registry.

---

## Workstream 7 — Фаза 7: Verification Memory

### Задачи
- [x] Реализовать `VerificationLedger` как append-only журнал.
- [x] Реализовать claim lifecycle (`proposed|accepted|rejected|needs_review|verified`).
- [x] Реализовать claim validation events и contradiction tracking.

### Комплексные тесты
- [x] **F7.Core.Functionality**: ledger хранит promoted-state pointers, claim records, source links и decision history.
- [x] **F7.Gate.Invariants**: worker output не может стать authoritative без gate promotion.
- [x] **F7.CrossPhase.Compatibility**: claims валидно ссылаются на extractions/source locator из фазы 6 и на контекст фаз 1–5.
- [x] **F7.Contradiction.Preservation**: при конфликтующих accepted claims создаются contradiction records, конфликт не сглаживается.

---

## Workstream 8 — Ledger Interpreter (read-only представления verification memory)

### Задачи
- [x] Ввести read-only сущность `ledger_interpreter`, читающую только promoted `phase7_verification_memory`.
- [x] Спроектировать `LedgerInterpretationView`:
  - `claims_by_status` (`proposed|accepted|rejected|needs_review|verified`);
  - `source_link_index`;
  - `open_contradictions`;
  - `synthesis_readiness` + `blocking_reasons`;
  - `next_actions`.
- [x] Зафиксировать policy, что interpreter не меняет `RunState` и не может выполнять promotion/verification действий.
- [x] Добавить операторские сценарии использования interpreter в RUNBOOK (диагностика и triage блокеров synthesis).

### Комплексные тесты
- [x] **F8I.Core.Functionality**: interpreter строит человеко-читаемый view из реального promoted ledger без потери claim/source/contradiction связей.
- [x] **F8I.ReadOnly.Invariant**: после вызова interpreter `run_state.proposals/events/promoted` остаются неизменными (zero-mutation guarantee).
- [x] **F8I.Contradiction.Visibility**: unresolved contradictions всегда явно присутствуют в view и не маскируются.
- [x] **F8I.Readiness.Blockers**: при `unchecked`/`disputed` валидации `authoritative_ready=False`, а `blocking_reasons` содержит трассируемые причины.

---

## Workstream 9 — Фаза 8: Finalizer (terminal result)

### Задачи
- [x] Добавить `phase8_finalizer` как отдельную терминальную фазу после promoted `phase7_verification_memory`.
- [x] Реализовать outcomes фазы 8:
  - `authoritative_synthesis`;
  - `limited_synthesis`;
  - `blocked_finalization_report`.
- [x] Реализовать gate фазы 8 (`PROMOTE|REVISE|REJECT`) с правилами:
  - authoritative запрещён при `unchecked` для обязательных validation полей;
  - contradictions не могут быть скрыты или сглажены;
  - append-only history не перезаписывается.
- [x] Добавить `finalization_status` в promoted-state (`authoritative|limited|blocked`) как terminal marker.
- [x] Зафиксировать authority boundary: worker output не может стать финальной authoritative выдачей без gate decision.

### Комплексные тесты
- [x] **F8.Core.Functionality**: фаза 8 формирует корректный terminal record и пишет `DecisionEvent` с валидным outcome.
- [x] **F8.Authoritative.Readiness**: authoritative synthesis отклоняется при любом `unchecked` в обязательной claim validation.
- [x] **F8.Limited.WithDisclosure**: limited synthesis разрешён только при явном раскрытии ограничений и границ применимости.
- [x] **F8.Blocked.FinalizationReport**: при критических блокерах создаётся blocked report с actionable next steps.
- [x] **F8.Contradiction.Preservation**: финализация не удаляет contradiction records и не сводит конфликт к нейтральной прозе.
- [x] **F8.AuthorityBoundary**: попытка worker-обхода gate приводит к protocol error/reject.

---

## Сквозные интеграционные тесты (A–F + расширение)

- [ ] **IT.A.ZeroKnowledgeInput**: фазы 1–5 проходят без retrieval и без domain lock-in.
- [ ] **IT.B.NoRetrievalBeforeDesign**: retrieval невозможен до promoted SourceDiscoveryPlan.
- [ ] **IT.C.SourceGroupSeparation**: группы источников разделены по epistemic role и limitations.
- [ ] **IT.D.ContradictionPreservation**: конфликт claims сохраняется в ledger.
- [ ] **IT.E.SynthesisRefusalWithoutProvenance**: synthesis запрещается при отсутствии provenance/validation.
- [ ] **IT.F.ReferenceLeakageGuards**: PICO/Boolean/UI/backend не становятся протоколом по умолчанию.
- [ ] **IT.G.ReopenAndInvalidateFlow**: изменение ранней фазы инициирует downstream invalidation и обязательный пересмотр.
- [ ] **IT.H.Auditability**: весь run восстанавливается из ledger без скрытого состояния.
- [ ] **IT.I.InterpreterReadOnlyAuditView**: ledger interpreter предоставляет полный audit view без мутации состояния.
- [ ] **IT.J.FinalizerOutcomeMatrix**: для одного и того же run корректно различаются authoritative/limited/blocked исходы в зависимости от validation/contradiction статуса.

---

## Тесты Output Contract (OC)

- [ ] **OC.ExactlyOneReport**: для completed run возвращается ровно один терминальный markdown-отчёт.
- [ ] **OC.ReportEnvelopePresent**: в ответе присутствует полный `report_envelope`; для unrecoverable ошибок — `terminal_error_return`.
- [ ] **OC.MarkdownEnvelopeConsistency**: metadata в YAML front matter markdown побайтно согласована с возвращаемым `report_envelope`; при расхождении run помечается invalid/not-completed.
- [ ] **OC.Phase8MappingConsistency**: соответствие `phase8 outcome -> report_filename` строго следует утверждённому mapping.
- [ ] **OC.BlockedReportNoSynthesis**: `blocked_finalization_report` не содержит ложной authoritative/limited финализации и в `## 6.1 Main synthesis` явно сообщает, что synthesis не произведён из-за blocked finalization.
- [ ] **OC.ProtocolErrorNoFalseReport**: при unrecoverable protocol error возвращается только `terminal_error_return`, без markdown-отчёта.

---

## Output contract: как пользователь получает отчёт (Markdown)

### Return contract (обязательный)
- [ ] Executor возвращает:
  - `report_markdown: string`
  - `report_filename: authoritative_synthesis_report.md | limited_synthesis_report.md | blocked_finalization_report.md`
  - `report_type: authoritative | limited | blocked`
  - `report_envelope: ReportEnvelope`
- [ ] Для unrecoverable ошибок finalization возвращается:
  - `terminal_error_return`:
    - `error_type: terminal_error`
    - `run_id: string | null`
    - `reason: string`
    - `diagnostic_event_id: string | null`
    - `safe_to_retry: boolean`
- [ ] `terminal_error_return` взаимоисключающ с markdown-отчётом (либо report, либо terminal_error).

### Delivery contract (обязательный)
- [ ] Если включён filesystem output, идентичный markdown записывается в:
  - `runs/{run_id}/reports/{report_filename}`
- [ ] В API/SDK режимах всегда доступен `report_markdown` + `report_envelope`.
- [ ] В CLI режимах поддерживается печать в `stdout` и/или запись в artifact path (через флаги запуска).

### Markdown envelope contract (обязательный)
- [ ] Markdown-отчёт начинается с YAML front matter.
- [ ] YAML front matter содержит тот же `report_envelope`, что и return payload.
- [ ] При расхождении front matter и return envelope run помечается `invalid` и MUST NOT считаться completed.

### Report type mapping (обязательный)
- [ ] Соответствие Phase 8 outcome -> report filename зафиксировано и проверяется:
  - `authoritative_synthesis -> authoritative_synthesis_report.md`
  - `limited_synthesis -> limited_synthesis_report.md`
  - `blocked_finalization_report -> blocked_finalization_report.md`
- [ ] `finalization_status` и `report_filename` всегда согласованы с mapping.

### Blocked report contract (обязательный)
- [ ] Для `blocked` секция `## 6.1 Main synthesis` содержит явную фразу:
  - `No synthesis was produced because finalization is blocked.`
- [ ] `blocked` отчёт не может содержать authoritative/limited финальные выводы.

---

## Definition of Done (DoD)

Проект готов к “implementation complete”, когда:
- [ ] все фазовые тесты пройдены;
- [ ] все кросс-фазовые тесты совместимости пройдены;
- [ ] сквозные интеграционные тесты A–H пройдены;
- [ ] output-contract тесты OC пройдены;
- [ ] отсутствуют нарушения контрольных запретов;
- [ ] audit trail воспроизводим по ledger;
- [ ] интерпретация ledger доступна через read-only view без изменения состояния;
- [ ] terminal finalization (Phase 8) корректно выбирает authoritative/limited/blocked outcome по gate-политике;
- [ ] документация (`README.md`, `RUNBOOK.md`, `ARCHITECTURE.md`) заполнена и актуальна.

---

## Обязательная сопровождающая документация при выполнении `tasks.md`

### README.md
Должен содержать:
- назначение проекта и scope;
- требования к окружению;
- установку зависимостей;
- запуск executor;
- запуск тестов (unit/integration/protocol);
- примеры типовых сценариев использования.

### RUNBOOK.md
Должен содержать:
- операционные процедуры запуска;
- health checks и метрики;
- диагностику типовых сбоев (gates, invalidation, capability failures);
- процедуры восстановления (replay из ledger, rollback promoted state);
- эскалацию и response checklist.

### ARCHITECTURE.md
Должен содержать:
- карту компонентов (graph nodes, gates, capabilities, state store, ledger);
- контракты данных и lifecycle записей;
- transition logic и policies;
- authority boundaries;
- traceability/auditability модель;
- decision log по архитектурным компромиссам.
