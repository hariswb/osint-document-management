"""Text processing and article ranking module."""

import re
import math
from typing import Dict, List, Set
from collections import Counter


class TextProcessor:
    """Process and clean text content."""

    # Common Indonesian stop words
    STOP_WORDS = {
        "yang",
        "di",
        "ke",
        "dari",
        "pada",
        "dalam",
        "untuk",
        "dengan",
        "dan",
        "atau",
        "adalah",
        "ini",
        "itu",
        "dapat",
        "dapatkan",
        "akan",
        "telah",
        "sudah",
        "saya",
        "anda",
        "dia",
        "mereka",
        "kita",
        "kami",
        "bukan",
        "tidak",
        "juga",
        "saja",
        "tetapi",
        "namun",
        "seperti",
        "oleh",
        "sebagai",
        "saat",
        "karena",
        "jika",
        "agar",
        "supaya",
        "bagi",
        "pada",
        "antara",
        "sejak",
        "hingga",
        "sampai",
        "tentang",
        "terhadap",
        "kepada",
    }

    def __init__(self):
        pass

    def clean_text(self, text: str) -> str:
        """
        Clean and normalize text.

        Args:
            text: Raw text

        Returns:
            Cleaned text
        """
        if not text:
            return ""

        # Convert to lowercase
        text = text.lower()

        # Remove URLs
        text = re.sub(r"https?://\S+|www\.\S+", "", text)

        # Remove email addresses
        text = re.sub(r"\S+@\S+", "", text)

        # Remove phone numbers
        text = re.sub(r"\+?\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", "", text)

        # Remove special characters but keep Indonesian characters
        text = re.sub(r"[^\w\s\-]", " ", text)

        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text)

        return text.strip()

    def extract_keywords(self, text: str, top_n: int = 10) -> List[str]:
        """
        Extract keywords from text.

        Args:
            text: Input text
            top_n: Number of top keywords to return

        Returns:
            List of keywords
        """
        cleaned = self.clean_text(text)
        words = cleaned.split()

        # Filter stop words and short words
        filtered = [w for w in words if w not in self.STOP_WORDS and len(w) > 2]

        # Count frequencies
        word_counts = Counter(filtered)

        # Return top N
        return [word for word, _ in word_counts.most_common(top_n)]

    def tokenize(self, text: str) -> List[str]:
        """Tokenize text into words."""
        cleaned = self.clean_text(text)
        return cleaned.split()


class ArticleRanker:
    """Rank articles based on relevance to query."""

    def __init__(self):
        self.text_processor = TextProcessor()

    def rank_articles(
        self, query: str, articles: List[Dict], top_n: int = 10
    ) -> List[Dict]:
        """
        Rank articles by relevance to query.

        Args:
            query: Search query
            articles: List of article dictionaries with 'title' and 'content' keys
            top_n: Number of top articles to return

        Returns:
            Ranked list of articles with 'relevance_score' added
        """
        if not articles:
            return []

        query_keywords = set(self.text_processor.extract_keywords(query, top_n=20))

        ranked = []
        for article in articles:
            score = self._calculate_relevance(
                query_keywords, article.get("title", ""), article.get("content", "")
            )

            article_copy = article.copy()
            article_copy["relevance_score"] = score
            ranked.append(article_copy)

        # Sort by score (descending)
        ranked.sort(key=lambda x: x["relevance_score"], reverse=True)

        return ranked[:top_n]

    def _calculate_relevance(
        self, query_keywords: Set[str], title: str, content: str
    ) -> float:
        """
        Calculate relevance score for an article.

        Args:
            query_keywords: Set of query keywords
            title: Article title
            content: Article content

        Returns:
            Relevance score (0.0 to 1.0)
        """
        if not query_keywords:
            return 0.0

        title_keywords = set(self.text_processor.extract_keywords(title, top_n=50))
        content_keywords = set(self.text_processor.extract_keywords(content, top_n=100))

        # Title matches are weighted more heavily
        title_matches = len(query_keywords & title_keywords)
        content_matches = len(query_keywords & content_keywords)

        # TF-IDF-like scoring
        title_score = title_matches / len(query_keywords) if query_keywords else 0
        content_score = (
            (content_matches / len(query_keywords) * 0.5) if query_keywords else 0
        )

        # Combine scores (title weighted 2x)
        score = (title_score * 2 + content_score) / 2.5

        # Normalize to 0-1
        return min(score, 1.0)

    def calculate_tf_idf(self, documents: List[str]) -> Dict[str, Dict[str, float]]:
        """
        Calculate TF-IDF scores for a collection of documents.

        Args:
            documents: List of document texts

        Returns:
            Dictionary mapping document index to word scores
        """
        if not documents:
            return {}

        # Tokenize all documents
        tokenized_docs = [self.text_processor.tokenize(doc) for doc in documents]

        # Calculate document frequency for each term
        doc_freq = Counter()
        for tokens in tokenized_docs:
            unique_terms = set(tokens)
            for term in unique_terms:
                doc_freq[term] += 1

        # Calculate TF-IDF for each document
        num_docs = len(documents)
        tf_idf_scores = {}

        for idx, tokens in enumerate(tokenized_docs):
            if not tokens:
                tf_idf_scores[idx] = {}
                continue

            term_freq = Counter(tokens)
            scores = {}

            for term, freq in term_freq.items():
                tf = freq / len(tokens)
                idf = math.log(num_docs / (doc_freq[term] + 1)) + 1
                scores[term] = tf * idf

            tf_idf_scores[idx] = scores

        return tf_idf_scores
