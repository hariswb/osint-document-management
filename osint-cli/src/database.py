from pathlib import Path
import duckdb


class DatabaseManager:
    def __init__(self, db_path: str = "data/osint.db"):
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = duckdb.connect(db_path)
        self._create_tables()

    def _create_tables(self):
        # Entities table: stores extracted named entities
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS entities (
                id INTEGER PRIMARY KEY,
                name VARCHAR NOT NULL,
                entity_type VARCHAR NOT NULL,
                confidence FLOAT,
                source_doc_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Relationships table: stores relationships between entities
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS relationships (
                id INTEGER PRIMARY KEY,
                source_entity_id INTEGER,
                target_entity_id INTEGER,
                relationship_type VARCHAR,
                confidence FLOAT,
                source_doc_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Documents table: stores document metadata
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY,
                filename VARCHAR NOT NULL,
                file_path VARCHAR NOT NULL,
                file_hash VARCHAR,
                doc_type VARCHAR,
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # KSEI Balance Position table: for Indonesian shareholder data
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS ksei_balancepos (
                id INTEGER PRIMARY KEY,
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
