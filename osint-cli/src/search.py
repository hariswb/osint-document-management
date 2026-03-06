"""Web search module using DuckDuckGo."""

from dataclasses import dataclass
from typing import List, Optional
from duckduckgo_search import DDGS


@dataclass
class SearchResult:
    """Represents a search result."""

    title: str
    href: str
    body: str
    source: str = "duckduckgo"
    score: Optional[float] = None


class SearchEngine:
    """DuckDuckGo-based search engine."""

    def __init__(self, max_results: int = 10, region: str = "id-id"):
        """
        Initialize the search engine.

        Args:
            max_results: Maximum number of results to return
            region: Region code (default: id-id for Indonesia)
        """
        self.max_results = max_results
        self.region = region
        self.ddgs = DDGS()

    def search(
        self, query: str, max_results: Optional[int] = None
    ) -> List[SearchResult]:
        """
        Perform a web search using DuckDuckGo.

        Args:
            query: Search query string
            max_results: Override default max_results

        Returns:
            List of SearchResult objects
        """
        max_res = max_results or self.max_results

        try:
            results = self.ddgs.text(
                query, region=self.region, safesearch="off", max_results=max_res
            )

            return [
                SearchResult(
                    title=r.get("title", ""),
                    href=r.get("href", ""),
                    body=r.get("body", ""),
                    source="duckduckgo",
                )
                for r in results
            ]
        except Exception as e:
            print(f"Search error: {e}")
            return []

    def search_news(
        self, query: str, max_results: Optional[int] = None
    ) -> List[SearchResult]:
        """
        Search for news articles using DuckDuckGo.

        Args:
            query: Search query string
            max_results: Override default max_results

        Returns:
            List of SearchResult objects
        """
        max_res = max_results or self.max_results

        try:
            results = self.ddgs.news(
                query, region=self.region, safesearch="off", max_results=max_res
            )

            return [
                SearchResult(
                    title=r.get("title", ""),
                    href=r.get("url", ""),
                    body=r.get("body", ""),
                    source="duckduckgo_news",
                )
                for r in results
            ]
        except Exception as e:
            print(f"News search error: {e}")
            return []
