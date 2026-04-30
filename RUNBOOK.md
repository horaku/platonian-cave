# RUNBOOK — Doc3 Executor

## Назначение
Операционное руководство по запуску, наблюдению, диагностике и восстановлению для текущей реализации:
- **Phase 1 — Intent Surface Extraction**
- **Phase 2 — Vocabulary Bootstrapping**

Документ фиксирует точный порядок событий, gate-переходов и условий promotion/invalidation.

---

## 1) Что реализовано

### Phase 1
1. Вход: plain-language запрос.
2. Выход фазы: `ProblemSurfaceRecord` в proposal.
3. Gate: `PROMOTE|REVISE|REJECT`.
4. Event: `DecisionEvent` записывается всегда.
5. Promotion: только при `PROMOTE`.

### Phase 2
1. Вход: только `promoted` output Phase 1 (`phase1_intent_surface`).
2. Выход фазы: `VocabularyCandidateSet`-подобный payload (`by_surface_fragment`, paraphrases, confusable terms, unresolved questions).
3. Gate: расширение терминов без нормализации (expansion-only).
4. Event: `DecisionEvent` записывается всегда.
5. Promotion: только при `PROMOTE`.
6. Совместимость: `phase1_fingerprint` в phase2 payload для проверки invalidation.

---

## 2) Компоненты и роли

- `extract_problem_surface` — phase1 node.
- `review_phase1` — gate phase1.
- `run_phase1` — оркестрация phase1.
- `build_vocabulary_candidates` — phase2 node.
- `review_phase2` — gate phase2.
- `run_phase2` — оркестрация phase2.
- `is_phase2_invalidated` — проверка совместимости phase2 с обновлённым promoted phase1.
- `InMemoryStateStore` — proposals/events/promoted storage.

---

## 3) Порядок событий: Phase 1

1. Создать `RunState(run_id, trace_id)`.
2. Вызвать `run_phase1(run_state, user_input)`.
3. `extract_problem_surface` формирует структуру surface.
4. Executor создаёт `ProposalRecord(phase="phase1_intent_surface")`.
5. `state_store.propose()` сохраняет proposal.
6. `review_phase1()` возвращает decision+reason.
7. Executor пишет `DecisionEvent` через `state_store.add_event()`.
8. Если decision=`PROMOTE`, выполнить `state_store.promote()`.
9. Вернуть обновлённый `run_state`.

---

## 4) Порядок событий: Phase 2

1. Проверить наличие `run_state.promoted["phase1_intent_surface"]`.
   - если нет: phase2 запуск запрещён (`ValueError`).
2. Вызвать `run_phase2(run_state)`.
3. `build_vocabulary_candidates(phase1_surface)` строит payload:
   - `candidate_professional_terms`,
   - `searchable_paraphrases`,
   - `nearby_but_confusable_terms`,
   - `unresolved_terminology_questions`,
   - `phase1_fingerprint`.
4. Executor создаёт `ProposalRecord(phase="phase2_vocabulary_bootstrap")`.
5. `state_store.propose()` сохраняет proposal.
6. `review_phase2()` проверяет expansion-only contract.
7. Executor пишет `DecisionEvent`.
8. Если decision=`PROMOTE`, `state_store.promote("phase2_vocabulary_bootstrap", proposal)`.
9. Возвращается обновлённый `run_state`.

---

## 5) Gate-инварианты

### Phase 1 gate
- `stated_request` пустой → `REJECT`
- Domain lock-in (“это задача из…”) → `REVISE`
- Specialist term leakage в surface → `REVISE`
- Нет candidate interpretations → `REJECT`
- Иначе `PROMOTE`

### Phase 2 gate
- Нет `by_surface_fragment` → `REJECT`
- Нет candidate terms во фрагменте → `REVISE`
- Есть `preferred_term` (premature normalization) → `REVISE`
- Нет confusable terms → `REVISE`
- Нет unresolved terminology questions → `REVISE`
- Иначе `PROMOTE`

---

## 6) Проверка совместимости Phase 1 ↔ Phase 2

Механизм:
- В phase2 payload сохраняется `phase1_fingerprint`.
- Функция `is_phase2_invalidated(run_state)` пересчитывает expected fingerprint на базе текущего promoted Phase 1.
- Если fingerprints расходятся → Phase 2 считается invalidated и требует `REVISE/re-run`.

---

## 7) Операционный запуск

### 7.1 Тест исполняемости Phase 2
```bash
pytest -q tests/test_phase2.py
```

### 7.2 Тест совместимости Phase 1 и Phase 2
```bash
pytest -q tests/test_phase1.py tests/test_phase2.py
```

### 7.3 Ручной интеграционный прогон P1→P2
```bash
PYTHONPATH=src python - <<'PY'
from doc3_executor.graph.executor import run_phase1
from doc3_executor.graph.phase2 import run_phase2, is_phase2_invalidated
from doc3_executor.schemas.models import RunState

rs = RunState(run_id='run_p1_p2', trace_id='trace_p1_p2')
run_phase1(rs, 'Хочу понять, как лучше искать материалы про то, почему люди бросают сложные онлайн-курсы')
run_phase2(rs)

print('phase1_promoted=', 'phase1_intent_surface' in rs.promoted)
print('phase2_promoted=', 'phase2_vocabulary_bootstrap' in rs.promoted)
print('events=', len(rs.events))
print('invalidated_before_change=', is_phase2_invalidated(rs))

rs.promoted['phase1_intent_surface']['stated_request'] = 'Другой запрос для проверки'
print('invalidated_after_change=', is_phase2_invalidated(rs))
PY
```

Ожидание:
- обе фазы promoted = `True`
- events = 2
- invalidated_before_change = `False`
- invalidated_after_change = `True`

---

## 8) Диагностика

### `ValueError: phase2 requires promoted phase1_intent_surface`
Причина: Phase 2 запущена до успешной promotion фазы 1.
Действия:
1. проверить последний `DecisionEvent` phase1;
2. если `REVISE/REJECT` — исправить surface и перезапустить Phase 1;
3. повторить запуск Phase 2.

### Phase 2 decision = `REVISE`
Проверить reason:
- premature normalization;
- missing confusable terms;
- missing unresolved terminology questions;
- missing candidate terms.

### `ModuleNotFoundError: doc3_executor`
Добавить `PYTHONPATH=src` для прямого запуска python.

---

## 9) Восстановление

Текущий backend — in-memory:
1. Повторить прогон с теми же входными параметрами.
2. Сравнить `proposals/events/promoted`.
3. При несовместимости Phase 2 выполнить re-run после re-promotion Phase 1.

Ограничение: долговременный persistence backend ещё не внедрён.

---

## 10) Incident checklist

Перед закрытием инцидента проверить:
- [ ] `phase1_intent_surface` promoted при успешном gate.
- [ ] `phase2_vocabulary_bootstrap` promoted при успешном gate.
- [ ] по каждой фазе есть `DecisionEvent`.
- [ ] Phase 2 не запускается без promoted Phase 1.
- [ ] `is_phase2_invalidated` корректно выявляет рассинхронизацию после изменения Phase 1.
- [ ] тесты `tests/test_phase1.py` и `tests/test_phase2.py` проходят.

---

## 11) Порядок событий: Phase 3 (Terminology Normalization)

1. Предусловие: должен существовать `run_state.promoted["phase2_vocabulary_bootstrap"]`.
   - Если нет — запуск Phase 3 запрещён (`ValueError`).
2. Вызов `run_phase3(run_state)`.
3. `normalize_terminology(phase2_payload)` строит `WorkingLexicon`-структуру:
   - `term_families`;
   - `preferred_term`, `acceptable_synonyms`, `terms_to_avoid`, `conflict_notes`;
   - `why_preferred_for_this_workflow`, `retrieval_role`;
   - `source_terms` (обязательная трассировка к кандидатам из Phase 2).
4. Executor создаёт `ProposalRecord(phase="phase3_terminology_normalization")`.
5. Proposal записывается в `run_state.proposals`.
6. `review_phase3(payload)` выполняет gate-check:
   - families не пустые;
   - preferred terms уникальны;
   - retrieval_role ∈ `{seed, expansion, negative_filter, context_only}`;
   - reason связан с retrieval precision/fidelity;
   - нет orphan terms (пустых `source_terms`).
7. Пишется `DecisionEvent` в `run_state.events`.
8. Только при `PROMOTE` выполняется запись в `run_state.promoted["phase3_terminology_normalization"]`.

### Ожидаемые исходы
- `PROMOTE`: lexicon пригоден для следующей фазы (hypothesis lattice).
- `REVISE`: терминологическая нормализация недостаточно обоснована/связана с Phase 2.
- `REJECT`: критически некорректная структура payload.

---

## 12) Тест исполняемости Phase 3

```bash
pytest -q tests/test_phase3.py
```

Проверяет:
- core functionality;
- gate invariant по reason (retrieval/fidelity tie);
- cross-phase compatibility (orphan terms block).

---

## 13) Тест совместимости цепочки Phase 1 → Phase 2 → Phase 3

```bash
pytest -q tests/test_phase1.py tests/test_phase2.py tests/test_phase3.py
```

Ручная проверка цепочки:
```bash
PYTHONPATH=src python - <<'PY'
from doc3_executor.graph.executor import run_phase1
from doc3_executor.graph.phase2 import run_phase2
from doc3_executor.graph.phase3 import run_phase3
from doc3_executor.schemas.models import RunState

rs = RunState(run_id='run_p1_p2_p3_ok', trace_id='trace_p1_p2_p3_ok')
run_phase1(rs, 'Нужен план поиска: хочу понять, почему люди бросают онлайн-курсы и как искать источники')
run_phase2(rs)
run_phase3(rs)

print('phase1_promoted=', 'phase1_intent_surface' in rs.promoted)
print('phase2_promoted=', 'phase2_vocabulary_bootstrap' in rs.promoted)
print('phase3_promoted=', 'phase3_terminology_normalization' in rs.promoted)
print('last_decision=', rs.events[-1].decision.value)
PY
```

Ожидание:
- все три promoted-флага `True`;
- последний `DecisionEvent` относится к phase3 и имеет `PROMOTE`.

---

## 14) Диагностика для Phase 3

### Симптом: `phase3_promoted=False` и последний decision=`REVISE`
Частая причина: orphan-linkage в одной из family (`source_terms` пуст).

Действия:
1. Проверить payload Phase 2 и наличие требуемых candidate terms.
2. Проверить причины в `run_state.events[-1].reason`.
3. Исправить mapping в normalization logic и перезапустить Phase 3.

### Симптом: `ValueError: phase3 requires promoted phase2_vocabulary_bootstrap`
Причина: не выполнен/не promoted Phase 2.

Действия:
1. Убедиться, что Phase 2 завершилась решением `PROMOTE`.
2. При `REVISE` — устранить замечания gate Phase 2.
3. Повторить запуск цепочки.

---

## 15) Порядок событий: Phase 4 (Hypothesis Lattice)

1. Предусловия запуска:
   - есть `run_state.promoted["phase1_intent_surface"]`;
   - есть `run_state.promoted["phase3_terminology_normalization"]`.
   - При отсутствии любого из них запуск запрещён (`ValueError`).

2. Вызов `run_phase4(run_state)`.

3. `build_hypothesis_lattice(problem_surface, working_lexicon)` формирует payload с гипотезами:
   - `hypothesis_id`, `framing`, `type`;
   - `linked_intent_fragments`, `linked_lexicon_terms`;
   - `evidence_needed`, `would_be_falsified_by`;
   - `do_not_rank_yet=True`.

4. Executor создаёт `ProposalRecord(phase="phase4_hypothesis_lattice")` и пишет его в `run_state.proposals`.

5. Gate-проверка `review_phase4(payload)`:
   - hypotheses не пустые;
   - `hypothesis_id` уникальны;
   - hypotheses взаимно различимы (non-differentiable варианты отклоняются);
   - есть связи с intent fragments и lexicon terms;
   - есть `evidence_needed` и `would_be_falsified_by`;
   - `do_not_rank_yet` обязательно `True`.

6. Пишется `DecisionEvent` в `run_state.events`.

7. Только при `PROMOTE` выполняется запись в `run_state.promoted["phase4_hypothesis_lattice"]`.

---

## 16) Тест исполняемости Phase 4

```bash
pytest -q tests/test_phase4.py
```

Ожидаемое покрытие:
- core functionality для генерации lattice;
- gate invariant: non-differentiable hypotheses блокируются;
- cross-phase compatibility: отсутствие link к lexicon → `REVISE`.

---

## 17) Тест совместимости цепочки Phase 1 → 2 → 3 → 4

```bash
pytest -q tests/test_phase1.py tests/test_phase2.py tests/test_phase3.py tests/test_phase4.py
```

Ручная проверка полного цикла:
```bash
PYTHONPATH=src python - <<'PY'
from doc3_executor.graph.executor import run_phase1
from doc3_executor.graph.phase2 import run_phase2
from doc3_executor.graph.phase3 import run_phase3
from doc3_executor.graph.phase4 import run_phase4
from doc3_executor.schemas.models import RunState

rs = RunState(run_id='run_p1_p2_p3_p4', trace_id='trace_p1_p2_p3_p4')
run_phase1(rs, 'Нужен план поиска: хочу понять, почему люди бросают онлайн-курсы и как искать источники')
run_phase2(rs)
run_phase3(rs)
run_phase4(rs)

print('phase1_promoted=', 'phase1_intent_surface' in rs.promoted)
print('phase2_promoted=', 'phase2_vocabulary_bootstrap' in rs.promoted)
print('phase3_promoted=', 'phase3_terminology_normalization' in rs.promoted)
print('phase4_promoted=', 'phase4_hypothesis_lattice' in rs.promoted)
print('events=', len(rs.events))
print('last_phase=', rs.events[-1].phase)
print('last_decision=', rs.events[-1].decision.value)
PY
```

Ожидание:
- все `phase*_promoted=True`;
- `events=4`;
- `last_phase=phase4_hypothesis_lattice`;
- `last_decision=PROMOTE`.

---

## 18) Диагностика для Phase 4

### Симптом: `ValueError: phase4 requires promoted phase1_intent_surface and phase3_terminology_normalization`
Причина: отсутствует promoted-state одной из требуемых фаз.

Действия:
1. проверить решения в `run_state.events` для phase1 и phase3;
2. повторно выполнить недостающую фазу до `PROMOTE`;
3. повторно запустить phase4.

### Симптом: `REVISE` на phase4 gate
Типовые причины:
- недифференцируемые гипотезы;
- отсутствуют связи с lexicon/intent;
- отсутствуют `evidence_needed` или `would_be_falsified_by`;
- `do_not_rank_yet != True`.

Действия:
1. проверить `run_state.events[-1].reason`;
2. поправить генерацию lattice;
3. повторить запуск phase4.

---

## 19) Порядок событий: Phase 5 (Source-Discovery Design)

1. Предусловия запуска:
   - есть `run_state.promoted["phase3_terminology_normalization"]`;
   - есть `run_state.promoted["phase4_hypothesis_lattice"]`.
   - При отсутствии любого — запуск фазы 5 запрещён (`ValueError`).

2. Вызов `run_phase5(run_state)`.

3. `build_source_discovery_plan(hypothesis_lattice, working_lexicon)` формирует `by_hypothesis`:
   - для каждой активной гипотезы формируются `source_groups` (с role/limitations);
   - формируются `query_families` с:
     - `seed_terms`, `expansion_terms`,
     - `negative_filters`,
     - `search_ready_queries`,
     - `expected_evidence_types`.

4. Executor создаёт `ProposalRecord(phase="phase5_source_discovery_design")`.

5. Proposal записывается в `run_state.proposals`.

6. Gate-проверка `review_phase5(payload, active_hypothesis_ids)`:
   - покрыты все active hypotheses;
   - есть `source_groups`;
   - есть `query_families`;
   - в каждой query family есть `negative_filters` и `search_ready_queries`;
   - есть и валидны `expected_evidence_types`.

7. Пишется `DecisionEvent` в `run_state.events`.

8. Только при `PROMOTE` обновляется `run_state.promoted["phase5_source_discovery_design"]`.

9. `can_run_retrieval(run_state)` переключается:
   - `False` до promoted Phase 5;
   - `True` после promoted Phase 5.

---

## 20) Тест исполняемости Phase 5

```bash
pytest -q tests/test_phase5.py
```

Покрывает:
- core functionality source-discovery plan;
- gate invariants (включая mandatory negative filters);
- cross-phase hypothesis coverage;
- pre-retrieval policy.

---

## 21) Тест совместимости цепочки Phase 1 → 2 → 3 → 4 → 5

```bash
pytest -q tests/test_phase1.py tests/test_phase2.py tests/test_phase3.py tests/test_phase4.py tests/test_phase5.py
```

Ручной интеграционный прогон:
```bash
PYTHONPATH=src python - <<'PY'
from doc3_executor.graph.executor import run_phase1
from doc3_executor.graph.phase2 import run_phase2
from doc3_executor.graph.phase3 import run_phase3
from doc3_executor.graph.phase4 import run_phase4
from doc3_executor.graph.phase5 import run_phase5, can_run_retrieval
from doc3_executor.schemas.models import RunState

rs = RunState(run_id='run_p1_p2_p3_p4_p5', trace_id='trace_p1_p2_p3_p4_p5')
run_phase1(rs, 'Нужен план поиска: хочу понять, почему люди бросают онлайн-курсы и как искать источники')
run_phase2(rs)
run_phase3(rs)
run_phase4(rs)
print('retrieval_before_p5=', can_run_retrieval(rs))
run_phase5(rs)
print('phase1_promoted=', 'phase1_intent_surface' in rs.promoted)
print('phase2_promoted=', 'phase2_vocabulary_bootstrap' in rs.promoted)
print('phase3_promoted=', 'phase3_terminology_normalization' in rs.promoted)
print('phase4_promoted=', 'phase4_hypothesis_lattice' in rs.promoted)
print('phase5_promoted=', 'phase5_source_discovery_design' in rs.promoted)
print('events=', len(rs.events))
print('last_phase=', rs.events[-1].phase)
print('last_decision=', rs.events[-1].decision.value)
print('retrieval_after_p5=', can_run_retrieval(rs))
PY
```

Ожидание:
- `retrieval_before_p5=False`;
- все `phase*_promoted=True` после phase5;
- `events=5`;
- `last_phase=phase5_source_discovery_design`;
- `last_decision=PROMOTE`;
- `retrieval_after_p5=True`.

---

## 22) Диагностика для Phase 5

### Симптом: `ValueError: phase5 requires promoted phase3_terminology_normalization and phase4_hypothesis_lattice`
Причина: отсутствует promoted-state phase3 или phase4.

Действия:
1. проверить `DecisionEvent` для phase3/phase4;
2. довести недостающую фазу до `PROMOTE`;
3. перезапустить phase5.

### Симптом: `REVISE` на phase5 gate
Типовые причины:
- не покрыты все active hypotheses;
- отсутствуют `negative_filters`;
- отсутствуют `search_ready_queries`;
- пустые/невалидные `expected_evidence_types`.

Действия:
1. проверить `run_state.events[-1].reason`;
2. исправить payload phase5;
3. повторить запуск phase5.

### Симптом: retrieval не разрешён после phase5
Причина: phase5 не получила `PROMOTE`.

Действия:
1. проверить наличие `phase5_source_discovery_design` в `run_state.promoted`;
2. проверить последнее решение gate;
3. исправить замечания и повторить phase5.

---

## 23) Порядок событий: Phase 6 (Triage and Extraction)

1. Предусловия запуска:
   - есть `run_state.promoted["phase4_hypothesis_lattice"]`;
   - есть `run_state.promoted["phase5_source_discovery_design"]`.
   - При отсутствии одного из них `run_phase6` завершится `ValueError`.

2. Вход фазы:
   - `retrieved_records` (реальные записи из retrieval-слоя);
   - promoted state из phases 4 и 5.

3. Вызов `run_phase6(run_state, retrieved_records)`.

4. Внутри phase node `triage_and_extract(...)` формируются:
   - `triage.screening_criteria` (`include_if/exclude_if/review_bucket_if`),
   - `accepted_items`, `rejected_items`, `review_bucket`,
   - `extractions` с provenance:
     - `source_id`,
     - `source_locator.url_or_doi` + span/section,
     - `extracted_claim`,
     - `linked_hypothesis`,
     - `supports_or_challenges`, `uncertainty_flags`.

5. Executor формирует `ProposalRecord(phase="phase6_triage_and_extraction")` и пишет в `run_state.proposals`.

6. Gate `review_phase6(payload, active_hypothesis_ids)` проверяет:
   - полноту screening criteria;
   - наличие extraction matrix, если есть accepted items;
   - связь accepted/extractions с active hypotheses;
   - наличие `source_locator.url_or_doi` и `extracted_claim`.

7. Записывается `DecisionEvent` в `run_state.events`.

8. Если decision=`PROMOTE`, `phase6_triage_and_extraction` попадает в `run_state.promoted`.

9. `can_run_synthesis(run_state)`:
   - `False` до promoted phase6;
   - `True` только при promoted phase6 и непустом `extractions`.

---

## 24) Тест исполняемости Phase 6

```bash
pytest -q tests/test_phase6.py
```

Покрывает:
- core functionality triage/extraction;
- gate invariant: accepted items требуют extraction matrix;
- cross-phase linkage to active hypotheses;
- policy: synthesis blocked before phase6 promotion.

---

## 25) Тест совместимости цепочки Phase 1 → 2 → 3 → 4 → 5 → 6

```bash
pytest -q tests/test_phase1.py tests/test_phase2.py tests/test_phase3.py tests/test_phase4.py tests/test_phase5.py tests/test_phase6.py
```

Ручной интеграционный прогон:
```bash
PYTHONPATH=src python - <<'PY'
from doc3_executor.graph.executor import run_phase1
from doc3_executor.graph.phase2 import run_phase2
from doc3_executor.graph.phase3 import run_phase3
from doc3_executor.graph.phase4 import run_phase4
from doc3_executor.graph.phase5 import run_phase5
from doc3_executor.graph.phase6 import run_phase6, can_run_synthesis
from doc3_executor.schemas.models import RunState

rs = RunState(run_id='run_p1_to_p6', trace_id='trace_p1_to_p6')
run_phase1(rs, 'Нужен план поиска: хочу понять, почему люди бросают онлайн-курсы и как искать источники')
run_phase2(rs)
run_phase3(rs)
run_phase4(rs)
run_phase5(rs)
print('synthesis_before_p6=', can_run_synthesis(rs))

active_hid = rs.promoted['phase4_hypothesis_lattice']['hypotheses'][0]['hypothesis_id']
records = [
    {
        'source_id': 's1',
        'linked_hypotheses': [active_hid],
        'url_or_doi': 'https://example.org/s1',
        'section': 'results',
        'span': 'p3',
        'claim': 'Higher cognitive load increases dropout risk.',
        'evidence_type': 'case_study',
        'supports_or_challenges': 'supports',
    },
    {'source_id': 's2', 'linked_hypotheses': [], 'url_or_doi': 'https://example.org/s2'}
]
run_phase6(rs, records)

print('phase6_promoted=', 'phase6_triage_and_extraction' in rs.promoted)
print('events=', len(rs.events))
print('last_phase=', rs.events[-1].phase)
print('last_decision=', rs.events[-1].decision.value)
print('synthesis_after_p6=', can_run_synthesis(rs))
PY
```

Ожидание:
- `synthesis_before_p6=False`;
- `phase6_promoted=True`;
- `events=6`;
- `last_phase=phase6_triage_and_extraction`;
- `last_decision=PROMOTE`;
- `synthesis_after_p6=True`.

---

## 26) Диагностика для Phase 6

### Симптом: `ValueError: phase6 requires promoted phase4_hypothesis_lattice and phase5_source_discovery_design`
Причина: отсутствует promoted phase4 или phase5.

Действия:
1. проверить `DecisionEvent` phase4/phase5;
2. довести недостающую фазу до `PROMOTE`;
3. повторить phase6.

### Симптом: phase6 decision = `REVISE`
Типовые причины:
- отсутствуют или неполны screening criteria;
- есть accepted items, но отсутствуют extractions;
- extraction привязан к неактивной гипотезе;
- отсутствует `source_locator.url_or_doi` или `extracted_claim`.

Действия:
1. проверить `run_state.events[-1].reason`;
2. исправить triage/extraction payload;
3. повторить запуск phase6.

### Симптом: synthesis остаётся заблокированным после phase6
Причина: phase6 не promoted или пустой extraction matrix.

Действия:
1. проверить наличие `phase6_triage_and_extraction` в `run_state.promoted`;
2. проверить `len(run_state.promoted['phase6_triage_and_extraction']['extractions']) > 0`;
3. устранить причину `REVISE` и повторить phase6.

---

## 27) Порядок событий: Phase 7 (Verification Memory)

1. Предусловие запуска:
   - в `run_state.promoted` присутствует `phase6_triage_and_extraction`.
   - Если нет — `run_phase7` завершится `ValueError`.

2. Вызов `run_phase7(run_state)`.

3. Внутри `build_verification_ledger(...)` формируется `verification_ledger`:
   - `run_id`;
   - `promoted_state` pointers (phase1/phase3/phase4/phase5);
   - `claim_records`, производные из extractions Phase 6;
   - каждый claim содержит:
     - `status` (на старте `proposed`),
     - `source_links` (`source_id`, `extraction_id`, `locator`),
     - `validation_status` (по умолчанию `unchecked`),
     - `decision_history`.

4. Executor создаёт `ProposalRecord(phase="phase7_verification_memory")` и пишет его в `run_state.proposals`.

5. Gate `review_phase7(payload)` проверяет:
   - наличие и целостность ledger;
   - наличие `run_id`;
   - наличие required promoted-state pointers;
   - валидность claim statuses;
   - непустые/валидные source links;
   - валидность значений `validation_status`;
   - наличие `decision_history`.

6. Пишется `DecisionEvent` в `run_state.events`.

7. Только при `PROMOTE` ledger становится `run_state.promoted["phase7_verification_memory"]`.

8. `ready_for_authoritative_synthesis(run_state)`:
   - `False`, если phase7 не promoted;
   - `False`, если в любом claim есть `unchecked` в validation fields;
   - `True` только после завершения валидации всех claim-полей.

---

## 28) Тест исполняемости Phase 7

```bash
pytest -q tests/test_phase7.py
```

Проверяется:
- генерация verification ledger;
- gate invariants по source links / statuses / history;
- блок authoritative synthesis до завершения validation.

---

## 29) Тест совместимости цепочки Phase 1 → 2 → 3 → 4 → 5 → 6 → 7

```bash
pytest -q tests/test_phase1.py tests/test_phase2.py tests/test_phase3.py tests/test_phase4.py tests/test_phase5.py tests/test_phase6.py tests/test_phase7.py
```

Ручной интеграционный прогон:
```bash
PYTHONPATH=src python - <<'PY'
from doc3_executor.graph.executor import run_phase1
from doc3_executor.graph.phase2 import run_phase2
from doc3_executor.graph.phase3 import run_phase3
from doc3_executor.graph.phase4 import run_phase4
from doc3_executor.graph.phase5 import run_phase5
from doc3_executor.graph.phase6 import run_phase6
from doc3_executor.graph.phase7 import run_phase7, ready_for_authoritative_synthesis
from doc3_executor.schemas.models import RunState

rs = RunState(run_id='run_p1_to_p7', trace_id='trace_p1_to_p7')
run_phase1(rs, 'Нужен план поиска: хочу понять, почему люди бросают онлайн-курсы и как искать источники')
run_phase2(rs)
run_phase3(rs)
run_phase4(rs)
run_phase5(rs)

hid = rs.promoted['phase4_hypothesis_lattice']['hypotheses'][0]['hypothesis_id']
run_phase6(rs, [{
    'source_id': 's1',
    'linked_hypotheses': [hid],
    'url_or_doi': 'https://example.org/s1',
    'section': 'results',
    'span': 'p3',
    'claim': 'Higher cognitive load increases dropout risk.',
    'evidence_type': 'case_study',
    'supports_or_challenges': 'supports',
}])

print('authoritative_synthesis_before_p7=', ready_for_authoritative_synthesis(rs))
run_phase7(rs)
print('phase7_promoted=', 'phase7_verification_memory' in rs.promoted)
print('events=', len(rs.events))
print('last_phase=', rs.events[-1].phase)
print('last_decision=', rs.events[-1].decision.value)
print('authoritative_synthesis_after_p7=', ready_for_authoritative_synthesis(rs))
PY
```

Ожидание:
- `authoritative_synthesis_before_p7=False`;
- `phase7_promoted=True`;
- `events=7`;
- `last_phase=phase7_verification_memory`;
- `last_decision=PROMOTE`;
- `authoritative_synthesis_after_p7=False` (пока validation_status = `unchecked`).

---

## 30) Диагностика для Phase 7

### Симптом: `ValueError: phase7 requires promoted phase6_triage_and_extraction`
Причина: phase6 не доведена до `PROMOTE`.

Действия:
1. проверить `run_state.events` на решение phase6;
2. исправить причины `REVISE/REJECT` в phase6;
3. повторно выполнить phase6, затем phase7.

### Симптом: phase7 decision = `REVISE`
Типовые причины:
- claim без source links;
- невалидный `validation_status`;
- отсутствует `decision_history`;
- пустой/невалидный locator в source links.

Действия:
1. проверить `run_state.events[-1].reason`;
2. исправить структуру ledger;
3. повторить запуск phase7.

### Симптом: `ready_for_authoritative_synthesis=False` после phase7 promotion
Причина: ожидаемое поведение до прохождения claim validation (поля остаются `unchecked`).

Действия:
1. выполнить слой validation и обновить validation_status по claim;
2. убедиться, что `unchecked` отсутствует;
3. повторно проверить `ready_for_authoritative_synthesis(run_state)`.

---

## 30) Порядок событий: Phase 8 (Finalizer)

1. Предусловие запуска:
   - в `run_state.promoted` присутствует `phase7_verification_memory`.
   - Если нет — `run_phase8` завершится `ValueError`.

2. Вызов `run_phase8(run_state)`.

3. Executor читает `verification_ledger.claim_records` из promoted Phase 7 и вычисляет:
   - `authoritative_ready` через `ready_for_authoritative_synthesis(run_state)`;
   - наличие `open_contradictions`;
   - наличие `disputed` validation статусов.

4. Формируется `finalization` proposal с outcome:
   - `authoritative_synthesis`, если claims полностью validated и нет открытых конфликтов;
   - `limited_synthesis`, если claims есть, но authoritative условия не выполнены;
   - `blocked_finalization_report`, если есть disputed/критические блокеры.

5. В proposal добавляется report metadata:
   - `report_type` (`authoritative|limited|blocked`)
   - `report_filename`
   - `main_synthesis` (для blocked обязательно: `No synthesis was produced because finalization is blocked.`)

6. Gate `review_phase8(payload)` проверяет:
   - валидный outcome;
   - наличие report metadata;
   - наличие claim_records;
   - запрет authoritative outcome при `unchecked|disputed`;
   - корректную blocked формулировку.

7. Записывается `DecisionEvent` с phase=`phase8_finalizer`.

8. Только при `PROMOTE` proposal становится `run_state.promoted["phase8_finalizer"]`.

---

## 31) Тест исполняемости Phase 8

```bash
pytest -q tests/test_phase8.py
```

Проверяется:
- генерация phase8 finalization proposal;
- запись DecisionEvent для phase8;
- gate-проверки authoritative/blocked инвариантов.

---

## 32) Тест совместимости цепочки Phase 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8

```bash
pytest -q tests/test_phase1.py tests/test_phase2.py tests/test_phase3.py tests/test_phase4.py tests/test_phase5.py tests/test_phase6.py tests/test_phase7.py tests/test_phase8.py
```

Ручной интеграционный прогон:
```bash
PYTHONPATH=src python - <<'PY'
from doc3_executor.graph.executor import run_phase1
from doc3_executor.graph.phase2 import run_phase2
from doc3_executor.graph.phase3 import run_phase3
from doc3_executor.graph.phase4 import run_phase4
from doc3_executor.graph.phase5 import run_phase5
from doc3_executor.graph.phase6 import run_phase6
from doc3_executor.graph.phase7 import run_phase7
from doc3_executor.graph.phase8 import run_phase8
from doc3_executor.schemas.models import RunState

rs = RunState(run_id='run_p1_to_p8', trace_id='trace_p1_to_p8')
run_phase1(rs, 'Нужен план поиска: хочу понять, почему люди бросают онлайн-курсы и как искать источники')
run_phase2(rs)
run_phase3(rs)
run_phase4(rs)
run_phase5(rs)
hid = rs.promoted['phase4_hypothesis_lattice']['hypotheses'][0]['hypothesis_id']
run_phase6(rs, [{
    'source_id': 's1',
    'linked_hypotheses': [hid],
    'url_or_doi': 'https://example.org/s1',
    'section': 'results',
    'span': 'p3',
    'claim': 'Higher cognitive load increases dropout risk.',
    'evidence_type': 'case_study',
    'supports_or_challenges': 'supports',
}])
run_phase7(rs)
run_phase8(rs)

print('phase8_promoted=', 'phase8_finalizer' in rs.promoted)
print('events=', len(rs.events))
print('last_phase=', rs.events[-1].phase)
print('last_decision=', rs.events[-1].decision.value)
print('phase8_outcome=', rs.promoted['phase8_finalizer']['finalization']['outcome'])
PY
```

---

## 33) Дополнения по закрытию Workstream 9

Phase 8 finalizer теперь дополнительно фиксирует:
- `finalization_status`: `authoritative | limited | blocked`;
- `limitations` для limited/blocked outcomes;
- `next_actions` как обязательный actionable список для blocked outcome.

Дополнительные gate-правила Phase 8:
- `limited_synthesis` требует явного disclosure (`limitations`);
- `blocked_finalization_report` требует:
  - стандартную фразу в main synthesis;
  - непустой список `next_actions`.

Дополнительные проверки:
```bash
pytest -q tests/test_phase8.py
```

Покрываются сценарии:
- limited with disclosure;
- blocked report on disputed validation;
- contradiction preservation;
- authority-boundary reject при попытке bypass.

---

## 34) Операторские сценарии: Ledger Interpreter (диагностика и triage блокеров synthesis)

### Назначение
`ledger_interpreter` — read-only слой над promoted `phase7_verification_memory`.
Он не меняет `RunState` и используется оператором для:
- обзора статусов claims;
- локализации блокеров authoritative synthesis;
- приоритизации следующего шага (validation, contradiction review, re-run phase8).

### Базовый операторский сценарий
```bash
PYTHONPATH=src python - <<'PY'
from doc3_executor.graph.executor import run_phase1
from doc3_executor.graph.phase2 import run_phase2
from doc3_executor.graph.phase3 import run_phase3
from doc3_executor.graph.phase4 import run_phase4
from doc3_executor.graph.phase5 import run_phase5
from doc3_executor.graph.phase6 import run_phase6
from doc3_executor.graph.phase7 import run_phase7
from doc3_executor.capabilities.ledger_interpreter import interpret_ledger
from doc3_executor.schemas.models import RunState

rs = RunState(run_id='run_interpreter_ops', trace_id='trace_interpreter_ops')
run_phase1(rs, 'Нужен план поиска: почему люди бросают онлайн-курсы')
run_phase2(rs)
run_phase3(rs)
run_phase4(rs)
run_phase5(rs)
hid = rs.promoted['phase4_hypothesis_lattice']['hypotheses'][0]['hypothesis_id']
run_phase6(rs, [{
    'source_id': 's1',
    'linked_hypotheses': [hid],
    'url_or_doi': 'https://example.org/s1',
    'section': 'results',
    'span': 'p3',
    'claim': 'Higher cognitive load increases dropout risk.',
    'evidence_type': 'case_study',
    'supports_or_challenges': 'supports',
}])
run_phase7(rs)

view = interpret_ledger(rs)
print('authoritative_ready=', view['synthesis_readiness']['authoritative_ready'])
print('blocking_reasons=', view['synthesis_readiness']['blocking_reasons'])
print('next_actions=', view['next_actions'])
print('open_contradictions=', view['open_contradictions'])
PY
```

### Triage policy по результатам interpreter
1. `authoritative_ready=False` и есть `unchecked`:
   - выполнить/добавить claim validation;
   - повторно проверить interpreter view;
   - затем запускать `phase8_finalizer`.
2. Есть `open_contradictions`:
   - провести contradiction review;
   - зафиксировать adjudication/статус;
   - повторно проверить readiness.
3. Нет блокеров:
   - переход к finalization (Phase 8).

### Инварианты оператора
- Нельзя использовать interpreter для promotion/verification действий.
- Любые изменения состояния проходят через phase/gate flow.
- Interpreter используется только как диагностический и explainability слой.

---

## 35) Жизненный цикл тестов: что в Dev/CI, а что в Runtime

### Runtime (использование workflow)
При обычном запуске executor выполняется только протокол:
- Phase nodes;
- Gate checks;
- Promotion/Decision events;
- Finalization/output generation.

`pytest` в runtime path не вызывается.

### Dev/CI (контур качества)
Тестовые наборы запускаются как quality gates до merge/release:
- `F*` — фазовая корректность;
- `IT*` — сквозная интеграция протокола;
- `OC*` — output contract и delivery invariants.

### Минимальные команды
```bash
# Локальная быстрая проверка фазы
pytest -q tests/test_phase8.py

# Полная фазовая проверка цепочки
pytest -q tests/test_phase1.py tests/test_phase2.py tests/test_phase3.py tests/test_phase4.py tests/test_phase5.py tests/test_phase6.py tests/test_phase7.py tests/test_phase8.py

# Output contract / интеграция (по мере реализации)
pytest -q tests/test_*.py
```

### Release policy
Изменения в phase/gate/finalizer/interpreter считаются готовыми к релизу только после зелёного CI на обязательных наборах `F*`, `IT*`, `OC*`.

---

## 36) Сквозные интеграционные тесты A–J (статус и запуск)

После реализации `tests/test_integration.py` сквозные сценарии A–J выполняются как единый интеграционный контур качества.

### Что покрывается
- `IT.A.ZeroKnowledgeInput`
- `IT.B.NoRetrievalBeforeDesign`
- `IT.C.SourceGroupSeparation`
- `IT.D.ContradictionPreservation`
- `IT.E.SynthesisRefusalWithoutProvenance`
- `IT.F.ReferenceLeakageGuards`
- `IT.G.ReopenAndInvalidateFlow`
- `IT.H.Auditability`
- `IT.I.InterpreterReadOnlyAuditView`
- `IT.J.FinalizerOutcomeMatrix`

### Как запускать
```bash
pytest -q tests/test_integration.py
```

### Полный регрессионный запуск
```bash
pytest -q
```

### Ожидаемый operational результат
- все интеграционные тесты зелёные;
- поведение протокола подтверждено на сквозной цепочке фазы 1→8;
- output/finalizer/invalidation/auditability сценарии проверены как единый workflow-контур.
