"""Named Entity Recognition module for Indonesian text."""

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple
from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline


@dataclass
class Entity:
    """Represents a named entity."""

    text: str
    entity_type: str
    start: int
    end: int
    confidence: float

    def __hash__(self):
        return hash((self.text.lower(), self.entity_type))

    def __eq__(self, other):
        if not isinstance(other, Entity):
            return False
        return (
            self.text.lower() == other.text.lower()
            and self.entity_type == other.entity_type
        )


class IndonesianNERExtractor:
    """NER extractor using cahya/bert-base-indonesian-NER."""

    ENTITY_TYPES = {
        "B-PER": "PERSON",
        "I-PER": "PERSON",
        "B-ORG": "ORGANIZATION",
        "I-ORG": "ORGANIZATION",
        "B-LOC": "LOCATION",
        "I-LOC": "LOCATION",
    }

    def __init__(
        self, model_name: str = "cahya/bert-base-indonesian-NER", device: str = "cpu"
    ):
        """
        Initialize the NER extractor.

        Args:
            model_name: HuggingFace model name
            device: Device to run on (cpu/cuda)
        """
        self.model_name = model_name
        self.device = device
        self.tokenizer = None
        self.model = None
        self.nlp_pipeline = None
        self._loaded = False

    def load_model(self) -> None:
        """Load the NER model (lazy loading)."""
        if self._loaded:
            return

        print(f"Loading NER model: {self.model_name}")
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForTokenClassification.from_pretrained(self.model_name)

        self.nlp_pipeline = pipeline(
            "ner",
            model=self.model,
            tokenizer=self.tokenizer,
            device=self.device,
            aggregation_strategy="simple",
        )
        self._loaded = True
        print("NER model loaded successfully")

    def extract(self, text: str) -> List[Entity]:
        """
        Extract entities from text.

        Args:
            text: Input text

        Returns:
            List of Entity objects
        """
        if not self._loaded:
            self.load_model()

        if not text or len(text.strip()) == 0:
            return []

        # Split text into chunks if too long
        max_length = 512
        chunks = self._split_text(text, max_length)

        all_entities = []
        offset = 0

        for chunk in chunks:
            try:
                results = self.nlp_pipeline(chunk)

                for result in results:
                    entity_text = result.get("word", "").strip()
                    entity_label = result.get("entity_group", "")
                    confidence = result.get("score", 0.0)
                    start = result.get("start", 0) + offset
                    end = result.get("end", 0) + offset

                    # Map entity type
                    entity_type = self.ENTITY_TYPES.get(entity_label, entity_label)

                    # Clean entity text
                    entity_text = self._clean_entity_text(entity_text)

                    if entity_text and len(entity_text) > 1:
                        entity = Entity(
                            text=entity_text,
                            entity_type=entity_type,
                            start=start,
                            end=end,
                            confidence=confidence,
                        )
                        all_entities.append(entity)
            except Exception as e:
                print(f"Error processing chunk: {e}")

            offset += len(chunk)

        # Deduplicate entities
        return self._deduplicate_entities(all_entities)

    def extract_batch(self, texts: List[str]) -> List[List[Entity]]:
        """
        Extract entities from multiple texts.

        Args:
            texts: List of input texts

        Returns:
            List of entity lists
        """
        return [self.extract(text) for text in texts]

    def get_entity_summary(self, entities: List[Entity]) -> Dict[str, List[str]]:
        """
        Get a summary of entities grouped by type.

        Args:
            entities: List of entities

        Returns:
            Dictionary mapping entity types to lists of unique entity texts
        """
        summary: Dict[str, Set[str]] = {}

        for entity in entities:
            if entity.entity_type not in summary:
                summary[entity.entity_type] = set()
            summary[entity.entity_type].add(entity.text)

        return {k: sorted(list(v)) for k, v in summary.items()}

    def _split_text(self, text: str, max_length: int) -> List[str]:
        """Split text into chunks for processing."""
        # Simple sentence-based splitting
        sentences = re.split(r"(?<=[.!?])\s+", text)
        chunks = []
        current_chunk = []
        current_length = 0

        for sentence in sentences:
            sentence_length = len(sentence)

            if current_length + sentence_length > max_length:
                if current_chunk:
                    chunks.append(" ".join(current_chunk))
                current_chunk = [sentence]
                current_length = sentence_length
            else:
                current_chunk.append(sentence)
                current_length += sentence_length

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks if chunks else [text]

    def _clean_entity_text(self, text: str) -> str:
        """Clean extracted entity text."""
        # Remove special tokens
        text = text.replace("##", "")
        text = text.replace("Ġ", " ")
        text = text.strip()

        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text)

        return text

    def _deduplicate_entities(self, entities: List[Entity]) -> List[Entity]:
        """Remove duplicate entities."""
        seen = set()
        unique = []

        for entity in entities:
            key = (entity.text.lower(), entity.entity_type)
            if key not in seen:
                seen.add(key)
                unique.append(entity)

        return unique
