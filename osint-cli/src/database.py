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
                evidence TEXT,
                source_doc_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create sequence for entity aliases
        self.conn.execute("""
            CREATE SEQUENCE IF NOT EXISTS entity_aliases_id_seq START 1;
        """)

        # Entity aliases table: stores alternative names for entities
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS entity_aliases (
                id INTEGER PRIMARY KEY DEFAULT nextval('entity_aliases_id_seq'),
                entity_id INTEGER NOT NULL,
                alias_name VARCHAR NOT NULL,
                confidence FLOAT DEFAULT 1.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(entity_id, alias_name)
            )
        """)

        # Create sequence for entity mentions
        self.conn.execute("""
            CREATE SEQUENCE IF NOT EXISTS entity_mentions_id_seq START 1;
        """)

        # Entity mentions table: tracks entity mentions in documents
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS entity_mentions (
                id INTEGER PRIMARY KEY DEFAULT nextval('entity_mentions_id_seq'),
                entity_id INTEGER NOT NULL,
                doc_id INTEGER NOT NULL,
                context TEXT,
                start_pos INTEGER,
                end_pos INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create sequence for projects
        self.conn.execute("""
            CREATE SEQUENCE IF NOT EXISTS projects_id_seq START 1;
        """)

        # Projects table: stores investigation projects
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY DEFAULT nextval('projects_id_seq'),
                name VARCHAR NOT NULL,
                description TEXT,
                status VARCHAR DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Project documents junction table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS project_documents (
                project_id INTEGER,
                doc_id INTEGER,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (project_id, doc_id)
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
                url VARCHAR,
                file_hash VARCHAR,
                doc_type VARCHAR,
                status VARCHAR DEFAULT 'pending',
                domain VARCHAR,
                publish_date VARCHAR,
                entity_count INTEGER DEFAULT 0,
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
        self,
        filename: str,
        file_path: str,
        file_hash: str = None,
        doc_type: str = None,
        url: str = None,
        domain: str = None,
        publish_date: str = None,
        status: str = "pending",
    ) -> int:
        """Insert a document and return its ID."""
        self.conn.execute(
            """
            INSERT INTO documents (filename, file_path, file_hash, doc_type, url, domain, publish_date, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                filename,
                file_path,
                file_hash,
                doc_type,
                url,
                domain,
                publish_date,
                status,
            ),
        )
        self.conn.commit()
        result = self.conn.execute("SELECT currval('documents_id_seq')").fetchone()
        return result[0] if result else None

    def document_exists_by_url(self, url: str, project_id: int = None) -> bool:
        """Check if a document with the given URL already exists in a project."""
        if project_id:
            result = self.conn.execute(
                """
                SELECT 1 FROM documents d
                JOIN project_documents pd ON d.id = pd.doc_id
                WHERE d.url = ? AND pd.project_id = ?
                LIMIT 1
                """,
                (url, project_id),
            ).fetchone()
        else:
            result = self.conn.execute(
                "SELECT 1 FROM documents WHERE url = ? LIMIT 1",
                (url,),
            ).fetchone()
        return result is not None

    def add_document_to_project(self, doc_id: int, project_id: int) -> None:
        """Associate a document with a project."""
        self.conn.execute(
            """
            INSERT INTO project_documents (doc_id, project_id)
            VALUES (?, ?)
            ON CONFLICT DO NOTHING
            """,
            (doc_id, project_id),
        )
        self.conn.commit()

    def update_document_status(
        self, doc_id: int, status: str, entity_count: int = None
    ) -> None:
        """Update document status and optionally entity count."""
        if entity_count is not None:
            self.conn.execute(
                "UPDATE documents SET status = ?, entity_count = ? WHERE id = ?",
                (status, entity_count, doc_id),
            )
        else:
            self.conn.execute(
                "UPDATE documents SET status = ? WHERE id = ?",
                (status, doc_id),
            )
        self.conn.commit()

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

    def get_document(self, doc_id: int) -> tuple:
        """Get a document by ID."""
        result = self.conn.execute(
            "SELECT id, filename, file_path, file_hash, doc_type, processed_at FROM documents WHERE id = ?",
            (doc_id,),
        ).fetchone()
        return result

    def get_document_entities_count(self, doc_id: int) -> int:
        """Get the count of entities associated with a document."""
        result = self.conn.execute(
            "SELECT COUNT(*) FROM entities WHERE source_doc_id = ?",
            (doc_id,),
        ).fetchone()
        return result[0]

    def delete_document_with_entities(self, doc_id: int) -> dict:
        """Delete a document and all its associated entities using cascade delete.

        Returns:
            dict: Summary of deleted items
        """
        try:
            # Start transaction
            self.conn.execute("BEGIN TRANSACTION")

            # Get entity IDs associated with this document
            entity_rows = self.conn.execute(
                "SELECT id FROM entities WHERE source_doc_id = ?",
                (doc_id,),
            ).fetchall()
            entity_ids = [row[0] for row in entity_rows]

            # Delete relationships where entities are source or target
            if entity_ids:
                placeholders = ", ".join(["?"] * len(entity_ids))
                self.conn.execute(
                    f"DELETE FROM relationships WHERE source_entity_id IN ({placeholders}) OR target_entity_id IN ({placeholders})",
                    entity_ids + entity_ids,
                )

            # Delete entity mentions for this document
            self.conn.execute(
                "DELETE FROM entity_mentions WHERE doc_id = ?",
                (doc_id,),
            )

            # Delete entity aliases for entities of this document
            if entity_ids:
                placeholders = ", ".join(["?"] * len(entity_ids))
                self.conn.execute(
                    f"DELETE FROM entity_aliases WHERE entity_id IN ({placeholders})",
                    entity_ids,
                )

            # Count entities before deletion
            entities_deleted = len(entity_ids)

            # Delete entities
            self.conn.execute(
                "DELETE FROM entities WHERE source_doc_id = ?",
                (doc_id,),
            )

            # Remove from project associations
            self.conn.execute(
                "DELETE FROM project_documents WHERE doc_id = ?",
                (doc_id,),
            )

            # Delete the document itself
            self.conn.execute(
                "DELETE FROM documents WHERE id = ?",
                (doc_id,),
            )

            # Clean up orphaned relationships (where source or target entity no longer exists)
            self.conn.execute("""
                DELETE FROM relationships 
                WHERE source_entity_id NOT IN (SELECT id FROM entities)
                OR target_entity_id NOT IN (SELECT id FROM entities)
            """)

            # Commit transaction
            self.conn.commit()

            return {
                "success": True,
                "entities_deleted": entities_deleted,
                "document_deleted": True,
            }
        except Exception as e:
            self.conn.execute("ROLLBACK")
            raise e

    def get_project_documents(self, project_id: int) -> list:
        """Get all documents associated with a project."""
        result = self.conn.execute(
            """
            SELECT d.id, d.filename, d.file_path, d.file_hash, d.doc_type, d.processed_at,
                   COUNT(e.id) as entity_count
            FROM documents d
            JOIN project_documents pd ON d.id = pd.doc_id
            LEFT JOIN entities e ON e.source_doc_id = d.id
            WHERE pd.project_id = ?
            GROUP BY d.id, d.filename, d.file_path, d.file_hash, d.doc_type, d.processed_at, pd.added_at
            ORDER BY pd.added_at DESC
            """,
            (project_id,),
        ).fetchall()
        return result

    def update_document_processed_at(self, doc_id: int) -> None:
        """Update the processed_at timestamp for a document."""
        self.conn.execute(
            "UPDATE documents SET processed_at = CURRENT_TIMESTAMP WHERE id = ?",
            (doc_id,),
        )
        self.conn.commit()
