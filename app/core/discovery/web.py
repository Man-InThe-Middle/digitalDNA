from __future__ import annotations

from typing import Any

import httpx

from .base import DiscoveryProvider


class WebSearchDiscoveryProvider(DiscoveryProvider):
    """Public web discovery using DuckDuckGo's HTML results."""

    name = "web"

    async def discover(self, query: str) -> list[dict[str, Any]]:
        query = query.strip()
        if not query:
            return []

        url = "https://html.duckduckgo.com/html/"

        try:
            async with httpx.AsyncClient(
                timeout=15.0,
                follow_redirects=True,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 Chrome/120 Safari/537.36"
                    )
                },
            ) as client:
                response = await client.post(
                    url,
                    data={"q": query},
                )
                response.raise_for_status()

        except (httpx.HTTPError, httpx.TimeoutException):
            return []

        from html.parser import HTMLParser

        class ResultParser(HTMLParser):
            def __init__(self) -> None:
                super().__init__()
                self.results: list[dict[str, Any]] = []
                self._current: dict[str, Any] | None = None
                self._capture_title = False
                self._capture_snippet = False

            def handle_starttag(
                self,
                tag: str,
                attrs: list[tuple[str, str | None]],
            ) -> None:
                attributes = dict(attrs)

                if tag == "a" and "result__a" in attributes.get("class", ""):
                    self._current = {
                        "title": "",
                        "url": attributes.get("href", ""),
                        "snippet": "",
                        "source": "duckduckgo",
                        "provider": "web",
                    }
                    self._capture_title = True

                elif (
                    tag == "a"
                    and self._current is not None
                    and "result__snippet" in attributes.get("class", "")
                ):
                    self._capture_snippet = True

            def handle_data(self, data: str) -> None:
                if self._current is None:
                    return

                if self._capture_title:
                    self._current["title"] += data.strip()

                elif self._capture_snippet:
                    self._current["snippet"] += data.strip()

            def handle_endtag(self, tag: str) -> None:
                if tag == "a":
                    if self._capture_title:
                        self._capture_title = False

                    elif self._capture_snippet:
                        self._capture_snippet = False

                        if self._current:
                            self.results.append(self._current)
                            self._current = None

        parser = ResultParser()
        parser.feed(response.text)

        return parser.results[:20]