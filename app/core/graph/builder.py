from app.models.domain import Candidate, GraphResponse, Relationship


def build_graph(candidates: list[Candidate]) -> GraphResponse:
    nodes = []
    edges = []
    for candidate in candidates:
        nodes.append({"id": str(candidate.id), "type": "person", "label": candidate.name})
        for profile in candidate.profiles:
            pid = str(profile.id)
            nodes.append({"id": pid, "type": "profile", "label": profile.platform, "username": profile.username})
            edges.append(
                Relationship(
                    source_entity=str(candidate.id),
                    relationship="HAS_PUBLIC_PROFILE",
                    target_entity=pid,
                    evidence_ids=[e.id for e in candidate.evidence],
                    confidence=0.8,
                )
            )
    return GraphResponse(nodes=nodes, edges=edges)
