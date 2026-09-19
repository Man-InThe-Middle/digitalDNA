from __future__ import annotations
from hashlib import sha256
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
import httpx
from app.models.domain import ProfileRecord, SourceType

SOCIAL_HOSTS = {"github.com":"GitHub", "linkedin.com":"LinkedIn", "instagram.com":"Instagram", "x.com":"X", "twitter.com":"X", "youtube.com":"YouTube"}

class PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.description = ""
        self.links: list[str] = []
        self._title = False
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "title": self._title = True
        if tag == "meta" and (attrs.get("name") or "").lower() in {"description", "og:description"}:
            self.description = attrs.get("content") or self.description
        if tag == "a" and attrs.get("href"): self.links.append(attrs["href"])
    def handle_data(self, data):
        if self._title: self.title += data
    def handle_endtag(self, tag):
        if tag == "title": self._title = False

class WebsiteEnricher:
    name = "website_enrichment"
    def __init__(self, timeout: float = 8.0, max_pages: int = 8):
        self.timeout, self.max_pages = timeout, max_pages
    @staticmethod
    def _is_candidate(profile: ProfileRecord) -> bool:
        if not profile.url: return False
        host = urlparse(str(profile.url)).netloc.lower().removeprefix("www.")
        return profile.source_type in {SourceType.SEARCH, SourceType.WEBSITE} and host not in SOCIAL_HOSTS
    async def enrich(self, profiles: list[ProfileRecord]) -> list[ProfileRecord]:
        candidates = [p for p in profiles if self._is_candidate(p)][:self.max_pages]
        if not candidates: return []
        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True, headers={"User-Agent":"DigitalDNA/2.0"}) as client:
            for profile in candidates:
                try:
                    response = await client.get(str(profile.url))
                    response.raise_for_status()
                    if "text/html" not in response.headers.get("content-type", ""): continue
                    body = response.content[:1_000_000]
                    parser = PageParser(); parser.feed(body.decode("utf-8", errors="ignore"))
                    links=[]
                    for raw in parser.links:
                        absolute=urljoin(str(profile.url), raw)
                        host=urlparse(absolute).netloc.lower().removeprefix("www.")
                        if host in SOCIAL_HOSTS: links.append(absolute)
                    profile.metadata.update({
                        "page_title":" ".join(parser.title.split())[:300],
                        "page_description":" ".join(parser.description.split())[:600],
                        "outbound_public_links":sorted(set(links)),
                        "content_sha256":sha256(body).hexdigest(),
                    })
                    if links: profile.metadata["explicit_cross_links"] = True
                except (httpx.HTTPError, ValueError):
                    continue
        return profiles
