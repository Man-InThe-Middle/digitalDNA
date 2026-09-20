from pathlib import Path

from app.core.entities.extractor import extract_entity_graph
from app.db.store import Store
from app.models.domain import Candidate, Evidence, ProfileRecord, SourceType


def _fixture():
    profile = ProfileRecord(
        platform="GitHub",
        username="alice",
        display_name="Alice Doe",
        url="https://github.com/alice",
        organization="Acme Labs",
        source_type=SourceType.CODE,
        metadata={
            "repo_details": [{"name": "digitaldna", "url": "https://github.com/alice/digitaldna"}],
        },
    )
    evidence = Evidence(
        source_url=profile.url,
        source_type=SourceType.CODE,
        claim="Public GitHub profile belongs to Alice Doe.",
        signal_type="name_match",
        profile_ids=[profile.id],
        reliability=0.9,
        weight=0.8,
    )
    return Candidate(name="Alice Doe", profiles=[profile], evidence=[evidence]), evidence


def test_entity_extraction_creates_core_entities_and_edges():
    candidate, evidence = _fixture()
    entities, relationships = extract_entity_graph(candidate, [evidence])

    types = {entity.type.value for entity in entities}
    relations = {edge.relation_type.value for edge in relationships}

    assert {"PERSON", "ACCOUNT", "ALIAS", "ORGANIZATION", "PROJECT"} <= types
    assert {"HAS_ACCOUNT", "ALIAS_OF", "AFFILIATED_WITH", "CONTRIBUTES_TO"} <= relations
    assert all(edge.evidence_ids for edge in relationships)


def test_entity_store_round_trip(tmp_path: Path):
    candidate, evidence = _fixture()
    entities, relationships = extract_entity_graph(candidate, [evidence])
    store = Store(tmp_path / "digitaldna.db")

    from app.models.domain import Investigation
    investigation = Investigation(subject_label="Alice Doe", authorized=True, discovery_mode="demo")
    store.save_investigation(investigation)
    store.replace_entity_graph(investigation.id, entities, relationships)

    saved_entities, saved_relationships = store.get_entity_graph(investigation.id)
    assert len(saved_entities) == len(entities)
    assert len(saved_relationships) == len(relationships)
    assert any(item["type"] == "PROJECT" for item in saved_entities)
