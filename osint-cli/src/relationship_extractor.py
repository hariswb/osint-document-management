"""Relationship extraction module for entity relationships."""

import re
import math
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class ExtractedRelationship:
    """Represents an extracted relationship."""

    source_text: str
    target_text: str
    source_type: str
    target_type: str
    relationship_type: str
    confidence: float
    evidence: str
    sentence_context: str


class RelationshipExtractor:
    """Extracts relationships between entities from text."""

    def __init__(self):
        # Relationship patterns for Indonesian text
        self.patterns = {
            "employment": [
                r"(\w+(?:\s+\w+){0,4})\s+(?:adalah|merupakan|sebagai|menjadi|bekerja sebagai)\s+(?:\w+\s+)*(?: CEO | direktur | manajer | pegawai | staf | karyawan | pejabat | pimpinan | ketua )[^.]*?(?:\s+dari|\s+di)\s+(\w+(?:\s+\w+){0,4})",
                r"(\w+(?:\s+\w+){0,4})\s+(?:memimpin|memimpin|mengelola|menjabat)\s+(?:\w+\s+)*(?:di|pada|dalam)\s+(\w+(?:\s+\w+){0,4})",
            ],
            "affiliation": [
                r"(\w+(?:\s+\w+){0,4})\s+(?:bergabung|terdaftar|tercatat|terafiliasi|berhubungan|berasosiasi)\s+(?:\w+\s+)*(?:dengan|pada|di)\s+(\w+(?:\s+\w+){0,4})",
                r"(\w+(?:\s+\w+){0,4})\s+(?:adalah anggota|menjadi anggota|termasuk dalam)\s+(\w+(?:\s+\w+){0,4})",
            ],
            "family": [
                r"(\w+(?:\s+\w+){0,3})\s+(?:adalah|merupakan)\s+(?:\w+\s+)*(?:istri|suami|anak|ayah|ibu|saudara|keluarga|kerabat)\s+(?:dari|nya)\s+(\w+(?:\s+\w+){0,3})",
                r"(\w+(?:\s+\w+){0,3})\s+(?:menikah dengan|bercerai dari|berhubungan dengan)\s+(\w+(?:\s+\w+){0,3})",
            ],
            "ownership": [
                r"(\w+(?:\s+\w+){0,4})\s+(?:memiliki|menguasai|mendapatkan|membeli|mengakuisisi)\s+(?:\w+\s+)*?(\d+(?:\.\d+)?%?)?\s*(?:saham|kepemilikan|bagian|hak|aset)?\s*(?:dari|pada)?\s+(\w+(?:\s+\w+){0,4})",
                r"(\w+(?:\s+\w+){0,4})\s+(?:dimiliki|dikuasai|dipegang|dikontrol)\s+(?:\w+\s+)*oleh\s+(\w+(?:\s+\w+){0,4})",
            ],
            "location": [
                r"(\w+(?:\s+\w+){0,4})\s+(?:berlokasi|berada|terletak|berbasis|berkantor|bermarkas)\s+(?:\w+\s+)*(?:di|pada|dalam)\s+(\w+(?:\s+\w+){0,4})",
                r"(\w+(?:\s+\w+){0,4})\s+(?:berasal|beroperasi|melayani)\s+(?:\w+\s+)*(?:dari|di|pada)\s+(\w+(?:\s+\w+){0,4})",
            ],
        }

        # Confidence scores for different extraction methods
        self.confidence_scores = {
            "pattern": 0.8,
            "co_occurrence": 0.5,
            "syntactic": 0.7,
        }

    def extract_from_text(
        self, text: str, entities: List[Dict], doc_id: Optional[int] = None
    ) -> List[ExtractedRelationship]:
        """Extract relationships from text given a list of entities."""
        relationships = []

        # Split text into sentences
        sentences = self._split_sentences(text)

        for sentence in sentences:
            # Pattern-based extraction
            pattern_rels = self._extract_patterns(sentence, entities)
            relationships.extend(pattern_rels)

            # Co-occurrence extraction
            cooc_rels = self._extract_cooccurrence(sentence, entities)
            relationships.extend(cooc_rels)

        # Deduplicate and score
        relationships = self._deduplicate_and_score(relationships)

        return relationships

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Handle Indonesian sentence delimiters
        sentences = re.split(r"[.!?。]+", text)
        return [s.strip() for s in sentences if len(s.strip()) > 10]

    def split_paragraphs(self, text: str) -> List[str]:
        """Split text into paragraphs."""
        paragraphs = re.split(r"\n\s*\n+", text)
        # Fall back to single newlines if no double-newlines found
        if len(paragraphs) <= 1:
            paragraphs = text.split("\n")
        return [p.strip() for p in paragraphs if len(p.strip()) > 20]

    def sliding_windows(self, text: str, window_size: int = 300, step: int = None) -> List[str]:
        """Split text into overlapping sliding word windows."""
        if step is None:
            step = window_size // 2
        tokens = text.split()
        if len(tokens) <= window_size:
            return [text]
        windows = []
        for i in range(0, len(tokens) - window_size + 1, step):
            windows.append(" ".join(tokens[i : i + window_size]))
        return windows

    def _log_likelihood(self, k: int, ki: float, kj: float, kij: float) -> float:
        """Compute Log-Likelihood significance (G²) for co-occurrence."""
        def xlogy(x: float) -> float:
            return x * math.log(x) if x > 0 else 0.0

        o11 = kij
        o12 = ki - kij
        o21 = kj - kij
        o22 = k - ki - kj + kij

        ll = 2.0 * (
            xlogy(o11) + xlogy(o12) + xlogy(o21) + xlogy(o22)
            - xlogy(ki) - xlogy(k - ki)
            - xlogy(kj) - xlogy(k - kj)
            + xlogy(k)
        )
        return max(0.0, ll)

    def compute_cooccurrence_network(
        self,
        documents: List[dict],
        window_type: str = "sentence",
        window_size: int = 300,
        min_cooc: int = 1,
    ) -> List[dict]:
        """Compute entity co-occurrence network from documents using sub-document windows.

        Args:
            documents: List of {"id": int, "content": str, "entity_names": List[str]}
            window_type: "sentence" | "paragraph" | "sliding"
            window_size: word count for sliding windows (ignored for sentence/paragraph)
            min_cooc: minimum co-occurrence count to include an edge

        Returns:
            List of {"source": name, "target": name, "weight": float,
                     "count": int, "evidence": str} sorted by weight descending.
        """
        try:
            from scipy.sparse import csr_matrix
            import numpy as np
        except ImportError:
            # Fallback: use pure-Python lists instead of sparse matrix
            csr_matrix = None
            np = None

        # Collect all unique entity names (case-insensitive, preserve first-seen casing)
        seen_lower: set = set()
        all_entity_names: List[str] = []
        for doc in documents:
            for name in doc.get("entity_names", []):
                key = name.lower()
                if key not in seen_lower:
                    seen_lower.add(key)
                    all_entity_names.append(name)

        n_entities = len(all_entity_names)
        if n_entities < 2:
            return []

        name_to_idx = {name.lower(): i for i, name in enumerate(all_entity_names)}

        # Build per-window entity presence records
        # window_records: list of (window_text, frozenset_of_entity_indices)
        window_records: List[tuple] = []

        for doc in documents:
            content = doc.get("content", "")
            if not content:
                continue
            entity_names_lower = [n.lower() for n in doc.get("entity_names", [])]

            if window_type == "sentence":
                windows = self._split_sentences(content)
            elif window_type == "paragraph":
                windows = self.split_paragraphs(content)
            else:
                windows = self.sliding_windows(content, window_size=window_size)

            for window in windows:
                window_lower = window.lower()
                present = frozenset(
                    name_to_idx[name]
                    for name in entity_names_lower
                    if name in name_to_idx and name in window_lower
                )
                if len(present) >= 2:
                    window_records.append((window, present))

        n_windows = len(window_records)
        if n_windows == 0:
            return []

        # Build co-occurrence counts and evidence in one pass
        cooc_counts: Dict[tuple, int] = {}
        evidence_map: Dict[tuple, List[str]] = {}

        for window_text, present in window_records:
            present_list = sorted(present)
            for pi, ei in enumerate(present_list):
                for ej in present_list[pi + 1 :]:
                    key = (ei, ej)
                    cooc_counts[key] = cooc_counts.get(key, 0) + 1
                    if len(evidence_map.get(key, [])) < 3:
                        evidence_map.setdefault(key, []).append(window_text)

        if not cooc_counts:
            return []

        # Per-entity window counts (ki, kj) using sparse matrix for accuracy
        if csr_matrix is not None and np is not None:
            rows, cols, data = [], [], []
            for w_idx, (_, present) in enumerate(window_records):
                for e_idx in present:
                    rows.append(w_idx)
                    cols.append(e_idx)
                    data.append(1.0)
            X = csr_matrix(
                (data, (rows, cols)), shape=(n_windows, n_entities), dtype=float
            )
            ki_arr = np.asarray(X.sum(axis=0)).flatten()
        else:
            ki_arr = [0.0] * n_entities
            for _, present in window_records:
                for e_idx in present:
                    ki_arr[e_idx] += 1

        k = float(n_windows)

        edges = []
        for (ei, ej), kij in cooc_counts.items():
            if kij < min_cooc:
                continue
            ki = float(ki_arr[ei])
            kj = float(ki_arr[ej])
            ll = self._log_likelihood(k, ki, kj, float(kij))
            evidence_snippets = evidence_map.get((ei, ej), [])
            edges.append({
                "source": all_entity_names[ei],
                "target": all_entity_names[ej],
                "weight": ll,
                "count": kij,
                "evidence": " | ".join(evidence_snippets[:3]),
            })

        edges.sort(key=lambda e: e["weight"], reverse=True)
        return edges

    def _extract_patterns(
        self, sentence: str, entities: List[Dict]
    ) -> List[ExtractedRelationship]:
        """Extract relationships using patterns."""
        relationships = []

        for rel_type, patterns in self.patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, sentence, re.IGNORECASE)
                for match in matches:
                    groups = match.groups()
                    if len(groups) >= 2:
                        source_text = groups[0].strip()
                        target_text = groups[-1].strip()

                        # Find matching entities
                        source = self._find_entity_by_text(source_text, entities)
                        target = self._find_entity_by_text(target_text, entities)

                        if source and target and source["id"] != target["id"]:
                            relationships.append(
                                ExtractedRelationship(
                                    source_text=source["name"],
                                    target_text=target["name"],
                                    source_type=source["entity_type"],
                                    target_type=target["entity_type"],
                                    relationship_type=rel_type,
                                    confidence=self.confidence_scores["pattern"],
                                    evidence=match.group(0),
                                    sentence_context=sentence,
                                )
                            )

        return relationships

    def _extract_cooccurrence(
        self, sentence: str, entities: List[Dict]
    ) -> List[ExtractedRelationship]:
        """Extract relationships based on entity co-occurrence in sentences."""
        relationships = []

        # Find all entities mentioned in this sentence
        mentioned = []
        for entity in entities:
            if entity["name"].lower() in sentence.lower():
                mentioned.append(entity)

        # Create co-occurrence relationships for pairs
        if len(mentioned) >= 2:
            for i, source in enumerate(mentioned):
                for target in mentioned[i + 1 :]:
                    if source["id"] != target["id"]:
                        # Determine relationship type based on entity types
                        rel_type = self._infer_relationship_type(
                            source["entity_type"], target["entity_type"]
                        )

                        relationships.append(
                            ExtractedRelationship(
                                source_text=source["name"],
                                target_text=target["name"],
                                source_type=source["entity_type"],
                                target_type=target["entity_type"],
                                relationship_type=rel_type,
                                confidence=self.confidence_scores["co_occurrence"],
                                evidence=sentence,
                                sentence_context=sentence,
                            )
                        )

        return relationships

    def _find_entity_by_text(self, text: str, entities: List[Dict]) -> Optional[Dict]:
        """Find an entity by matching text."""
        text_lower = text.lower()
        for entity in entities:
            if (
                entity["name"].lower() == text_lower
                or entity["name"].lower() in text_lower
            ):
                return entity
        return None

    def _infer_relationship_type(self, type1: str, type2: str) -> str:
        """Infer relationship type based on entity types."""
        type_pair = tuple(sorted([type1, type2]))

        type_mappings = {
            ("PER", "ORG"): "affiliation",
            ("PER", "GPE"): "location",
            ("ORG", "GPE"): "location",
            ("PER", "PER"): "family",
            ("ORG", "ORG"): "affiliation",
        }

        return type_mappings.get(type_pair, "co-occurrence")

    def _deduplicate_and_score(
        self, relationships: List[ExtractedRelationship]
    ) -> List[ExtractedRelationship]:
        """Deduplicate relationships and calculate final confidence scores."""
        seen = {}

        for rel in relationships:
            key = (
                rel.source_text.lower(),
                rel.target_text.lower(),
                rel.relationship_type,
            )

            if key in seen:
                # Boost confidence for multiple evidences
                seen[key].confidence = min(1.0, seen[key].confidence + 0.1)
            else:
                seen[key] = rel

        return list(seen.values())

    def calculate_relationship_strength(
        self, relationships: List[ExtractedRelationship]
    ) -> Dict[Tuple[str, str], float]:
        """Calculate relationship strength based on frequency and confidence."""
        strength_scores = defaultdict(lambda: {"count": 0, "total_confidence": 0.0})

        for rel in relationships:
            key = (rel.source_text, rel.target_text)
            strength_scores[key]["count"] += 1
            strength_scores[key]["total_confidence"] += rel.confidence

        # Calculate final strength scores
        result = {}
        for key, data in strength_scores.items():
            avg_confidence = data["total_confidence"] / data["count"]
            frequency_boost = min(0.2, (data["count"] - 1) * 0.05)
            result[key] = min(1.0, avg_confidence + frequency_boost)

        return result


class RelationshipStore:
    """Stores and manages relationships in the database."""

    def __init__(self, db_manager):
        self.db = db_manager

    def create_relationship(
        self,
        source_id: int,
        target_id: int,
        rel_type: str,
        confidence: float,
        evidence: Optional[str] = None,
        doc_id: Optional[int] = None,
    ) -> int:
        """Create a relationship in the database."""
        self.db.conn.execute(
            """
            INSERT INTO relationships 
            (source_entity_id, target_entity_id, relationship_type, confidence, evidence, source_doc_id)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT (source_entity_id, target_entity_id, relationship_type) DO UPDATE SET
                confidence = excluded.confidence,
                evidence = excluded.evidence,
                created_at = CURRENT_TIMESTAMP
            """,
            (source_id, target_id, rel_type, confidence, evidence, doc_id),
        )
        self.db.conn.commit()
        result = self.db.conn.execute(
            "SELECT currval('relationships_id_seq')"
        ).fetchone()
        return result[0]

    def get_relationships(
        self, entity_id: Optional[int] = None, rel_type: Optional[str] = None
    ) -> List[Dict]:
        """Get relationships from database."""
        if entity_id:
            results = self.db.conn.execute(
                """
                SELECT 
                    r.id,
                    r.source_entity_id,
                    r.target_entity_id,
                    s.name as source_name,
                    t.name as target_name,
                    r.relationship_type,
                    r.confidence,
                    r.evidence,
                    r.source_doc_id,
                    r.created_at
                FROM relationships r
                JOIN entities s ON r.source_entity_id = s.id
                JOIN entities t ON r.target_entity_id = t.id
                WHERE r.source_entity_id = ? OR r.target_entity_id = ?
                ORDER BY r.confidence DESC, r.created_at DESC
                """,
                (entity_id, entity_id),
            ).fetchall()
        else:
            where_clause = "WHERE r.relationship_type = ?" if rel_type else ""
            params = (rel_type,) if rel_type else ()
            results = self.db.conn.execute(
                f"""
                SELECT 
                    r.id,
                    r.source_entity_id,
                    r.target_entity_id,
                    s.name as source_name,
                    t.name as target_name,
                    r.relationship_type,
                    r.confidence,
                    r.evidence,
                    r.source_doc_id,
                    r.created_at
                FROM relationships r
                JOIN entities s ON r.source_entity_id = s.id
                JOIN entities t ON r.target_entity_id = t.id
                {where_clause}
                ORDER BY r.confidence DESC, r.created_at DESC
                """,
                params,
            ).fetchall()

        return [
            {
                "id": row[0],
                "source_entity_id": row[1],
                "target_entity_id": row[2],
                "source_name": row[3],
                "target_name": row[4],
                "relationship_type": row[5],
                "confidence": row[6],
                "evidence": row[7],
                "source_doc_id": row[8],
                "created_at": str(row[9]),
            }
            for row in results
        ]

    def delete_relationship(self, rel_id: int) -> bool:
        """Delete a relationship."""
        try:
            self.db.conn.execute("DELETE FROM relationships WHERE id = ?", (rel_id,))
            self.db.conn.commit()
            return True
        except Exception as e:
            print(f"Error deleting relationship: {e}")
            return False

    def get_relationship_stats(self) -> Dict:
        """Get relationship statistics."""
        total = self.db.conn.execute("SELECT COUNT(*) FROM relationships").fetchone()[0]

        by_type = self.db.conn.execute(
            """
            SELECT relationship_type, COUNT(*) 
            FROM relationships 
            GROUP BY relationship_type
            """
        ).fetchall()

        avg_confidence = self.db.conn.execute(
            "SELECT AVG(confidence) FROM relationships"
        ).fetchone()[0]

        return {
            "total": total,
            "by_type": {row[0]: row[1] for row in by_type},
            "average_confidence": avg_confidence or 0.0,
        }
