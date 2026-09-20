from .base import DiscoveryQuery, DiscoveryProvider
from .github import GitHubDiscoveryProvider
from .web import BingWebDiscoveryProvider, DuckDuckGoWebDiscoveryProvider

# Backward-compatible alias for older imports
WebSearchDiscoveryProvider = DuckDuckGoWebDiscoveryProvider

__all__ = [
    "DiscoveryQuery",
    "DiscoveryProvider",
    "GitHubDiscoveryProvider",
    "BingWebDiscoveryProvider",
    "DuckDuckGoWebDiscoveryProvider",
    "WebSearchDiscoveryProvider",
]