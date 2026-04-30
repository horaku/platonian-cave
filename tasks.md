# Doc3 Executor — задачи разработки и комплексные тесты фаз

## Tasks Iteration 1: Protocol-driven state machine

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

- [x] **IT.A.ZeroKnowledgeInput**: фазы 1–5 проходят без retrieval и без domain lock-in.
- [x] **IT.B.NoRetrievalBeforeDesign**: retrieval невозможен до promoted SourceDiscoveryPlan.
- [x] **IT.C.SourceGroupSeparation**: группы источников разделены по epistemic role и limitations.
- [x] **IT.D.ContradictionPreservation**: конфликт claims сохраняется в ledger.
- [x] **IT.E.SynthesisRefusalWithoutProvenance**: synthesis запрещается при отсутствии provenance/validation.
- [x] **IT.F.ReferenceLeakageGuards**: PICO/Boolean/UI/backend не становятся протоколом по умолчанию.
- [x] **IT.G.ReopenAndInvalidateFlow**: изменение ранней фазы инициирует downstream invalidation и обязательный пересмотр.
- [x] **IT.H.Auditability**: весь run восстанавливается из ledger без скрытого состояния.
- [x] **IT.I.InterpreterReadOnlyAuditView**: ledger interpreter предоставляет полный audit view без мутации состояния.
- [x] **IT.J.FinalizerOutcomeMatrix**: для одного и того же run корректно различаются authoritative/limited/blocked исходы в зависимости от validation/contradiction статуса.

---

## Тесты Output Contract (OC)

- [x] **OC.ExactlyOneReport**: для completed run возвращается ровно один терминальный markdown-отчёт.
- [x] **OC.ReportEnvelopePresent**: в ответе присутствует полный `report_envelope`; для unrecoverable ошибок — `terminal_error_return`.
- [x] **OC.MarkdownEnvelopeConsistency**: metadata в YAML front matter markdown побайтно согласована с возвращаемым `report_envelope`; при расхождении run помечается invalid/not-completed.
- [x] **OC.Phase8MappingConsistency**: соответствие `phase8 outcome -> report_filename` строго следует утверждённому mapping.
- [x] **OC.BlockedReportNoSynthesis**: `blocked_finalization_report` не содержит ложной authoritative/limited финализации и в `## 6.1 Main synthesis` явно сообщает, что synthesis не произведён из-за blocked finalization.
- [x] **OC.ProtocolErrorNoFalseReport**: при unrecoverable protocol error возвращается только `terminal_error_return`, без markdown-отчёта.

---

## Output contract: как пользователь получает отчёт (Markdown)

### Return contract (обязательный)
- [x] Executor возвращает:
  - `report_markdown: string`
  - `report_filename: authoritative_synthesis_report.md | limited_synthesis_report.md | blocked_finalization_report.md`
  - `report_type: authoritative | limited | blocked`
  - `report_envelope: ReportEnvelope`
- [x] Для unrecoverable ошибок finalization возвращается:
  - `terminal_error_return`:
    - `error_type: terminal_error`
    - `run_id: string | null`
    - `reason: string`
    - `diagnostic_event_id: string | null`
    - `safe_to_retry: boolean`
- [x] `terminal_error_return` взаимоисключающ с markdown-отчётом (либо report, либо terminal_error).

### Delivery contract (обязательный)
- [x] Если включён filesystem output, идентичный markdown записывается в:
  - `runs/{run_id}/reports/{report_filename}`
- [x] В API/SDK режимах всегда доступен `report_markdown` + `report_envelope`.
- [x] В CLI режимах поддерживается печать в `stdout` и/или запись в artifact path (через флаги запуска).

### Markdown envelope contract (обязательный)
- [x] Markdown-отчёт начинается с YAML front matter.
- [x] YAML front matter содержит тот же `report_envelope`, что и return payload.
- [x] При расхождении front matter и return envelope run помечается `invalid` и MUST NOT считаться completed.

### Report type mapping (обязательный)
- [x] Соответствие Phase 8 outcome -> report filename зафиксировано и проверяется:
  - `authoritative_synthesis -> authoritative_synthesis_report.md`
  - `limited_synthesis -> limited_synthesis_report.md`
  - `blocked_finalization_report -> blocked_finalization_report.md`
- [x] `finalization_status` и `report_filename` всегда согласованы с mapping.

### Blocked report contract (обязательный)
- [x] Для `blocked` секция `## 6.1 Main synthesis` содержит явную фразу:
  - `No synthesis was produced because finalization is blocked.`
- [x] `blocked` отчёт не может содержать authoritative/limited финальные выводы.

---

## Workstream 10 — Productization: устойчивый user-facing runner и упаковка

### Задачи
- [x] Реализовать единый `run_workflow_resilient` (или CLI entrypoint), который ведёт run через Phase 1→8 с учётом gate-решений.
- [x] Внедрить policy для `REVISE`:
  - bounded retry;
  - логика переоткрытия предыдущей фазы;
  - формирование понятного user-facing сообщения с `reason` и `next action`.
- [x] Внедрить policy для `REJECT`:
  - немедленный controlled stop;
  - генерация `blocked_finalization_report` / `terminal_error_return` по контракту.
- [x] Устранить packaging gap для `src/` layout:
  - добавить корректную setuptools-конфигурацию package discovery в `pyproject.toml`;
  - обеспечить импорт `doc3_executor` после `pip install -e .` без `PYTHONPATH` хака.
- [x] Добавить официальный CLI/runner сценарий в README и RUNBOOK:
  - минимальная команда запуска;
  - expected outputs;
  - поведение при `REVISE/REJECT`.

### Комплексные тесты
- [x] **P10.Runner.HappyPath**: user-facing runner проходит цепочку 1→8 и возвращает terminal report payload.
- [x] **P10.Runner.ReviseRecovery**: при `REVISE` runner выполняет retry/reopen policy и завершает run без необработанного исключения.
- [x] **P10.Runner.RejectHandling**: при `REJECT` runner корректно завершает run через blocked/error ветку output contract.
- [x] **P10.Packaging.EditableInstall**: после `pip install -e .` импорт `doc3_executor` работает в отдельном python-процессе без `PYTHONPATH`.
- [x] **P10.CLI.WindowsFlow**: Windows-совместимый сценарий запуска (PowerShell) приводит к artifact report path без ручного патчинга окружения.

---

## Tasks Iteration 2: Agentic deep-research workflow

### Workstream A2.1 — Agentic runtime contract and decision records

#### Задачи
- [ ] Ввести обязательный `agent_step_record`:
  - `selected_capability`,
  - `intent_for_step`,
  - `why_this_step`,
  - `expected_state_change`,
  - `risk_flags`.
- [ ] Зафиксировать policy matrix “какая capability разрешена на какой фазе”.
- [ ] Реализовать аудит-связь `agent_step_record -> DecisionEvent -> promoted/verified state`.

#### Комплексные тесты
- [ ] **A2.Contract.StepTraceability**: каждый шаг агента связан с event chain и воспроизводим по run history.
- [ ] **A2.Contract.CapabilityPolicy**: нарушение phase-capability policy блокируется и фиксируется как policy violation.

---

### Workstream A2.2 — Capability expansion for deep-research execution

#### Задачи
- [ ] Реализовать рабочие adapters для:
  - `search.run`,
  - `source.fetch`,
  - `source.enrich`,
  - `extract.claims`,
  - `validate.claim`,
  - `compare.contradictions`.
- [ ] Добавить единый capability response envelope:
  - `status`,
  - `payload`,
  - `errors`,
  - `provenance_links`.
- [ ] Ввести timeout/retry/failure taxonomy для внешних capability вызовов.

#### Комплексные тесты
- [ ] **A2.Tools.ExecutionSurface**: агент выполняет multi-step capability chain без обхода gate-политик.
- [ ] **A2.Tools.FailureRecovery**: capability-failures переводятся в управляемый recovery/blocked path без необработанного падения.

---

### Workstream A2.3 — Deliberation loop and revise-class recovery

#### Задачи
- [ ] Расширить runner до deliberation-first цикла:
  - выбор следующего шага на основе gaps/contradictions;
  - strategy selection для `REVISE`.
- [ ] Ввести revise-classification:
  - ambiguity,
  - terminology mismatch,
  - insufficient evidence,
  - policy violation.
- [ ] Для каждого revise-класса закрепить recovery strategy + bounded attempts + escalation.

#### Комплексные тесты
- [ ] **A2.Revise.ClassStrategies**: для каждого revise-класса применяется корректная стратегия восстановления.
- [ ] **A2.Reject.ControlledStop**: reject завершает run через blocked/error output branch с понятной диагностикой.

---

### Workstream A2.4 — Human-in-the-loop checkpoints

#### Задачи
- [ ] Добавить explicit human checkpoints для критичных promotion/finalization переходов.
- [ ] Реализовать override records:
  - actor,
  - reason,
  - affected records,
  - downstream invalidation marker.
- [ ] Ввести policy “agent recommendation != final authority” для high-impact решений.

#### Комплексные тесты
- [ ] **A2.HITL.OverrideAudit**: каждый override записывается в ledger/decision history и воспроизводим.
- [ ] **A2.HITL.PolicyBoundary**: критичный переход невозможен без required human checkpoint.

---

### Workstream A2.5 — Synthesis quality and contradiction fidelity

#### Задачи
- [ ] Реализовать rich synthesis renderer:
  - evidence backbone,
  - claim status matrix,
  - contradiction section,
  - limitations,
  - next actions.
- [ ] Для `limited` отчётов строить synthesis только по validated subset с явным disclosure.
- [ ] Запретить neutral smoothing конфликтов в narrative.

#### Комплексные тесты
- [ ] **A2.Synthesis.ContentMinBar**: отчет содержит обязательные содержательные секции, а не template-only строку.
- [ ] **A2.Synthesis.ContradictionFidelity**: conflicts явно отражены в финальном отчете и не исчезают при рендере.

---

### Workstream A2.6 — Product-grade e2e reliability and replay

#### Задачи
- [ ] Добавить e2e smoke сценарии CLI для Windows/Linux.
- [ ] Реализовать replay-from-ledger сценарий до эквивалентного terminal outcome.
- [ ] Добавить run-level diagnostics summary и failure-classification report.

#### Комплексные тесты
- [ ] **A2.E2E.CLI.Windows**: стандартный PowerShell запуск даёт terminal payload и artifact path без manual hacks.
- [ ] **A2.E2E.Replay**: run воспроизводится из ledger до эквивалентного report outcome.

---

## Definition of Done (DoD)

### Iteration 1 DoD — Completed baseline

Итерация 1 готова к “implementation complete”, когда:
- [x] все фазовые тесты пройдены;
- [x] все кросс-фазовые тесты совместимости пройдены;
- [x] сквозные интеграционные тесты A–H пройдены;
- [x] output-contract тесты OC пройдены;
- [x] отсутствуют нарушения контрольных запретов;
- [x] audit trail воспроизводим по ledger;
- [x] интерпретация ledger доступна через read-only view без изменения состояния;
- [x] terminal finalization (Phase 8) корректно выбирает authoritative/limited/blocked outcome по gate-политике;
- [x] документация (`README.md`, `RUNBOOK.md`, `ARCHITECTURE.md`) заполнена и актуальна.
- [x] user-facing runner устойчиво обрабатывает `PROMOTE|REVISE|REJECT` без ручного вмешательства в код запуска.
- [x] editable-install и импорт package подтверждены на чистом окружении без `PYTHONPATH` workaround.

### Iteration 2 DoD — Planned / In progress

Итерация 2 считается завершённой только когда:
- [ ] закрыты workstreams A2.1–A2.6 (задачи и соответствующие комплексные тесты);
- [ ] agentic runtime сохраняет полную трассируемость шагов (`agent_step_record -> DecisionEvent -> promoted/verified state`);
- [ ] capability policy matrix соблюдается и нарушения блокируются gate/policy слоем;
- [ ] revise/reject ветки дают контролируемый recovery/blocked outcome без необработанных исключений;
- [ ] HITL checkpoints и override-аудит работают как обязательная authority boundary;
- [ ] финальный synthesis сохраняет contradiction fidelity и disclosure для limited outcome;
- [ ] e2e CLI smoke + replay-from-ledger подтверждают воспроизводимость terminal outcome.

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
