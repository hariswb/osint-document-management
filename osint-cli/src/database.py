from pathlib import Path
import duckdb


class DatabaseManager:
    def __init__(self, db_path: str = "data/osint.db"):
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = duckdb.connect(db_path)
        self._create_tables()

    def _create_tables(self):
        # Create sequence for auto-incrementing IDs
        self.conn.execute("""
            CREATE SEQUENCE IF NOT EXISTS entities_id_seq START 1;
        """)

        # Entities table: stores extracted named entities
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS entities (
                id INTEGER PRIMARY KEY DEFAULT nextval('entities_id_seq'),
                name VARCHAR NOT NULL,
                entity_type VARCHAR NOT NULL,
                confidence FLOAT,
                source_doc_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create sequence for relationships
        self.conn.execute("""
            CREATE SEQUENCE IF NOT EXISTS relationships_id_seq START 1;
        """)

        # Relationships table: stores relationships between entities
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS relationships (
                id INTEGER PRIMARY KEY DEFAULT nextval('relationships_id_seq'),
                source_entity_id INTEGER,
                target_entity_id INTEGER,
                relationship_type VARCHAR,
                confidence FLOAT,
                source_doc_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create sequence for documents
        self.conn.execute("""
            CREATE SEQUENCE IF NOT EXISTS documents_id_seq START 1;
        """)

        # Documents table: stores document metadata
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY DEFAULT nextval('documents_id_seq'),
                filename VARCHAR NOT NULL,
                file_path VARCHAR NOT NULL,
                file_hash VARCHAR,
                doc_type VARCHAR,
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create sequence for ksei_balancepos
        self.conn.execute("""
            CREATE SEQUENCE IF NOT EXISTS ksei_balancepos_id_seq START 1;
        """)

        # KSEI Balance Position table: for Indonesian shareholder data
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS ksei_balancepos (
                id INTEGER PRIMARY KEY DEFAULT nextval('ksei_balancepos_id_seq'),
                participant_id VARCHAR,
                investor_name VARCHAR,
                security_code VARCHAR,
                security_name VARCHAR,
                balance INTEGER,
                processed_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        self.conn.commit()

    def close(self):
        self.conn.close()

    def insert_document(
        self, filename: str, file_path: str, file_hash: str = None, doc_type: str = None
    ) -> int:
        """Insert a document and return its ID."""
        self.conn.execute(
            """
            INSERT INTO documents (filename, file_path, file_hash, doc_type)
            VALUES (?, ?, ?, ?)
        """,
            (filename, file_path, file_hash, doc_type),
        )
        self.conn.commit()
        result = self.conn.execute("SELECT currval('documents_id_seq')").fetchone()
        return result[0]

    def insert_entity(
        self,
        name: str,
        entity_type: str,
        confidence: float = None,
        source_doc_id: int = None,
    ) -> int:
        """Insert an entity and return its ID."""
        # Convert confidence to Python float if it's a numpy type
        if confidence is not None:
            confidence = float(confidence)

        self.conn.execute(
            """
            INSERT INTO entities (name, entity_type, confidence, source_doc_id)
            VALUES (?, ?, ?, ?)
        """,
            (name, entity_type, confidence, source_doc_id),
        )
        self.conn.commit()
        result = self.conn.execute("SELECT currval('entities_id_seq')").fetchone()
        return result[0]

    def get_entities(self, entity_type: str = None, limit: int = 100) -> list:
        """Get entities, optionally filtered by type."""
        if entity_type:
            result = self.conn.execute(
                """
                SELECT * FROM entities WHERE entity_type = ? ORDER BY created_at DESC LIMIT ?
            """,
                (entity_type, limit),
            ).fetchall()
        else:
            result = self.conn.execute(
                """
                SELECT * FROM entities ORDER BY created_at DESC LIMIT ?
            """,
                (limit,),
            ).fetchall()
        return result

    def get_entity_count(self) -> int:
        """Get total entity count."""
        result = self.conn.execute("SELECT COUNT(*) FROM entities").fetchone()
        return result[0]

    def get_document_count(self) -> int:
        """Get total document count."""
        result = self.conn.execute("SELECT COUNT(*) FROM documents").fetchone()
        return result[0]
