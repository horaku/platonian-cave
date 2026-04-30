from doc3_executor.graph.executor import run_phase1
from doc3_executor.graph.phase2 import is_phase2_invalidated, run_phase2
from doc3_executor.schemas.models import GateDecision, RunState


def test_f2_core_functionality():
    rs = RunState(run_id="run_f2_1", trace_id="trace_f2_1")
    run_phase1(rs, "Хочу понять, как лучше искать материалы про то, почему люди бросают сложные онлайн-курсы")
    out = run_phase2(rs)

    proposal = out.proposals[-1]
    assert proposal.phase == "phase2_vocabulary_bootstrap"
    payload = proposal.payload
    fragment = payload["by_surface_fragment"][0]
    assert fragment["candidate_professional_terms"]
    assert fragment["searchable_paraphrases"]
    assert fragment["nearby_but_confusable_terms"]


def test_f2_gate_invariants_block_premature_preferred_term():
    rs = RunState(run_id="run_f2_2", trace_id="trace_f2_2")
    run_phase1(rs, "Хочу понять, как лучше искать материалы")
    out = run_phase2(rs)

    # mutate last proposal as if phase violated contract
    out.proposals[-1].payload["by_surface_fragment"][0]["preferred_term"] = "retention"
    from doc3_executor.gates.phase2_gate import review_phase2

    decision, reason = review_phase2(out.proposals[-1].payload)
    assert decision == GateDecision.REVISE
    assert "premature normalization" in reason


def test_f2_crossphase_compatibility_invalidation_on_phase1_change():
    rs = RunState(run_id="run_f2_3", trace_id="trace_f2_3")
    run_phase1(rs, "Помоги сформулировать задачу поиска материалов")
    run_phase2(rs)
    assert is_phase2_invalidated(rs) is False

    # simulate changed promoted phase1
    rs.promoted["phase1_intent_surface"]["stated_request"] = "Совершенно другой запрос"
    assert is_phase2_invalidated(rs) is True
