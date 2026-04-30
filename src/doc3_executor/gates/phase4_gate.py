from __future__ import annotations

from doc3_executor.schemas.models import GateDecision


def _signature(h: dict) -> tuple:
    return (
        h.get("framing", "").strip().lower(),
        tuple(sorted(h.get("linked_lexicon_terms", []))),
        tuple(sorted(h.get("type", []))),
    )


def review_phase4(hypothesis_payload: dict):
    hypotheses = hypothesis_payload.get("hypotheses", [])
    if not hypotheses:
        return GateDecision.REJECT, "no hypotheses"

    seen_ids = set()
    seen_signatures = set()
    for h in hypotheses:
        hid = h.get("hypothesis_id")
        if not hid:
            return GateDecision.REJECT, "missing hypothesis_id"
        if hid in seen_ids:
            return GateDecision.REVISE, "duplicate hypothesis_id"
        seen_ids.add(hid)

        sig = _signature(h)
        if sig in seen_signatures:
            return GateDecision.REVISE, "non-differentiable hypotheses"
        seen_signatures.add(sig)

        if not h.get("linked_intent_fragments"):
            return GateDecision.REVISE, "missing linked_intent_fragments"
        if not h.get("linked_lexicon_terms"):
            return GateDecision.REVISE, "missing linked_lexicon_terms"
        if not h.get("evidence_needed"):
            return GateDecision.REVISE, "missing evidence_needed"
        if not h.get("would_be_falsified_by"):
            return GateDecision.REVISE, "missing falsification conditions"
        if h.get("do_not_rank_yet") is not True:
            return GateDecision.REVISE, "do_not_rank_yet must be true"

    return GateDecision.PROMOTE, "phase4 lattice satisfies differentiation gate"
