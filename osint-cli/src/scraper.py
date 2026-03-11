"""Web scraping module using Scrapling for HTTP and stealthy browser fetching."""

import re
from dataclasses import dataclass
from typing import List, Optional
from urllib.parse import urlparse
from scrapling.fetchers import Fetcher, StealthyFetcher


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
    """Adaptive web scraper with anti-bot bypass using Scrapling fetchers."""

    def __init__(self, timeout: int = 30):
        """
        Initialize the scraper.

        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout

    def scrape(self, url: str) -> Optional[ScrapedArticle]:
        """
        Scrape a single URL with fallback to StealthyFetcher for JS-heavy sites.

        Args:
            url: URL to scrape

        Returns:
            ScrapedArticle or None if failed
        """
        article = self._scrape_http(url)
        if article:
            return article

        print(f"HTTP scraping failed for {url}, trying StealthyFetcher fallback...")
        article = self._scrape_stealthy(url)
        if article:
            return article

        return None

    def _scrape_http(self, url: str) -> Optional[ScrapedArticle]:
        """Scrape using Scrapling's Fetcher for HTTP requests."""
        try:
            page = Fetcher().get(url, stealthy_headers=True, timeout=self.timeout)

            article = self._parse_scrapling_page(url, page)

            if article and len(article.content.strip()) > 100:
                return article
            else:
                print(
                    f"HTTP scrape returned insufficient content ({len(article.content) if article else 0} chars)"
                )
                return None

        except Exception as e:
            print(f"HTTP scraping error for {url}: {e}")
            return None

    def _scrape_stealthy(self, url: str) -> Optional[ScrapedArticle]:
        """Scrape using Scrapling's StealthyFetcher for JavaScript-heavy sites."""
        try:
            page = StealthyFetcher.fetch(
                url, headless=True, network_idle=True, timeout=self.timeout * 1000
            )

            article = self._parse_scrapling_page(url, page)

            if article and len(article.content.strip()) > 100:
                print(
                    f"StealthyFetcher successfully scraped {len(article.content)} chars"
                )
                return article
            else:
                print(
                    f"StealthyFetcher returned insufficient content ({len(article.content) if article else 0} chars)"
                )
                return None

        except Exception as e:
            print(f"StealthyFetcher scraping error for {url}: {e}")
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

    def _parse_scrapling_page(self, url: str, page) -> ScrapedArticle:
        """Parse Scrapling page object and extract article data."""
        title = self._extract_title(page)
        content = self._extract_content(page)
        author = self._extract_author(page)
        publish_date = self._extract_date(page)
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

    def _extract_title(self, page) -> str:
        """Extract article title."""
        # Prefer OG title (attribute-based, needs XPath)
        og = page.xpath('//meta[@property="og:title"]/@content').get()
        if og:
            return str(og).strip()

        for selector in ["h1.article-title", "h1.entry-title", "h1.post-title", "h1", "title"]:
            elems = page.css(selector)
            if elems:
                text = elems[0].get_all_text().strip()
                if text:
                    return text

        return ""

    def _extract_content(self, page) -> str:
        """Extract article content."""
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
            content_elems = page.css(selector)
            if content_elems:
                paragraphs = content_elems[0].css("p")
                if paragraphs:
                    texts = [
                        p.get_all_text().strip()
                        for p in paragraphs
                        if len(p.get_all_text().strip()) > 20
                    ]
                    text = "\n\n".join(texts)
                    if len(text) > 200:
                        return self._clean_text(text)

        # Fallback: collect all paragraphs on the page
        texts = [
            p.get_all_text().strip()
            for p in page.css("p")
            if len(p.get_all_text().strip()) > 20
        ]
        return self._clean_text("\n\n".join(texts))

    def _extract_author(self, page) -> Optional[str]:
        """Extract article author."""
        # Prefer meta name=author (attribute-based)
        meta = page.xpath('//meta[@name="author"]/@content').get()
        if meta:
            return str(meta).strip()

        for selector in ['[class*="author"]', '[class*="byline"]', '[rel="author"]']:
            elems = page.css(selector)
            if elems:
                text = elems[0].get_all_text().strip()
                if text:
                    return text

        return None

    def _extract_date(self, page) -> Optional[str]:
        """Extract publish date."""
        # Try meta properties first (attribute-based)
        for xpath in [
            '//meta[@property="article:published_time"]/@content',
            '//meta[@property="og:updated_time"]/@content',
            '//time/@datetime',
        ]:
            val = page.xpath(xpath).get()
            if val:
                return str(val).strip()

        # Fallback: text from date/time elements
        for selector in ['[class*="date"]', '[class*="published"]', "time"]:
            elems = page.css(selector)
            if elems:
                text = elems[0].get_all_text().strip()
                if text:
                    return text

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


def extract_domain(url: str) -> str:
    """Extract domain from URL."""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc
        # Remove www. prefix if present
        if domain.startswith("www."):
            domain = domain[4:]
        return domain
    except Exception:
        return ""
