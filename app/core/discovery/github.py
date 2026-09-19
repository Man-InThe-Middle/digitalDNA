from __future__ import annotations

import httpx

from app.models.domain import ProfileRecord, SourceType
from .base import DiscoveryQuery


class GitHubDiscoveryProvider:
    """Public GitHub discovery adapter. It only reads public GitHub API data."""

    BASE_URL = "https://api.github.com"

    def __init__(self, token: str | None = None, timeout: float = 10.0):
        self.token = token
        self.timeout = timeout

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    async def discover(self, query: DiscoveryQuery) -> list[ProfileRecord]:
        search_terms = []
        if query.username:
            search_terms.append(query.username)
        if query.name:
            search_terms.append(query.name)
        if not search_terms:
            return []

        async with httpx.AsyncClient(timeout=self.timeout, headers=self._headers(), follow_redirects=True) as client:
            response = await client.get(f"{self.BASE_URL}/search/users", params={"q": " ".join(search_terms), "per_page": 10})
            response.raise_for_status()
            users = response.json().get("items", [])

            profiles: list[ProfileRecord] = []
            for item in users[:10]:
                login = item.get("login")
                if not login:
                    continue
                detail = await client.get(f"{self.BASE_URL}/users/{login}")
                if detail.status_code != 200:
                    continue
                data = detail.json()
                profiles.append(ProfileRecord(
                    platform="GitHub",
                    username=data.get("login"),
                    display_name=data.get("name"),
                    url=data.get("html_url"),
                    bio=data.get("bio"),
                    organization=data.get("company"),
                    location=data.get("location"),
                    source_type=SourceType.CODE,
                    metadata={"avatar_url": data.get("avatar_url"), "public_repos": data.get("public_repos", 0)},
                ))
            return profiles
