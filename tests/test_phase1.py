from doc3_executor.graph.executor import run_phase1
from doc3_executor.schemas.models import GateDecision, RunState


def test_f1_core_functionality():
    rs = RunState(run_id="run_1", trace_id="trace_1")
    out = run_phase1(rs, "Хочу понять, как лучше искать материалы про то, почему люди бросают сложные онлайн-курсы")

    assert len(out.proposals) == 1
    payload = out.proposals[0].payload
    assert payload["stated_request"].startswith("Хочу понять")
    assert payload["candidate_interpretations"]
    assert "no_domain_lock_in" in payload["prohibited_moves"]


def test_f1_gate_invariants_revise_on_domain_lock_in():
    rs = RunState(run_id="run_2", trace_id="trace_2")
    out = run_phase1(rs, "Это задача из HCI, как оптимально искать источники")

    assert out.events[-1].decision == GateDecision.REVISE
    assert "lock-in" in out.events[-1].reason
    assert "phase1_intent_surface" not in out.promoted


def test_f1_crossphase_promoted_is_only_input_for_next_phase_baseline():
    rs = RunState(run_id="run_3", trace_id="trace_3")
    out = run_phase1(rs, "Помоги сформулировать задачу поиска материалов")

    assert out.events[-1].decision == GateDecision.PROMOTE
    promoted = out.promoted.get("phase1_intent_surface")
    assert promoted is not None
    assert promoted == out.proposals[0].payload
