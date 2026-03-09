"""Entity resolution and deduplication module."""

import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from difflib import SequenceMatcher


@dataclass
class EntityMatch:
    """Represents a potential entity match."""

    entity_id: int
    name: str
    similarity: float
    match_type: str  # 'exact', 'fuzzy', 'substring', 'initials'


class EntityResolver:
    """Resolves and deduplicates entities using fuzzy matching."""

    def __init__(self, similarity_threshold: float = 0.85):
        self.similarity_threshold = similarity_threshold
        self.common_suffixes = [
            "pt",
            "tbk",
            "limited",
            "ltd",
            "inc",
            "corp",
            "corporation",
            "company",
            "co",
            "group",
            "holding",
            "international",
            "indonesia",
        ]
        self.common_prefixes = ["pt", "cv", "pd", "ud", "yayasan", "koperasi"]

    def normalize_name(self, name: str) -> str:
        """Normalize entity name for comparison."""
        # Convert to lowercase
        normalized = name.lower()

        # Remove common organizational suffixes
        for suffix in self.common_suffixes:
            normalized = re.sub(rf"\s+{suffix}\b", "", normalized)

        # Remove common prefixes
        for prefix in self.common_prefixes:
            normalized = re.sub(rf"^{prefix}\s+", "", normalized)

        # Remove extra whitespace and special characters
        normalized = re.sub(r"[^\w\s]", " ", normalized)
        normalized = re.sub(r"\s+", " ", normalized).strip()

        return normalized

    def calculate_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between two entity names."""
        norm1 = self.normalize_name(name1)
        norm2 = self.normalize_name(name2)

        # Exact match after normalization
        if norm1 == norm2:
            return 1.0

        # Check for substring match
        if norm1 in norm2 or norm2 in norm1:
            min_len = min(len(norm1), len(norm2))
            max_len = max(len(norm1), len(norm2))
            return min_len / max_len

        # Fuzzy match using SequenceMatcher
        similarity = SequenceMatcher(None, norm1, norm2).ratio()

        return similarity

    def find_matches(
        self, query_name: str, candidates: List[Tuple[int, str]], top_k: int = 5
    ) -> List[EntityMatch]:
        """Find matching entities from a list of candidates."""
        matches = []

        for entity_id, candidate_name in candidates:
            similarity = self.calculate_similarity(query_name, candidate_name)

            if similarity >= self.similarity_threshold:
                match_type = self._classify_match(
                    query_name, candidate_name, similarity
                )
                matches.append(
                    EntityMatch(
                        entity_id=entity_id,
                        name=candidate_name,
                        similarity=similarity,
                        match_type=match_type,
                    )
                )

        # Sort by similarity (descending)
        matches.sort(key=lambda x: x.similarity, reverse=True)

        return matches[:top_k]

    def _classify_match(self, name1: str, name2: str, similarity: float) -> str:
        """Classify the type of match."""
        norm1 = self.normalize_name(name1)
        norm2 = self.normalize_name(name2)

        if norm1 == norm2:
            return "exact"
        elif norm1 in norm2 or norm2 in norm1:
            return "substring"
        elif similarity >= 0.95:
            return "near_exact"
        else:
            return "fuzzy"

    def should_merge(self, name1: str, name2: str) -> Tuple[bool, float]:
        """Determine if two entities should be merged."""
        similarity = self.calculate_similarity(name1, name2)
        should_merge = similarity >= self.similarity_threshold
        return should_merge, similarity

    def extract_initials(self, name: str) -> str:
        """Extract initials from a name."""
        words = self.normalize_name(name).split()
        return "".join(word[0] for word in words if word)

    def find_alias_candidates(
        self, entities: List[Tuple[int, str, str]]
    ) -> List[Tuple[int, int, float]]:
        """Find potential alias pairs from a list of entities.

        Args:
            entities: List of (id, name, entity_type) tuples

        Returns:
            List of (entity1_id, entity2_id, confidence) tuples
        """
        alias_pairs = []

        # Group by entity type for more accurate matching
        by_type: Dict[str, List[Tuple[int, str]]] = {}
        for entity_id, name, entity_type in entities:
            if entity_type not in by_type:
                by_type[entity_type] = []
            by_type[entity_type].append((entity_id, name))

        # Find matches within each type
        for entity_type, type_entities in by_type.items():
            for i, (id1, name1) in enumerate(type_entities):
                for id2, name2 in type_entities[i + 1 :]:
                    similarity = self.calculate_similarity(name1, name2)
                    if similarity >= self.similarity_threshold:
                        alias_pairs.append((id1, id2, similarity))

        return alias_pairs

    def suggest_canonical_name(self, names: List[str]) -> str:
        """Suggest a canonical name from a list of aliases."""
        if not names:
            return ""

        # Prefer the longest name (usually the most complete)
        # but also consider frequency if we had that data
        return max(names, key=len)


class AliasManager:
    """Manages entity aliases and canonical names."""

    def __init__(self, db_manager):
        self.db = db_manager
        self.resolver = EntityResolver()

    def create_alias(
        self, entity_id: int, alias_name: str, confidence: float = 1.0
    ) -> int:
        """Create a new alias for an entity."""
        self.db.conn.execute(
            """
            INSERT INTO entity_aliases (entity_id, alias_name, confidence)
            VALUES (?, ?, ?)
            ON CONFLICT (entity_id, alias_name) DO UPDATE SET
                confidence = excluded.confidence,
                created_at = CURRENT_TIMESTAMP
            """,
            (entity_id, alias_name, confidence),
        )
        self.db.conn.commit()
        result = self.db.conn.execute(
            "SELECT currval('entity_aliases_id_seq')"
        ).fetchone()
        return result[0]

    def get_aliases(self, entity_id: int) -> List[Dict]:
        """Get all aliases for an entity."""
        results = self.db.conn.execute(
            """
            SELECT id, alias_name, confidence, created_at
            FROM entity_aliases
            WHERE entity_id = ?
            ORDER BY confidence DESC, created_at DESC
            """,
            (entity_id,),
        ).fetchall()

        return [
            {
                "id": row[0],
                "alias_name": row[1],
                "confidence": row[2],
                "created_at": str(row[3]),
            }
            for row in results
        ]

    def find_duplicates(self) -> List[Dict]:
        """Find potential duplicate entities across the database."""
        # Get all entities
        results = self.db.conn.execute(
            """
            SELECT id, name, entity_type
            FROM entities
            ORDER BY entity_type, name
            """
        ).fetchall()

        entities = [(row[0], row[1], row[2]) for row in results]

        # Find potential duplicates
        duplicates = self.resolver.find_alias_candidates(entities)

        # Build response with entity details
        duplicate_groups = []
        processed = set()

        for id1, id2, confidence in duplicates:
            if id1 in processed or id2 in processed:
                continue

            # Get entity details
            entity1 = self.db.conn.execute(
                "SELECT id, name, entity_type FROM entities WHERE id = ?", (id1,)
            ).fetchone()
            entity2 = self.db.conn.execute(
                "SELECT id, name, entity_type FROM entities WHERE id = ?", (id2,)
            ).fetchone()

            if entity1 and entity2:
                duplicate_groups.append(
                    {
                        "entity1": {
                            "id": entity1[0],
                            "name": entity1[1],
                            "type": entity1[2],
                        },
                        "entity2": {
                            "id": entity2[0],
                            "name": entity2[1],
                            "type": entity2[2],
                        },
                        "confidence": confidence,
                        "suggested_action": "merge" if confidence > 0.95 else "review",
                    }
                )
                processed.add(id1)
                processed.add(id2)

        return duplicate_groups

    def merge_entities(self, target_id: int, source_id: int) -> bool:
        """Merge source entity into target entity."""
        try:
            # Add source name as alias of target
            source_name = self.db.conn.execute(
                "SELECT name FROM entities WHERE id = ?", (source_id,)
            ).fetchone()

            if source_name:
                self.create_alias(target_id, source_name[0], confidence=1.0)

            # Update relationships to point to target
            self.db.conn.execute(
                """
                UPDATE relationships
                SET source_entity_id = ?
                WHERE source_entity_id = ?
                """,
                (target_id, source_id),
            )

            self.db.conn.execute(
                """
                UPDATE relationships
                SET target_entity_id = ?
                WHERE target_entity_id = ?
                """,
                (target_id, source_id),
            )

            # Update entity mentions in documents
            self.db.conn.execute(
                """
                UPDATE entity_mentions
                SET entity_id = ?
                WHERE entity_id = ?
                """,
                (target_id, source_id),
            )

            # Delete source entity
            self.db.conn.execute("DELETE FROM entities WHERE id = ?", (source_id,))

            self.db.conn.commit()
            return True
        except Exception as e:
            print(f"Error merging entities: {e}")
            self.db.conn.rollback()
            return False
