from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class TriageExtractionResult:
    triage: Dict
    extractions: List[Dict]


def triage_and_extract(retrieved_records: List[Dict], source_discovery_plan: Dict, hypothesis_lattice: Dict) -> TriageExtractionResult:
    include_if = ["contains empirical evidence", "relevant to active hypothesis"]
    exclude_if = ["off topic", "wrong domain", "duplicate"]
    review_bucket_if = ["unclear scope", "missing metadata"]

    active_hids = {h["hypothesis_id"] for h in hypothesis_lattice.get("hypotheses", [])}
    accepted, rejected, review_bucket, extractions = [], [], [], []

    for idx, rec in enumerate(retrieved_records):
        sid = rec["source_id"]
        linked = [hid for hid in rec.get("linked_hypotheses", []) if hid in active_hids]
        if rec.get("inaccessible"):
            rejected.append({"source_id": sid, "reason": "source inaccessible", "rejection_type": "inaccessible"})
            continue
        if not linked:
            rejected.append({"source_id": sid, "reason": "not linked to active hypotheses", "rejection_type": "off_scope"})
            continue
        if rec.get("needs_review"):
            review_bucket.append({"source_id": sid, "uncertainty": "requires manual scope decision"})
            continue

        accepted.append({"source_id": sid, "reason": "matches active hypothesis and has usable evidence", "linked_hypotheses": linked})
        extractions.append(
            {
                "extraction_id": f"ext_{idx}",
                "source_id": sid,
                "source_locator": {
                    "url_or_doi": rec.get("url_or_doi", ""),
                    "section": rec.get("section"),
                    "paragraph_or_span": rec.get("span"),
                },
                "extracted_claim": rec.get("claim", ""),
                "evidence_type": rec.get("evidence_type", "case_study"),
                "linked_hypothesis": linked[0],
                "supports_or_challenges": rec.get("supports_or_challenges", "supports"),
                "uncertainty_flags": rec.get("uncertainty_flags", []),
            }
        )

    return TriageExtractionResult(
        triage={
            "screening_criteria": {
                "include_if": include_if,
                "exclude_if": exclude_if,
                "review_bucket_if": review_bucket_if,
            },
            "accepted_items": accepted,
            "rejected_items": rejected,
            "review_bucket": review_bucket,
        },
        extractions=extractions,
    )
