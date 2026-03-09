"""Web search module supporting multiple search engines."""

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
    """Multi-engine search supporting DuckDuckGo and Google."""

    def __init__(
        self, max_results: int = 10, region: str = "id-id", provider: str = "duckduckgo"
    ):
        """
        Initialize the search engine.

        Args:
            max_results: Maximum number of results to return
            region: Region code (default: id-id for Indonesia)
            provider: Search provider - "duckduckgo" or "google"
        """
        self.max_results = max_results
        self.region = region
        self.provider = provider
        # Create fresh DDGS instance for each search to avoid session issues

    def search(
        self, query: str, max_results: Optional[int] = None
    ) -> List[SearchResult]:
        """
        Perform a web search using the configured provider.

        Args:
            query: Search query string
            max_results: Override default max_results

        Returns:
            List of SearchResult objects
        """
        if self.provider.lower() == "google":
            return self._search_google(query, max_results)
        else:
            return self._search_duckduckgo(query, max_results)

    def _search_duckduckgo(
        self, query: str, max_results: Optional[int] = None
    ) -> List[SearchResult]:
        """Perform a web search using DuckDuckGo with retry logic."""
        max_res = max_results or self.max_results
        import time

        # Try multiple times to get better results
        max_retries = 3
        best_results = []

        for attempt in range(max_retries):
            try:
                # Create fresh DDGS instance for each attempt
                ddgs = DDGS()

                results = list(
                    ddgs.text(
                        query,
                        region=self.region,
                        max_results=max_res * 2,  # Get extra results
                    )
                )

                if not results:
                    continue

                # Score results by relevance
                query_words = set(query.lower().split())
                scored_results = []

                for r in results:
                    title = r.get("title", "").lower()
                    body = r.get("body", "").lower()

                    # Calculate relevance score
                    score = sum(
                        1 for word in query_words if word in title or word in body
                    )

                    # Bonus for title matches
                    title_score = sum(2 for word in query_words if word in title)
                    score += title_score

                    if score > 0:  # Only include relevant results
                        scored_results.append((score, r))

                # Sort by score
                scored_results.sort(key=lambda x: x[0], reverse=True)

                # If we got good results, return them
                if scored_results:
                    relevant_results = [r for score, r in scored_results[:max_res]]

                    # If we have enough high-quality results, return them
                    if len(relevant_results) >= max_res // 2:
                        return [
                            SearchResult(
                                title=r.get("title", ""),
                                href=r.get("href", ""),
                                body=r.get("body", ""),
                                source="duckduckgo",
                            )
                            for r in relevant_results
                        ]

                # Keep best results so far
                if scored_results and (
                    not best_results or scored_results[0][0] > best_results[0][0]
                ):
                    best_results = scored_results

                # Small delay between retries
                if attempt < max_retries - 1:
                    time.sleep(0.5)

            except Exception as e:
                print(f"DuckDuckGo search attempt {attempt + 1} error: {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)
                continue

        # Return best results we got
        if best_results:
            return [
                SearchResult(
                    title=r.get("title", ""),
                    href=r.get("href", ""),
                    body=r.get("body", ""),
                    source="duckduckgo",
                )
                for score, r in best_results[:max_res]
            ]

        return []

    def _search_google(
        self, query: str, max_results: Optional[int] = None
    ) -> List[SearchResult]:
        """Perform a web search using Google (via scraping)."""
        max_res = max_results or self.max_results

        try:
            # Try to use googlesearch-python if available
            try:
                from googlesearch import search as google_search

                results = []
                for url in google_search(
                    query, num_results=max_res, lang=self.region[:2]
                ):
                    results.append(
                        SearchResult(
                            title=url,  # googlesearch doesn't provide titles
                            href=url,
                            body="",  # googlesearch doesn't provide snippets
                            source="google",
                        )
                    )
                return results
            except ImportError:
                # Fallback to a simple implementation using requests and BeautifulSoup
                return self._search_google_fallback(query, max_res)
        except Exception as e:
            print(f"Google search error: {e}")
            # Fallback to DuckDuckGo
            print("Falling back to DuckDuckGo...")
            return self._search_duckduckgo(query, max_results)

    def _search_google_fallback(
        self, query: str, max_results: int
    ) -> List[SearchResult]:
        """Fallback Google search using httpx/BeautifulSoup."""
        import httpx
        from bs4 import BeautifulSoup
        from urllib.parse import quote_plus

        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
            }

            search_url = (
                f"https://www.google.com/search?q={quote_plus(query)}&num={max_results}"
            )

            with httpx.Client(
                headers=headers, timeout=10, follow_redirects=True
            ) as client:
                response = client.get(search_url)
                response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            results = []

            # Try multiple selectors for Google results
            selectors = [
                "div.g",  # Standard results
                "div[data-ved]",  # Alternative format
                ".yuRUbf",  # Another format
            ]

            for selector in selectors:
                items = soup.select(selector)
                for item in items[:max_results]:
                    # Try to find link and title
                    link_elem = item.select_one("a[href]")
                    title_elem = item.select_one("h3") or item.select_one(".DKV0Md")
                    snippet_elem = item.select_one(".VwiC3b") or item.select_one(
                        ".s3v94d"
                    )

                    if link_elem:
                        href = link_elem.get("href", "")
                        # Clean up the URL
                        if href.startswith("/url?q="):
                            href = href.split("/url?q=")[1].split("&")[0]

                        title = title_elem.get_text(strip=True) if title_elem else href
                        body = snippet_elem.get_text(strip=True) if snippet_elem else ""

                        if href and not href.startswith("/"):
                            results.append(
                                SearchResult(
                                    title=title,
                                    href=href,
                                    body=body,
                                    source="google",
                                )
                            )

                if results:
                    break

            return results[:max_results]

        except Exception as e:
            print(f"Google fallback search error: {e}")
            return []

    def search_news(
        self, query: str, max_results: Optional[int] = None
    ) -> List[SearchResult]:
        """
        Search for news articles.

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
