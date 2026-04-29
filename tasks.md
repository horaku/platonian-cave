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
- [ ] Реализовать `VerificationLedger` как append-only журнал.
- [ ] Реализовать claim lifecycle (`proposed|accepted|rejected|needs_review|verified`).
- [ ] Реализовать claim validation events и contradiction tracking.

### Комплексные тесты
- [ ] **F7.Core.Functionality**: ledger хранит promoted-state pointers, claim records, source links и decision history.
- [ ] **F7.Gate.Invariants**: worker output не может стать authoritative без gate promotion.
- [ ] **F7.CrossPhase.Compatibility**: claims валидно ссылаются на extractions/source locator из фазы 6 и на контекст фаз 1–5.
- [ ] **F7.Contradiction.Preservation**: при конфликтующих accepted claims создаются contradiction records, конфликт не сглаживается.

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

---

## Definition of Done (DoD)

Проект готов к “implementation complete”, когда:
- [ ] все фазовые тесты пройдены;
- [ ] все кросс-фазовые тесты совместимости пройдены;
- [ ] сквозные интеграционные тесты A–H пройдены;
- [ ] отсутствуют нарушения контрольных запретов;
- [ ] audit trail воспроизводим по ledger;
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
