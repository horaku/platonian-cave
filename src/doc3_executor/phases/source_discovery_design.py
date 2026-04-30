from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class SourceDiscoveryPlanResult:
    by_hypothesis: List[Dict]


def build_source_discovery_plan(hypothesis_lattice: Dict, working_lexicon: Dict) -> SourceDiscoveryPlanResult:
    preferred_terms = [f.get("preferred_term") for f in working_lexicon.get("term_families", [])]
    plans = []
    for h in hypothesis_lattice.get("hypotheses", []):
        hid = h["hypothesis_id"]
        plans.append(
            {
                "hypothesis_id": hid,
                "source_groups": [
                    {
                        "group": "academic",
                        "epistemic_role": "empirical evidence and definitions",
                        "unique_evidence_expected": ["peer-reviewed findings", "validated methods"],
                        "limitations": ["publication lag", "domain jargon"],
                    },
                    {
                        "group": "practitioner",
                        "epistemic_role": "field heuristics and implementation patterns",
                        "unique_evidence_expected": ["operational playbooks", "failure anecdotes"],
                        "limitations": ["anecdotal bias"],
                    },
                ],
                "query_families": [
                    {
                        "query_family_id": f"qf_{hid}_core",
                        "purpose": "retrieve core definitions and causal evidence",
                        "seed_terms": [t for t in preferred_terms if t in h.get("linked_lexicon_terms", [])],
                        "expansion_terms": ["factors", "predictors", "interventions"],
                        "negative_filters": ["marketing", "employee attrition"],
                        "search_ready_queries": [
                            f"{h.get('framing')} causes systematic review",
                            f"{' '.join(h.get('linked_lexicon_terms', []))} empirical study",
                        ],
                        "expected_evidence_types": ["definition", "method", "case_study", "critique"],
                    }
                ],
            }
        )

    return SourceDiscoveryPlanResult(by_hypothesis=plans)
