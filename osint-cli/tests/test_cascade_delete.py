"""
Unit tests for cascade delete - NER entities should be deleted when a document is removed.
"""

import pytest


class TestCascadeDelete:
    """Test suite for cascade delete functionality."""

    def test_delete_document_cascade_deletes_entities(
        self,
        db,
        create_project,
        create_document,
        create_entity,
        link_document_to_project,
    ):
        """Test that deleting a document cascades deletion of its entities."""
        # Create project and document
        project = create_project(name="Cascade Test")
        doc = create_document(filename="test.txt")
        link_document_to_project(doc, project)

        # Create entities for the document
        entity1 = create_entity(source_doc_id=doc, name="Entity 1")
        entity2 = create_entity(source_doc_id=doc, name="Entity 2")
        entity3 = create_entity(source_doc_id=doc, name="Entity 3")

        # Verify entities exist
        entities_before = db.conn.execute(
            "SELECT id FROM entities WHERE source_doc_id = ?", (doc,)
        ).fetchall()
        assert len(entities_before) == 3

        # Delete document with cascade
        result = db.delete_document_with_entities(doc)

        # Verify success
        assert result["success"] is True
        assert result["document_deleted"] is True
        assert result["entities_deleted"] == 3

        # Verify entities are deleted
        entities_after = db.conn.execute(
            "SELECT id FROM entities WHERE source_doc_id = ?", (doc,)
        ).fetchall()
        assert len(entities_after) == 0

        # Verify document is deleted
        doc_exists = db.conn.execute(
            "SELECT id FROM documents WHERE id = ?", (doc,)
        ).fetchone()
        assert doc_exists is None

    def test_delete_document_cascade_deletes_relationships(
        self,
        db,
        create_project,
        create_document,
        create_entity,
        link_document_to_project,
    ):
        """Test that deleting a document cascades deletion of relationships between its entities."""
        # Create project and document
        project = create_project(name="Relationship Cascade Test")
        doc = create_document(filename="test.txt")
        link_document_to_project(doc, project)

        # Create entities
        entity1 = create_entity(source_doc_id=doc, name="Person A")
        entity2 = create_entity(source_doc_id=doc, name="Person B")
        entity3 = create_entity(source_doc_id=doc, name="Organization C")

        # Create relationships
        db.conn.execute(
            """
            INSERT INTO relationships (source_entity_id, target_entity_id, relationship_type, evidence, source_doc_id)
            VALUES (?, ?, ?, ?, ?)
            """,
            (entity1, entity2, "knows", "Evidence text", doc),
        )
        db.conn.execute(
            """
            INSERT INTO relationships (source_entity_id, target_entity_id, relationship_type, evidence, source_doc_id)
            VALUES (?, ?, ?, ?, ?)
            """,
            (entity2, entity3, "works_for", "Another evidence", doc),
        )
        db.conn.commit()

        # Verify relationships exist
        rels_before = db.conn.execute(
            "SELECT id FROM relationships WHERE source_doc_id = ?", (doc,)
        ).fetchall()
        assert len(rels_before) == 2

        # Delete document
        db.delete_document_with_entities(doc)

        # Verify relationships are deleted
        rels_after = db.conn.execute(
            "SELECT id FROM relationships WHERE source_doc_id = ?", (doc,)
        ).fetchall()
        assert len(rels_after) == 0

        # Also verify no orphaned relationships exist
        all_rels = db.conn.execute(
            "SELECT id FROM relationships WHERE source_entity_id = ? OR target_entity_id = ?",
            (entity1, entity1),
        ).fetchall()
        assert len(all_rels) == 0

    def test_delete_document_cascade_deletes_entity_mentions(
        self,
        db,
        create_project,
        create_document,
        create_entity,
        link_document_to_project,
    ):
        """Test that deleting a document cascades deletion of entity mentions."""
        # Create project and document
        project = create_project(name="Mentions Cascade Test")
        doc = create_document(filename="test.txt")
        link_document_to_project(doc, project)

        # Create entity
        entity = create_entity(source_doc_id=doc, name="Test Entity")

        # Create entity mentions
        db.conn.execute(
            """
            INSERT INTO entity_mentions (entity_id, doc_id, context, start_pos, end_pos)
            VALUES (?, ?, ?, ?, ?)
            """,
            (entity, doc, "Context around mention", 10, 25),
        )
        db.conn.execute(
            """
            INSERT INTO entity_mentions (entity_id, doc_id, context, start_pos, end_pos)
            VALUES (?, ?, ?, ?, ?)
            """,
            (entity, doc, "Another context", 50, 65),
        )
        db.conn.commit()

        # Verify mentions exist
        mentions_before = db.conn.execute(
            "SELECT id FROM entity_mentions WHERE doc_id = ?", (doc,)
        ).fetchall()
        assert len(mentions_before) == 2

        # Delete document
        db.delete_document_with_entities(doc)

        # Verify mentions are deleted
        mentions_after = db.conn.execute(
            "SELECT id FROM entity_mentions WHERE doc_id = ?", (doc,)
        ).fetchall()
        assert len(mentions_after) == 0

    def test_delete_document_cascade_deletes_entity_aliases(
        self,
        db,
        create_project,
        create_document,
        create_entity,
        link_document_to_project,
    ):
        """Test that deleting a document cascades deletion of entity aliases."""
        # Create project and document
        project = create_project(name="Aliases Cascade Test")
        doc = create_document(filename="test.txt")
        link_document_to_project(doc, project)

        # Create entity
        entity = create_entity(source_doc_id=doc, name="John Smith")

        # Create aliases
        db.conn.execute(
            """
            INSERT INTO entity_aliases (entity_id, alias_name, confidence)
            VALUES (?, ?, ?)
            """,
            (entity, "J. Smith", 0.9),
        )
        db.conn.execute(
            """
            INSERT INTO entity_aliases (entity_id, alias_name, confidence)
            VALUES (?, ?, ?)
            """,
            (entity, "Johnny", 0.8),
        )
        db.conn.commit()

        # Verify aliases exist
        aliases_before = db.conn.execute(
            "SELECT id FROM entity_aliases WHERE entity_id = ?", (entity,)
        ).fetchall()
        assert len(aliases_before) == 2

        # Delete document
        db.delete_document_with_entities(doc)

        # Verify aliases are deleted
        aliases_after = db.conn.execute(
            "SELECT id FROM entity_aliases WHERE entity_id = ?", (entity,)
        ).fetchall()
        assert len(aliases_after) == 0

    def test_delete_document_removes_project_association(
        self, db, create_project, create_document, link_document_to_project
    ):
        """Test that deleting a document removes its project associations."""
        # Create multiple projects and document
        project1 = create_project(name="Project 1")
        project2 = create_project(name="Project 2")
        doc = create_document(filename="shared.txt")

        # Link to both projects
        link_document_to_project(doc, project1)
        link_document_to_project(doc, project2)

        # Verify associations exist
        associations_before = db.conn.execute(
            "SELECT project_id FROM project_documents WHERE doc_id = ?", (doc,)
        ).fetchall()
        assert len(associations_before) == 2

        # Delete document
        db.delete_document_with_entities(doc)

        # Verify associations are removed
        associations_after = db.conn.execute(
            "SELECT project_id FROM project_documents WHERE doc_id = ?", (doc,)
        ).fetchall()
        assert len(associations_after) == 0

    def test_delete_document_does_not_affect_other_documents(
        self,
        db,
        create_project,
        create_document,
        create_entity,
        link_document_to_project,
    ):
        """Test that deleting one document does not affect entities from other documents."""
        # Create project and two documents
        project = create_project(name="Isolation Test")
        doc1 = create_document(filename="doc1.txt")
        doc2 = create_document(filename="doc2.txt")

        link_document_to_project(doc1, project)
        link_document_to_project(doc2, project)

        # Create entities for both documents
        entity1_doc1 = create_entity(source_doc_id=doc1, name="Doc1 Entity 1")
        entity2_doc1 = create_entity(source_doc_id=doc1, name="Doc1 Entity 2")
        entity1_doc2 = create_entity(source_doc_id=doc2, name="Doc2 Entity 1")
        entity2_doc2 = create_entity(source_doc_id=doc2, name="Doc2 Entity 2")
        entity3_doc2 = create_entity(source_doc_id=doc2, name="Doc2 Entity 3")

        # Delete doc1
        result = db.delete_document_with_entities(doc1)

        # Verify only doc1 entities were deleted
        assert result["entities_deleted"] == 2

        # Verify doc2 entities still exist
        doc2_entities = db.conn.execute(
            "SELECT id, name FROM entities WHERE source_doc_id = ?", (doc2,)
        ).fetchall()
        assert len(doc2_entities) == 3

        doc2_names = [e[1] for e in doc2_entities]
        assert "Doc2 Entity 1" in doc2_names
        assert "Doc2 Entity 2" in doc2_names
        assert "Doc2 Entity 3" in doc2_names

        # Verify doc2 still exists
        doc2_exists = db.conn.execute(
            "SELECT id FROM documents WHERE id = ?", (doc2,)
        ).fetchone()
        assert doc2_exists is not None

    def test_transaction_rollback_on_error(
        self,
        db,
        create_project,
        create_document,
        create_entity,
        link_document_to_project,
    ):
        """Test that transaction is rolled back if cascade delete fails."""
        # Create project and document
        project = create_project(name="Transaction Test")
        doc = create_document(filename="test.txt")
        link_document_to_project(doc, project)

        # Create entity
        entity = create_entity(source_doc_id=doc, name="Test Entity")

        # Verify document and entity exist before deletion attempt
        doc_before = db.conn.execute(
            "SELECT id FROM documents WHERE id = ?", (doc,)
        ).fetchone()
        entity_before = db.conn.execute(
            "SELECT id FROM entities WHERE id = ?", (entity,)
        ).fetchone()

        assert doc_before is not None
        assert entity_before is not None

        # Normal deletion should succeed
        result = db.delete_document_with_entities(doc)
        assert result["success"] is True

        # Verify deletion succeeded
        doc_after = db.conn.execute(
            "SELECT id FROM documents WHERE id = ?", (doc,)
        ).fetchone()
        entity_after = db.conn.execute(
            "SELECT id FROM entities WHERE id = ?", (entity,)
        ).fetchone()

        assert doc_after is None
        assert entity_after is None

    def test_delete_nonexistent_document(self, db):
        """Test that deleting a non-existent document handles gracefully."""
        # Try to delete a document that doesn't exist
        # This should not raise an error but report 0 entities deleted
        result = db.delete_document_with_entities(99999)

        assert result["success"] is True
        assert result["document_deleted"] is True  # No document to delete
        assert result["entities_deleted"] == 0

    def test_cascade_delete_with_complex_relationships(
        self,
        db,
        create_project,
        create_document,
        create_entity,
        link_document_to_project,
    ):
        """Test cascade delete with complex relationship patterns."""
        # Create project and document
        project = create_project(name="Complex Test")
        doc = create_document(filename="complex.txt")
        link_document_to_project(doc, project)

        # Create a chain of entities
        entity_a = create_entity(source_doc_id=doc, name="Entity A")
        entity_b = create_entity(source_doc_id=doc, name="Entity B")
        entity_c = create_entity(source_doc_id=doc, name="Entity C")
        entity_d = create_entity(source_doc_id=doc, name="Entity D")

        # Create bidirectional relationships
        db.conn.execute(
            "INSERT INTO relationships (source_entity_id, target_entity_id, relationship_type, source_doc_id) VALUES (?, ?, ?, ?)",
            (entity_a, entity_b, "knows", doc),
        )
        db.conn.execute(
            "INSERT INTO relationships (source_entity_id, target_entity_id, relationship_type, source_doc_id) VALUES (?, ?, ?, ?)",
            (entity_b, entity_a, "knows", doc),
        )
        db.conn.execute(
            "INSERT INTO relationships (source_entity_id, target_entity_id, relationship_type, source_doc_id) VALUES (?, ?, ?, ?)",
            (entity_b, entity_c, "friends_with", doc),
        )
        db.conn.execute(
            "INSERT INTO relationships (source_entity_id, target_entity_id, relationship_type, source_doc_id) VALUES (?, ?, ?, ?)",
            (entity_c, entity_d, "works_for", doc),
        )
        db.conn.execute(
            "INSERT INTO relationships (source_entity_id, target_entity_id, relationship_type, source_doc_id) VALUES (?, ?, ?, ?)",
            (entity_d, entity_a, "related_to", doc),
        )
        db.conn.commit()

        # Verify all relationships exist
        rels_before = db.conn.execute(
            "SELECT COUNT(*) FROM relationships WHERE source_doc_id = ?", (doc,)
        ).fetchone()[0]
        assert rels_before == 5

        # Delete document
        result = db.delete_document_with_entities(doc)

        assert result["success"] is True
        assert result["entities_deleted"] == 4

        # Verify all relationships are deleted
        rels_after = db.conn.execute(
            "SELECT COUNT(*) FROM relationships WHERE source_doc_id = ?", (doc,)
        ).fetchone()[0]
        assert rels_after == 0

        # Also verify no orphaned relationships by entity ID
        all_entity_ids = [entity_a, entity_b, entity_c, entity_d]
        for eid in all_entity_ids:
            orphaned = db.conn.execute(
                "SELECT COUNT(*) FROM relationships WHERE source_entity_id = ? OR target_entity_id = ?",
                (eid, eid),
            ).fetchone()[0]
            assert orphaned == 0

    def test_delete_document_without_entities(
        self, db, create_project, create_document, link_document_to_project
    ):
        """Test deleting a document that has no entities."""
        # Create project and document
        project = create_project(name="No Entities Test")
        doc = create_document(filename="empty.txt")
        link_document_to_project(doc, project)

        # Don't create any entities for this document

        # Delete document
        result = db.delete_document_with_entities(doc)

        assert result["success"] is True
        assert result["document_deleted"] is True
        assert result["entities_deleted"] == 0

        # Verify document is deleted
        doc_exists = db.conn.execute(
            "SELECT id FROM documents WHERE id = ?", (doc,)
        ).fetchone()
        assert doc_exists is None
