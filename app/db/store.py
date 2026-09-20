from __future__ import annotations
import json
import sqlite3
from pathlib import Path
from typing import Any
from uuid import UUID
from app.models.domain import Entity, EntityRelationship, Investigation

DB_PATH = Path("digitaldna.db")


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, default=str)


class Store:
    """SQLite persistence for investigations plus their first-class entity graph."""

    def __init__(self, path: Path = DB_PATH):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.init()

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def init(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS investigations (
                    id TEXT PRIMARY KEY,
                    subject_label TEXT NOT NULL,
                    context TEXT,
                    authorized INTEGER NOT NULL,
                    discovery_mode TEXT NOT NULL DEFAULT 'demo',
                    image_sha256 TEXT,
                    image_name TEXT,
                    created_at TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'created',
                    result_json TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_investigations_created ON investigations(created_at DESC);

                CREATE TABLE IF NOT EXISTS entities (
                    id TEXT PRIMARY KEY,
                    investigation_id TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    label TEXT NOT NULL,
                    canonical_url TEXT,
                    aliases_json TEXT NOT NULL,
                    source_ids_json TEXT NOT NULL,
                    evidence_ids_json TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    first_seen TEXT NOT NULL,
                    last_seen TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    FOREIGN KEY(investigation_id) REFERENCES investigations(id) ON DELETE CASCADE
                );
                CREATE INDEX IF NOT EXISTS idx_entities_investigation ON entities(investigation_id);
                CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(investigation_id, entity_type);

                CREATE TABLE IF NOT EXISTS entity_relationships (
                    id TEXT PRIMARY KEY,
                    investigation_id TEXT NOT NULL,
                    from_entity_id TEXT NOT NULL,
                    to_entity_id TEXT NOT NULL,
                    relation_type TEXT NOT NULL,
                    evidence_ids_json TEXT NOT NULL,
                    source_ids_json TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    observed_at TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    FOREIGN KEY(investigation_id) REFERENCES investigations(id) ON DELETE CASCADE,
                    FOREIGN KEY(from_entity_id) REFERENCES entities(id) ON DELETE CASCADE,
                    FOREIGN KEY(to_entity_id) REFERENCES entities(id) ON DELETE CASCADE
                );
                CREATE INDEX IF NOT EXISTS idx_entity_edges_investigation ON entity_relationships(investigation_id);
                """
            )
            columns = {row[1] for row in conn.execute("PRAGMA table_info(investigations)").fetchall()}
            if "discovery_mode" not in columns:
                conn.execute("ALTER TABLE investigations ADD COLUMN discovery_mode TEXT NOT NULL DEFAULT 'demo'")

    def save_investigation(self, inv: Investigation, status: str = "created") -> None:
        with self.connect() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO investigations
                (id, subject_label, context, authorized, discovery_mode, image_sha256, image_name, created_at, status, result_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, COALESCE((SELECT result_json FROM investigations WHERE id = ?), NULL))""",
                (str(inv.id), inv.subject_label, inv.context, int(inv.authorized), inv.discovery_mode,
                 inv.image_sha256, inv.image_name, inv.created_at.isoformat(), status, str(inv.id)),
            )

    def set_status(self, investigation_id: UUID, status: str) -> None:
        with self.connect() as conn:
            conn.execute("UPDATE investigations SET status=? WHERE id=?", (status, str(investigation_id)))

    def set_result(self, investigation_id: UUID, result: dict[str, Any], status: str = "complete") -> None:
        with self.connect() as conn:
            conn.execute(
                "UPDATE investigations SET status=?, result_json=? WHERE id=?",
                (status, _json(result), str(investigation_id)),
            )

    def replace_entity_graph(self, investigation_id: UUID, entities: list[Entity], relationships: list[EntityRelationship]) -> None:
        inv_id = str(investigation_id)
        with self.connect() as conn:
            conn.execute("DELETE FROM entity_relationships WHERE investigation_id=?", (inv_id,))
            conn.execute("DELETE FROM entities WHERE investigation_id=?", (inv_id,))
            conn.executemany(
                """INSERT INTO entities
                (id, investigation_id, entity_type, label, canonical_url, aliases_json, source_ids_json,
                 evidence_ids_json, confidence, first_seen, last_seen, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                [(
                    str(e.id), inv_id, e.type.value, e.label, str(e.canonical_url) if e.canonical_url else None,
                    _json([str(x) for x in e.aliases]), _json([str(x) for x in e.source_ids]),
                    _json([str(x) for x in e.evidence_ids]), e.confidence, e.first_seen.isoformat(),
                    e.last_seen.isoformat(), _json(e.metadata),
                ) for e in entities],
            )
            conn.executemany(
                """INSERT INTO entity_relationships
                (id, investigation_id, from_entity_id, to_entity_id, relation_type, evidence_ids_json,
                 source_ids_json, confidence, observed_at, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                [(
                    str(r.id), inv_id, str(r.from_entity_id), str(r.to_entity_id), r.relation_type.value,
                    _json([str(x) for x in r.evidence_ids]), _json([str(x) for x in r.source_ids]),
                    r.confidence, r.observed_at.isoformat(), _json(r.metadata),
                ) for r in relationships],
            )

    def get_entity_graph(self, investigation_id: UUID) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        inv_id = str(investigation_id)
        with self.connect() as conn:
            entity_rows = conn.execute("SELECT * FROM entities WHERE investigation_id=? ORDER BY entity_type, label", (inv_id,)).fetchall()
            rel_rows = conn.execute("SELECT * FROM entity_relationships WHERE investigation_id=? ORDER BY relation_type", (inv_id,)).fetchall()
        entities = []
        for row in entity_rows:
            entities.append({
                "id": row["id"], "type": row["entity_type"], "label": row["label"], "canonical_url": row["canonical_url"],
                "aliases": json.loads(row["aliases_json"]), "source_ids": json.loads(row["source_ids_json"]),
                "evidence_ids": json.loads(row["evidence_ids_json"]), "confidence": row["confidence"],
                "first_seen": row["first_seen"], "last_seen": row["last_seen"], "metadata": json.loads(row["metadata_json"]),
            })
        relationships = []
        for row in rel_rows:
            relationships.append({
                "id": row["id"], "from_entity_id": row["from_entity_id"], "to_entity_id": row["to_entity_id"],
                "relation_type": row["relation_type"], "evidence_ids": json.loads(row["evidence_ids_json"]),
                "source_ids": json.loads(row["source_ids_json"]), "confidence": row["confidence"],
                "observed_at": row["observed_at"], "metadata": json.loads(row["metadata_json"]),
            })
        return entities, relationships

    def get(self, investigation_id: UUID) -> tuple[Investigation, str, dict[str, Any] | None] | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM investigations WHERE id=?", (str(investigation_id),)).fetchone()
        if not row:
            return None
        inv = Investigation.model_validate({
            "id": row["id"], "subject_label": row["subject_label"], "context": row["context"],
            "authorized": bool(row["authorized"]), "discovery_mode": row["discovery_mode"] or "demo",
            "image_sha256": row["image_sha256"], "image_name": row["image_name"], "created_at": row["created_at"],
        })
        result = json.loads(row["result_json"]) if row["result_json"] else None
        return inv, row["status"], result

    def list_recent(self, limit: int = 20) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT id, subject_label, authorized, created_at, status FROM investigations ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]


store = Store()
