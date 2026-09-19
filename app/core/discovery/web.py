from __future__ import annotations

from html.parser import HTMLParser
from urllib.parse import quote_plus, urlparse

import httpx

from app.models.domain import ProfileRecord, SourceType
from .base import DiscoveryQuery


class _LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links: list[tuple[str, str]] = []
        self._href: str | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            attrs_dict = dict(attrs)
            self._href = attrs_dict.get("href")
            self._text = []

    def handle_data(self, data):
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag):
        if tag == "a" and self._href:
            text = " ".join("".join(self._text).split())
            self.links.append((self._href, text))
            self._href = None
            self._text = []


PLATFORM_TYPES = {
    "github.com": ("GitHub", SourceType.CODE),
    "linkedin.com": ("LinkedIn", SourceType.PROFESSIONAL),
    "instagram.com": ("Instagram", SourceType.SOCIAL),
    "x.com": ("X", SourceType.SOCIAL),
    "twitter.com": ("X", SourceType.SOCIAL),
    "youtube.com": ("YouTube", SourceType.SOCIAL),
}


class DuckDuckGoWebDiscoveryProvider:
    """Minimal public web-search adapter. No login, cookies, or private data are used."""

    SEARCH_URL = "https://html.duckduckgo.com/html/"

    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout

    async def discover(self, query: DiscoveryQuery) -> list[ProfileRecord]:
        terms = [query.name]
        if query.username:
            terms.append(query.username)
        search = " ".join(t for t in terms if t)
        if not search:
            return []

        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True, headers={"User-Agent": "DigitalDNA/0.2"}) as client:
            response = await client.get(self.SEARCH_URL, params={"q": search})
            response.raise_for_status()

        parser = _LinkParser()
        parser.feed(response.text)
        results: list[ProfileRecord] = []
        seen: set[str] = set()

        for href, title in parser.links:
            if not href.startswith(("http://", "https://")):
                continue
            parsed = urlparse(href)
            host = parsed.netloc.lower().removeprefix("www.")
            platform_info = PLATFORM_TYPES.get(host)
            if not platform_info or href in seen:
                continue
            seen.add(href)
            platform, source_type = platform_info
            username = parsed.path.strip("/").split("/")[0] or None
            results.append(ProfileRecord(
                platform=platform,
                username=username,
                display_name=title or query.name,
                url=href,
                source_type=source_type,
                metadata={"discovery": "web_search", "query": search},
            ))
            if len(results) >= 20:
                break
        return results
