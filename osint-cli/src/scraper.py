"""Web scraping module using Scrapling."""

import re
import time
from dataclasses import dataclass
from typing import List, Optional
from urllib.parse import urljoin, urlparse
import httpx
from bs4 import BeautifulSoup


@dataclass
class ScrapedArticle:
    """Represents a scraped article."""

    url: str
    title: str
    content: str
    author: Optional[str] = None
    publish_date: Optional[str] = None
    word_count: int = 0
    relevance_score: float = 0.0


class AdaptiveScraper:
    """Adaptive web scraper with anti-bot bypass capabilities."""

    def __init__(self, delay: float = 1.0, timeout: int = 30):
        """
        Initialize the scraper.

        Args:
            delay: Delay between requests in seconds
            timeout: Request timeout in seconds
        """
        self.delay = delay
        self.timeout = timeout
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
        }

    def scrape(self, url: str) -> Optional[ScrapedArticle]:
        """
        Scrape a single URL.

        Args:
            url: URL to scrape

        Returns:
            ScrapedArticle or None if failed
        """
        try:
            time.sleep(self.delay)

            with httpx.Client(
                timeout=self.timeout, headers=self.headers, follow_redirects=True
            ) as client:
                response = client.get(url)
                response.raise_for_status()

                return self._parse_html(url, response.text)
        except Exception as e:
            print(f"Error scraping {url}: {e}")
            return None

    def scrape_multiple(self, urls: List[str]) -> List[ScrapedArticle]:
        """
        Scrape multiple URLs.

        Args:
            urls: List of URLs to scrape

        Returns:
            List of successfully scraped articles
        """
        articles = []
        for url in urls:
            article = self.scrape(url)
            if article:
                articles.append(article)
        return articles

    def _parse_html(self, url: str, html: str) -> ScrapedArticle:
        """Parse HTML content and extract article data."""
        soup = BeautifulSoup(html, "lxml")

        # Extract title
        title = self._extract_title(soup)

        # Extract content
        content = self._extract_content(soup)

        # Extract author
        author = self._extract_author(soup)

        # Extract publish date
        publish_date = self._extract_date(soup)

        # Calculate word count
        word_count = len(content.split())

        return ScrapedArticle(
            url=url,
            title=title,
            content=content,
            author=author,
            publish_date=publish_date,
            word_count=word_count,
            relevance_score=0.0,
        )

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract article title."""
        # Try common title selectors
        selectors = [
            "h1.article-title",
            "h1.entry-title",
            "h1.post-title",
            "h1",
            '[property="og:title"]',
            "title",
        ]

        for selector in selectors:
            elem = soup.select_one(selector)
            if elem:
                if selector == '[property="og:title"]':
                    content = elem.get("content")
                    return str(content) if content else ""
                return elem.get_text(strip=True)

        return ""

    def _extract_content(self, soup: BeautifulSoup) -> str:
        """Extract article content."""
        # Remove unwanted elements
        for elem in soup(
            ["script", "style", "nav", "header", "footer", "aside", "advertisement"]
        ):
            elem.decompose()

        # Try common content selectors
        selectors = [
            "article",
            '[class*="article-content"]',
            '[class*="entry-content"]',
            '[class*="post-content"]',
            '[class*="content-body"]',
            "main",
            ".content",
            "#content",
        ]

        for selector in selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                # Get paragraphs
                paragraphs = content_elem.find_all("p")
                if paragraphs:
                    text = "\n\n".join(
                        p.get_text(strip=True)
                        for p in paragraphs
                        if len(p.get_text(strip=True)) > 20
                    )
                    if len(text) > 200:
                        return self._clean_text(text)

        # Fallback: get all paragraphs
        paragraphs = soup.find_all("p")
        text = "\n\n".join(
            p.get_text(strip=True)
            for p in paragraphs
            if len(p.get_text(strip=True)) > 20
        )
        return self._clean_text(text)

    def _extract_author(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract article author."""
        selectors = [
            '[class*="author"]',
            '[class*="byline"]',
            '[rel="author"]',
            '[name="author"]',
        ]

        for selector in selectors:
            elem = soup.select_one(selector)
            if elem:
                if selector == '[name="author"]':
                    content = elem.get("content")
                    return str(content) if content else None
                return elem.get_text(strip=True)

        return None

    def _extract_date(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract publish date."""
        selectors = [
            '[property="article:published_time"]',
            '[property="og:updated_time"]',
            '[class*="date"]',
            '[class*="published"]',
            "time",
        ]

        for selector in selectors:
            elem = soup.select_one(selector)
            if elem:
                if selector in [
                    '[property="article:published_time"]',
                    '[property="og:updated_time"]',
                ]:
                    content = elem.get("content")
                    return str(content) if content else None
                datetime = elem.get("datetime")
                if datetime:
                    return str(datetime)
                return elem.get_text(strip=True)

        return None

    def _clean_text(self, text: str) -> str:
        """Clean extracted text."""
        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text)
        # Remove special characters
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]", "", text)
        # Remove excessive newlines
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()
