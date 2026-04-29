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
