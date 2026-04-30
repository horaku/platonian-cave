from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class VerificationLedgerResult:
    verification_ledger: Dict


def build_verification_ledger(run_state_promoted: Dict, phase6_payload: Dict, run_id: str) -> VerificationLedgerResult:
    claims = []
    for ext in phase6_payload.get("extractions", []):
        claim_id = f"claim_{ext['extraction_id']}"
        claims.append(
            {
                "claim_id": claim_id,
                "claim_text": ext.get("extracted_claim", ""),
                "status": "proposed",
                "source_links": [
                    {
                        "source_id": ext.get("source_id"),
                        "extraction_id": ext.get("extraction_id"),
                        "locator": ext.get("source_locator", {}).get("url_or_doi", ""),
                    }
                ],
                "validation_status": {
                    "factual_consistency": "unchecked",
                    "citation_alignment": "unchecked",
                    "semantic_stability": "unchecked",
                },
                "contradictions": [],
                "decision_history": [
                    {"action": "proposed", "actor": "agent", "reason": "imported from extraction proposal"}
                ],
            }
        )

    ledger = {
        "run_id": run_id,
        "promoted_state": {
            "problem_surface_id": "phase1_intent_surface",
            "working_lexicon_id": "phase3_terminology_normalization",
            "hypothesis_lattice_id": "phase4_hypothesis_lattice",
            "source_discovery_plan_id": "phase5_source_discovery_design",
        },
        "claim_records": claims,
    }
    return VerificationLedgerResult(verification_ledger=ledger)
