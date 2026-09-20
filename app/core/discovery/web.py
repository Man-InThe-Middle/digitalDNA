from __future__ import annotations

import re
from html import unescape
from urllib.parse import quote, urlparse
import xml.etree.ElementTree as ET

import httpx

from app.models.domain import ProfileRecord, SourceType


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/142.0 Safari/537.36"
)


PLATFORM_MAP = {
    "linkedin.com": ("LinkedIn", SourceType.PROFESSIONAL),
    "instagram.com": ("Instagram", SourceType.SOCIAL),
    "x.com": ("X", SourceType.SOCIAL),
    "twitter.com": ("X", SourceType.SOCIAL),
    "youtube.com": ("YouTube", SourceType.SOCIAL),
    "youtu.be": ("YouTube", SourceType.SOCIAL),
    "github.com": ("GitHub", SourceType.CODE),
    "facebook.com": ("Facebook", SourceType.SOCIAL),
    "medium.com": ("Medium", SourceType.PUBLICATION),
    "substack.com": ("Substack", SourceType.PUBLICATION),
    "researchgate.net": ("ResearchGate", SourceType.PUBLICATION),
}


def _platform_for_url(url: str) -> tuple[str, SourceType]:
    host = urlparse(url).netloc.lower().removeprefix("www.")

    for domain, value in PLATFORM_MAP.items():
        if host == domain or host.endswith("." + domain):
            return value

    return "Web", SourceType.WEBSITE


def _clean_url(url: str | None) -> str | None:
    if not url:
        return None

    url = unescape(url).strip()

    if not url.startswith(("http://", "https://")):
        return None

    return url


def _extract_username(url: str, platform: str) -> str | None:
    if platform == "LinkedIn":
        match = re.search(r"/in/([^/?#]+)", url, re.I)
        return match.group(1) if match else None

    if platform in {"Instagram", "X", "GitHub", "Facebook"}:
        path = urlparse(url).path.strip("/")
        if path and "/" not in path:
            return path

    if platform == "YouTube":
        match = re.search(r"/(?:@|channel/|c/|user/)([^/?#]+)", url, re.I)
        return match.group(1) if match else None

    return None


def _make_profile(
    *,
    title: str,
    url: str,
    description: str,
) -> ProfileRecord:

    platform, source_type = _platform_for_url(url)
    username = _extract_username(url, platform)

    clean_title = re.sub(r"\s+", " ", unescape(title)).strip()
    clean_description = re.sub(
        r"\s+",
        " ",
        unescape(description),
    ).strip()

    metadata = {
        "search_title": clean_title,
        "search_description": clean_description,
        "discovery_source": "bing_rss",
    }

    # Pull obvious organization signals from snippets.
    organization = None

    organization_patterns = [
        r"\b(?:at|works at|working at|from)\s+([A-Z][A-Za-z0-9&.,' -]{2,80})",
        r"\b([A-Z][A-Za-z0-9&.,' -]{2,80})\s+(?:employee|founder|co-founder|director|CEO)\b",
    ]

    for pattern in organization_patterns:
        match = re.search(
            pattern,
            clean_description,
            re.I,
        )

        if match:
            organization = match.group(1).strip(" .,")
            break

    # Detect project / publication / event hints from the search result.
    combined = f"{clean_title} {clean_description}"

    projects = []
    publications = []
    events = []

    if re.search(
        r"\b(project|built|developed|created|launched|startup|repository|repo)\b",
        combined,
        re.I,
    ):
        projects.append(clean_title)

    if re.search(
        r"\b(paper|publication|published|journal|research|article)\b",
        combined,
        re.I,
    ):
        publications.append(clean_title)

    if re.search(
        r"\b(conference|summit|hackathon|workshop|webinar|event|speaker|panel)\b",
        combined,
        re.I,
    ):
        events.append(clean_title)

    metadata["projects"] = projects
    metadata["publications"] = publications
    metadata["events"] = events

    return ProfileRecord(
        platform=platform,
        username=username,
        display_name=clean_title or None,
        url=url,
        bio=clean_description or None,
        organization=organization,
        source_type=source_type,
        metadata=metadata,
    )


def _dedupe(profiles: list[ProfileRecord]) -> list[ProfileRecord]:
    seen = set()
    output = []

    for profile in profiles:
        key = (
            profile.platform.casefold(),
            (profile.username or "").casefold(),
            str(profile.url or "").casefold(),
        )

        if key in seen:
            continue

        seen.add(key)
        output.append(profile)

    return output


class BingWebDiscoveryProvider:

    name = "bing"

    async def discover(self, query) -> list[ProfileRecord]:

        search_query = f'"{query.name}"'

        url = (
            "https://www.bing.com/search"
            f"?q={quote(search_query)}"
            "&format=rss"
            "&mkt=en-US"
        )

        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "application/rss+xml, application/xml, text/xml",
        }

        async with httpx.AsyncClient(
            headers=headers,
            timeout=15,
            follow_redirects=True,
        ) as client:

            response = await client.get(url)

        print(f"[DigitalDNA] Bing RSS HTTP {response.status_code}")
        print(
            f"[DigitalDNA] Bing RSS payload: "
            f"{len(response.content)} bytes"
        )

        response.raise_for_status()

        try:
            root = ET.fromstring(response.content)
        except ET.ParseError as exc:
            print(
                f"[DigitalDNA] Bing RSS XML parse failed: "
                f"{type(exc).__name__}: {exc}"
            )
            return []

        profiles = []

        for item in root.findall(".//item"):

            title = item.findtext("title") or ""
            link = item.findtext("link") or ""
            description = item.findtext("description") or ""

            link = _clean_url(link)

            if not link:
                continue

            profiles.append(
                _make_profile(
                    title=title,
                    url=link,
                    description=description,
                )
            )

        profiles = _dedupe(profiles)

        print(
            f"[DigitalDNA] Bing RSS discovered "
            f"{len(profiles)} result(s)"
        )

        return profiles


class DuckDuckGoWebDiscoveryProvider:

    name = "duckduckgo"

    async def discover(self, query) -> list[ProfileRecord]:

        search_query = quote(f'"{query.name}"')

        url = (
            "https://html.duckduckgo.com/html/"
            f"?q={search_query}"
        )

        headers = {
            "User-Agent": USER_AGENT,
        }

        try:
            async with httpx.AsyncClient(
                headers=headers,
                timeout=10,
                follow_redirects=True,
            ) as client:

                response = await client.get(url)

            response.raise_for_status()

        except Exception as exc:
            print(
                f"[DigitalDNA] DuckDuckGo FAILED: "
                f"{type(exc).__name__}: {exc}"
            )
            return []

        html = response.text

        results = []

        pattern = re.compile(
            r'class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
            re.I | re.S,
        )

        for match in pattern.finditer(html):

            result_url = unescape(match.group(1))
            title = re.sub(
                r"<[^>]+>",
                "",
                unescape(match.group(2)),
            )

            result_url = _clean_url(result_url)

            if not result_url:
                continue

            results.append(
                _make_profile(
                    title=title,
                    url=result_url,
                    description="",
                )
            )

        results = _dedupe(results)

        print(
            f"[DigitalDNA] DuckDuckGo discovered "
            f"{len(results)} result(s)"
        )

        return results