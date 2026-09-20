from __future__ import annotations

import hashlib
import re
from html import unescape
from urllib.parse import urljoin

import httpx

from app.models.domain import Evidence, ProfileRecord, SourceType


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/142.0 Safari/537.36"
)


def _clean_text(value: str) -> str:
    value = unescape(value)
    value = re.sub(r"<script\b[^>]*>.*?</script>", " ", value, flags=re.I | re.S)
    value = re.sub(r"<style\b[^>]*>.*?</style>", " ", value, flags=re.I | re.S)
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def _source_type(profile: ProfileRecord) -> SourceType:
    return profile.source_type


def _hash_content(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _extract_title(html: str) -> str | None:
    match = re.search(
        r"<title[^>]*>(.*?)</title>",
        html,
        flags=re.I | re.S,
    )

    if not match:
        return None

    title = _clean_text(match.group(1))

    return title[:500] if title else None


def _extract_meta(html: str, name: str) -> str | None:
    pattern = (
        r'<meta[^>]+(?:name|property)=["\']'
        + re.escape(name)
        + r'["\'][^>]+content=["\'](.*?)["\']'
    )

    match = re.search(pattern, html, flags=re.I | re.S)

    if not match:
        return None

    value = _clean_text(match.group(1))

    return value[:2000] if value else None


def _extract_dates(text: str) -> list[str]:
    patterns = [
        r"\b20\d{2}-\d{1,2}-\d{1,2}\b",
        r"\b20\d{2}/\d{1,2}/\d{1,2}\b",
        r"\b\d{1,2}/\d{1,2}/20\d{2}\b",
        r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+20\d{2}\b",
        r"\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+20\d{2}\b",
    ]

    found = []

    for pattern in patterns:
        found.extend(re.findall(pattern, text, flags=re.I))

    # Preserve order while removing duplicates.
    output = []
    seen = set()

    for item in found:
        key = item.casefold()

        if key in seen:
            continue

        seen.add(key)
        output.append(item)

    return output[:20]


def _extract_claims(
    profile: ProfileRecord,
    title: str | None,
    description: str | None,
    text: str,
) -> list[Evidence]:

    evidence: list[Evidence] = []

    source_url = profile.url

    if title:
        evidence.append(
            Evidence(
                source_url=source_url,
                source_type=_source_type(profile),
                claim=f"Public page title: {title}",
                excerpt=title[:500],
                signal_type="page_title",
                weight=0.45,
                reliability=0.70,
                provenance={
                    "method": "public_page_metadata",
                },
            )
        )

    if description:
        evidence.append(
            Evidence(
                source_url=source_url,
                source_type=_source_type(profile),
                claim="Public page metadata describes the subject.",
                excerpt=description[:1000],
                signal_type="page_description",
                weight=0.55,
                reliability=0.70,
                provenance={
                    "method": "public_page_metadata",
                },
            )
        )

    if profile.organization:
        evidence.append(
            Evidence(
                source_url=source_url,
                source_type=_source_type(profile),
                claim=f"Source associates the subject with {profile.organization}.",
                excerpt=profile.organization,
                signal_type="organization_overlap",
                weight=0.80,
                reliability=0.75,
                provenance={
                    "method": "profile_field",
                },
            )
        )

    for date in _extract_dates(text):

        # Find a small context window around the date.
        position = text.lower().find(date.lower())

        if position >= 0:
            start = max(0, position - 180)
            end = min(len(text), position + len(date) + 220)
            excerpt = text[start:end]
        else:
            excerpt = date

        evidence.append(
            Evidence(
                source_url=source_url,
                source_type=_source_type(profile),
                claim=f"Public source contains date reference: {date}",
                excerpt=excerpt[:700],
                signal_type="date_reference",
                weight=0.45,
                reliability=0.65,
                provenance={
                    "method": "public_page_text",
                    "date_text": date,
                },
            )
        )

    return evidence


async def enrich_profile(
    profile: ProfileRecord,
) -> tuple[ProfileRecord, list[Evidence]]:

    if not profile.url:
        return profile, []

    url = str(profile.url)

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": (
            "text/html,application/xhtml+xml,"
            "application/xml;q=0.9,*/*;q=0.8"
        ),
    }

    try:
        async with httpx.AsyncClient(
            headers=headers,
            timeout=12,
            follow_redirects=True,
        ) as client:

            response = await client.get(url)

        response.raise_for_status()

    except Exception as exc:
        print(
            f"[DigitalDNA] Enrichment failed for {url}: "
            f"{type(exc).__name__}: {exc}"
        )

        return profile, []

    content = response.content

    # Avoid accidentally processing enormous pages.
    if len(content) > 2_000_000:
        content = content[:2_000_000]

    html = content.decode(
        response.encoding or "utf-8",
        errors="ignore",
    )

    title = _extract_title(html)

    description = (
        _extract_meta(html, "description")
        or _extract_meta(html, "og:description")
    )

    text = _clean_text(html)

    source_hash = _hash_content(content)

    metadata = dict(profile.metadata or {})

    metadata.update({
        "enriched": True,
        "http_status": response.status_code,
        "content_length": len(content),
        "source_hash": source_hash,
        "page_title": title,
        "page_description": description,
        "dates": _extract_dates(text),
    })

    enriched_profile = profile.model_copy(
        update={
            "display_name": (
                profile.display_name
                or title
            ),
            "bio": (
                profile.bio
                or description
            ),
            "metadata": metadata,
        }
    )

    evidence = _extract_claims(
        enriched_profile,
        title,
        description,
        text,
    )

    print(
        f"[DigitalDNA] Enriched {profile.platform} "
        f"{url} → {len(evidence)} evidence item(s)"
    )

    return enriched_profile, evidence


async def enrich_profiles(
    profiles: list[ProfileRecord],
) -> tuple[list[ProfileRecord], list[Evidence]]:

    if not profiles:
        return [], []

    results = []

    for profile in profiles:
        results.append(
            await enrich_profile(profile)
        )

    enriched_profiles = []
    evidence = []

    for enriched, items in results:
        enriched_profiles.append(enriched)
        evidence.extend(items)

    print(
        f"[DigitalDNA] Enrichment complete: "
        f"{len(enriched_profiles)} profile(s), "
        f"{len(evidence)} evidence item(s)"
    )

    return enriched_profiles, evidence  