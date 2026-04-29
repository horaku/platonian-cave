from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class HypothesisLatticeResult:
    hypotheses: List[Dict]


def build_hypothesis_lattice(problem_surface: Dict, working_lexicon: Dict) -> HypothesisLatticeResult:
    terms = []
    for family in working_lexicon.get("term_families", []):
        terms.append(family.get("preferred_term"))

    hypotheses = [
        {
            "hypothesis_id": "h_retention_factors",
            "framing": "Dropout driven by weak engagement and workload mismatch.",
            "type": ["workflow_problem", "retrieval_problem"],
            "linked_intent_fragments": [problem_surface.get("stated_request", "")[:40]],
            "linked_lexicon_terms": [t for t in terms if t in {"dropout", "retention"}],
            "evidence_needed": ["comparative studies on dropout factors", "definitions of retention vs dropout"],
            "would_be_falsified_by": ["evidence that workload and engagement do not correlate with dropout"],
            "do_not_rank_yet": True,
        },
        {
            "hypothesis_id": "h_search_strategy_gap",
            "framing": "Low recall caused by terminology mismatch in query design.",
            "type": ["retrieval_problem", "representation_problem"],
            "linked_intent_fragments": ["как искать материалы"],
            "linked_lexicon_terms": [t for t in terms if t in {"information retrieval", "dropout", "retention"}],
            "evidence_needed": ["query reformulation patterns", "missed-term analysis"],
            "would_be_falsified_by": ["evidence that terminology choice does not affect recall"],
            "do_not_rank_yet": True,
        },
    ]

    return HypothesisLatticeResult(hypotheses=hypotheses)
