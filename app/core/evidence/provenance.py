from __future__ import annotations

from collections import defaultdict
from app.models.domain import Evidence


def group_evidence(evidence: list[Evidence]) -> dict[str, list[Evidence]]:
    grouped: dict[str, list[Evidence]] = defaultdict(list)
    for item in evidence:
        grouped[item.signal_type].append(item)
    return dict(grouped)


def independent_source_count(evidence: list[Evidence]) -> int:
    urls = {str(item.source_url) for item in evidence if item.source_url}
    return len(urls)
