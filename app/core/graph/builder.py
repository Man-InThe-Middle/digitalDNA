from __future__ import annotations


def build_graph(data):

    candidate = data["candidate"]
    resolution = data["resolution"]

    nodes = []
    edges = []

    person_id = str(candidate.id)

    # -----------------------------------------
    # PERSON
    # -----------------------------------------

    nodes.append({
        "id": person_id,
        "type": "person",
        "label": candidate.name,
        "status": resolution.status.value,
        "score": resolution.score,
    })

    organizations = {}
    projects = {}
    events = {}

    # -----------------------------------------
    # PROFILES
    # -----------------------------------------

    for profile in candidate.profiles:

        profile_id = str(profile.id)

        nodes.append({

            "id": profile_id,

            "type": "account",

            "label":
                profile.platform,

            "username":
                profile.username,

            "url":
                str(profile.url)
                if profile.url
                else None,
        })

        # Evidence originating from this source
        source_evidence = [
            str(e.id)
            for e in candidate.evidence
            if e.source_url == profile.url
        ]

        # PERSON → ACCOUNT

        edges.append({

            "source_entity":
                person_id,

            "relationship":
                "IDENTITY_LINK",

            "target_entity":
                profile_id,

            "evidence_ids":
                source_evidence[:4],

            "confidence":
                round(
                    resolution.score / 100,
                    3
                ),
        })

        # -------------------------------------
        # ORGANIZATION
        # -------------------------------------

        if profile.organization:

            key = (
                profile.organization
                .casefold()
                .strip()
            )

            if key not in organizations:

                organization_id = (
                    f"org-{len(organizations)+1}"
                )

                organizations[key] = (
                    organization_id
                )

                nodes.append({

                    "id":
                        organization_id,

                    "type":
                        "organization",

                    "label":
                        profile.organization,
                })

            edges.append({

                "source_entity":
                    profile_id,

                "relationship":
                    "AFFILIATED_WITH",

                "target_entity":
                    organizations[key],

                "evidence_ids": [
                    str(e.id)
                    for e in candidate.evidence
                    if (
                        e.source_url == profile.url
                        and
                        e.signal_type
                        == "organization_overlap"
                    )
                ][:3],

                "confidence":
                    0.90,
            })

        # -------------------------------------
        # PROJECTS
        # -------------------------------------

        metadata = profile.metadata or {}

        repos = metadata.get("repos", [])

        if isinstance(repos, list):

            for repo in repos:

                key = str(repo).casefold()

                if key not in projects:

                    project_id = (
                        f"project-{len(projects)+1}"
                    )

                    projects[key] = project_id

                    nodes.append({

                        "id":
                            project_id,

                        "type":
                            "project",

                        "label":
                            str(repo),
                    })

                edges.append({

                    "source_entity":
                        profile_id,

                    "relationship":
                        "CONTRIBUTES_TO",

                    "target_entity":
                        projects[key],

                    "evidence_ids":
                        source_evidence[:2],

                    "confidence":
                        0.82,
                })

        # -------------------------------------
        # EVENTS
        # -------------------------------------

        event_name = (
            metadata.get("event")
            or
            metadata.get("event_name")
        )

        if event_name:

            key = (
                str(event_name)
                .casefold()
            )

            if key not in events:

                event_id = (
                    f"event-{len(events)+1}"
                )

                events[key] = event_id

                nodes.append({

                    "id":
                        event_id,

                    "type":
                        "event",

                    "label":
                        str(event_name),
                })

            edges.append({

                "source_entity":
                    profile_id,

                "relationship":
                    "PARTICIPATED_IN",

                "target_entity":
                    events[key],

                "evidence_ids":
                    source_evidence[:2],

                "confidence":
                    0.80,
            })

    return {
        "nodes": nodes,
        "edges": edges,
    }