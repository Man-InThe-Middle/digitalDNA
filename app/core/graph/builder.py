from __future__ import annotations

from app.models.domain import EntityRelation


def _source_evidence(candidate, profile):
    return [
        str(e.id)
        for e in candidate.evidence
        if e.source_url == profile.url
    ]


def build_graph(data):
    candidate = data["candidate"]
    resolution = data["resolution"]

    nodes = []
    edges = []

    person_id = str(candidate.id)
    resolution_confidence = round(resolution.score / 100, 3)

    # ---------------------------------------------------------
    # PERSON
    # ---------------------------------------------------------

    nodes.append({
        "id": person_id,
        "type": "person",
        "label": candidate.name,
        "status": resolution.status.value,
        "score": resolution.score,
        "confidence": resolution_confidence,
    })

    organizations = {}
    projects = {}
    events = {}
    publications = {}
    aliases = {}

    # ---------------------------------------------------------
    # PROFILES / RELATIONSHIPS
    # ---------------------------------------------------------

    for profile in candidate.profiles:

        metadata = profile.metadata or {}

        profile_id = str(profile.id)

        evidence_ids = _source_evidence(
            candidate,
            profile,
        )

        # ACCOUNT
        nodes.append({
            "id": profile_id,
            "type": "account",
            "label": profile.platform,
            "username": profile.username,
            "url": str(profile.url) if profile.url else None,
            "confidence": resolution_confidence,
            "metadata": metadata,
        })

        edges.append({
            "source_entity": person_id,
            "relationship": EntityRelation.HAS_ACCOUNT.value,
            "target_entity": profile_id,
            "evidence_ids": evidence_ids[:5],
            "confidence": resolution_confidence,
        })

        # -----------------------------------------------------
        # ALIAS
        # -----------------------------------------------------

        if profile.username:

            alias_key = profile.username.casefold().strip()

            if alias_key not in aliases:

                alias_id = f"alias-{len(aliases) + 1}"
                aliases[alias_key] = alias_id

                nodes.append({
                    "id": alias_id,
                    "type": "alias",
                    "label": f"@{profile.username}",
                    "confidence": 0.85,
                })

            edges.append({
                "source_entity": aliases[alias_key],
                "relationship": EntityRelation.ALIAS_OF.value,
                "target_entity": person_id,
                "evidence_ids": evidence_ids[:3],
                "confidence": 0.85,
            })

        # -----------------------------------------------------
        # ORGANIZATION
        # -----------------------------------------------------

        if profile.organization:

            key = profile.organization.casefold().strip()

            if key not in organizations:

                organization_id = (
                    f"org-{len(organizations) + 1}"
                )

                organizations[key] = organization_id

                nodes.append({
                    "id": organization_id,
                    "type": "organization",
                    "label": profile.organization,
                    "confidence": 0.90,
                })

            organization_evidence = [
                str(e.id)
                for e in candidate.evidence
                if (
                    e.source_url == profile.url
                    and e.signal_type == "organization_overlap"
                )
            ]

            edges.append({
                "source_entity": person_id,
                "relationship": EntityRelation.AFFILIATED_WITH.value,
                "target_entity": organizations[key],
                "evidence_ids": organization_evidence[:4],
                "confidence": 0.90,
            })

        # -----------------------------------------------------
        # PROJECTS
        # -----------------------------------------------------

        projects_list = metadata.get("projects", [])

        if isinstance(projects_list, list):

            for project in projects_list:

                if not project:
                    continue

                key = str(project).casefold().strip()

                if key not in projects:

                    project_id = (
                        f"project-{len(projects) + 1}"
                    )

                    projects[key] = project_id

                    nodes.append({
                        "id": project_id,
                        "type": "project",
                        "label": str(project),
                        "confidence": 0.82,
                    })

                edges.append({
                    "source_entity": person_id,
                    "relationship": EntityRelation.CONTRIBUTES_TO.value,
                    "target_entity": projects[key],
                    "evidence_ids": evidence_ids[:3],
                    "confidence": 0.82,
                })

        # -----------------------------------------------------
        # EVENTS
        # -----------------------------------------------------

        events_list = metadata.get("events", [])

        if isinstance(events_list, list):

            for event in events_list:

                if not event:
                    continue

                key = str(event).casefold().strip()

                if key not in events:

                    event_id = (
                        f"event-{len(events) + 1}"
                    )

                    events[key] = event_id

                    nodes.append({
                        "id": event_id,
                        "type": "event",
                        "label": str(event),
                        "confidence": 0.80,
                    })

                edges.append({
                    "source_entity": person_id,
                    "relationship": EntityRelation.PARTICIPATED_IN.value,
                    "target_entity": events[key],
                    "evidence_ids": evidence_ids[:3],
                    "confidence": 0.80,
                })

        # -----------------------------------------------------
        # PUBLICATIONS
        # -----------------------------------------------------

        publications_list = metadata.get(
            "publications",
            [],
        )

        if isinstance(publications_list, list):

            for publication in publications_list:

                if not publication:
                    continue

                key = str(publication).casefold().strip()

                if key not in publications:

                    publication_id = (
                        f"publication-{len(publications) + 1}"
                    )

                    publications[key] = publication_id

                    nodes.append({
                        "id": publication_id,
                        "type": "publication",
                        "label": str(publication),
                        "confidence": 0.80,
                    })

                edges.append({
                    "source_entity": person_id,
                    "relationship": EntityRelation.AUTHORED.value,
                    "target_entity": publications[key],
                    "evidence_ids": evidence_ids[:3],
                    "confidence": 0.80,
                })

    return {
        "nodes": nodes,
        "edges": edges,
    }