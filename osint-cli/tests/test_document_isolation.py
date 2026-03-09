"""
Unit tests for document isolation - projects should only access their own documents.
"""

import pytest


class TestDocumentIsolation:
    """Test suite for ensuring project document isolation."""

    def test_project_can_only_access_own_documents(
        self, db, create_project, create_document, link_document_to_project
    ):
        """Test that a project can only access its own documents, not others."""
        # Create two projects
        project_a = create_project(name="Project A")
        project_b = create_project(name="Project B")

        # Create documents for each project
        doc_a1 = create_document(filename="doc_a1.txt")
        doc_a2 = create_document(filename="doc_a2.txt")
        doc_b1 = create_document(filename="doc_b1.txt")

        # Link documents to projects
        link_document_to_project(doc_a1, project_a)
        link_document_to_project(doc_a2, project_a)
        link_document_to_project(doc_b1, project_b)

        # Query documents for Project A
        docs_project_a = db.conn.execute(
            """
            SELECT d.id, d.filename
            FROM documents d
            JOIN project_documents pd ON d.id = pd.doc_id
            WHERE pd.project_id = ?
            """,
            (project_a,),
        ).fetchall()

        # Query documents for Project B
        docs_project_b = db.conn.execute(
            """
            SELECT d.id, d.filename
            FROM documents d
            JOIN project_documents pd ON d.id = pd.doc_id
            WHERE pd.project_id = ?
            """,
            (project_b,),
        ).fetchall()

        # Project A should have 2 documents
        assert len(docs_project_a) == 2
        doc_a_ids = [d[0] for d in docs_project_a]
        assert doc_a1 in doc_a_ids
        assert doc_a2 in doc_a_ids
        assert doc_b1 not in doc_a_ids  # Project B's doc should NOT be in Project A

        # Project B should have 1 document
        assert len(docs_project_b) == 1
        assert docs_project_b[0][0] == doc_b1

    def test_project_cannot_see_another_projects_entities(
        self,
        db,
        create_project,
        create_document,
        create_entity,
        link_document_to_project,
    ):
        """Test that entities from one project's documents are not visible to another project."""
        # Create two projects
        project_a = create_project(name="Project A")
        project_b = create_project(name="Project B")

        # Create documents
        doc_a = create_document(filename="doc_a.txt")
        doc_b = create_document(filename="doc_b.txt")

        # Link to respective projects
        link_document_to_project(doc_a, project_a)
        link_document_to_project(doc_b, project_b)

        # Create entities for each document
        entity_a = create_entity(
            source_doc_id=doc_a, name="Entity A", entity_type="PERSON"
        )
        entity_b = create_entity(
            source_doc_id=doc_b, name="Entity B", entity_type="ORG"
        )

        # Query entities for Project A
        entities_project_a = db.conn.execute(
            """
            SELECT e.id, e.name, e.entity_type
            FROM entities e
            JOIN project_documents pd ON e.source_doc_id = pd.doc_id
            WHERE pd.project_id = ?
            """,
            (project_a,),
        ).fetchall()

        # Query entities for Project B
        entities_project_b = db.conn.execute(
            """
            SELECT e.id, e.name, e.entity_type
            FROM entities e
            JOIN project_documents pd ON e.source_doc_id = pd.doc_id
            WHERE pd.project_id = ?
            """,
            (project_b,),
        ).fetchall()

        # Project A should only see Entity A
        assert len(entities_project_a) == 1
        assert entities_project_a[0][0] == entity_a
        assert entities_project_a[0][1] == "Entity A"

        # Project B should only see Entity B
        assert len(entities_project_b) == 1
        assert entities_project_b[0][0] == entity_b
        assert entities_project_b[0][1] == "Entity B"

    def test_get_project_documents_method_isolates_correctly(
        self, db, create_project, create_document, link_document_to_project
    ):
        """Test that get_project_documents method properly isolates by project."""
        # Create projects
        project1 = create_project(name="Project 1")
        project2 = create_project(name="Project 2")

        # Create and link documents
        doc1 = create_document(filename="shared.txt")
        doc2 = create_document(filename="unique1.txt")
        doc3 = create_document(filename="unique2.txt")

        # Both projects share doc1, but have their own unique docs
        link_document_to_project(doc1, project1)
        link_document_to_project(doc1, project2)
        link_document_to_project(doc2, project1)
        link_document_to_project(doc3, project2)

        # Get documents for each project
        docs_p1 = db.get_project_documents(project1)
        docs_p2 = db.get_project_documents(project2)

        # Project 1 should have 2 documents
        assert len(docs_p1) == 2
        p1_ids = [d[0] for d in docs_p1]
        assert doc1 in p1_ids
        assert doc2 in p1_ids

        # Project 2 should have 2 documents
        assert len(docs_p2) == 2
        p2_ids = [d[0] for d in docs_p2]
        assert doc1 in p2_ids
        assert doc3 in p2_ids

    def test_document_exists_by_url_with_project_isolation(
        self, db, create_project, create_document, link_document_to_project
    ):
        """Test that document_exists_by_url respects project boundaries."""
        # Create projects
        project1 = create_project(name="Project 1")
        project2 = create_project(name="Project 2")

        # Create document with URL in project1
        url = "https://example.com/article"
        doc1 = create_document(filename="article.html", url=url)
        link_document_to_project(doc1, project1)

        # Check URL exists in project1
        exists_p1 = db.document_exists_by_url(url, project1)
        assert exists_p1 is True

        # Check URL does not exist in project2
        exists_p2 = db.document_exists_by_url(url, project2)
        assert exists_p2 is False

        # Check URL exists globally (without project_id)
        exists_global = db.document_exists_by_url(url)
        assert exists_global is True

    def test_entity_query_by_project_id_filters_correctly(
        self,
        db,
        create_project,
        create_document,
        create_entity,
        link_document_to_project,
    ):
        """Test that entity queries with project_id filter work correctly."""
        # Create projects
        project_x = create_project(name="Project X")
        project_y = create_project(name="Project Y")

        # Create documents and add to project
        doc_x = create_document(filename="doc_x.txt")
        doc_y = create_document(filename="doc_y.txt")

        link_document_to_project(doc_x, project_x)
        link_document_to_project(doc_y, project_y)

        # Create multiple entities per document
        create_entity(source_doc_id=doc_x, name="Person X1")
        create_entity(source_doc_id=doc_x, name="Person X2")
        create_entity(source_doc_id=doc_y, name="Person Y1")
        create_entity(source_doc_id=doc_y, name="Person Y2")
        create_entity(source_doc_id=doc_y, name="Person Y3")

        # Query entities for Project X
        entities_x = db.conn.execute(
            """
            SELECT e.id, e.name
            FROM entities e
            JOIN project_documents pd ON e.source_doc_id = pd.doc_id
            WHERE pd.project_id = ?
            """,
            (project_x,),
        ).fetchall()

        # Query entities for Project Y
        entities_y = db.conn.execute(
            """
            SELECT e.id, e.name
            FROM entities e
            JOIN project_documents pd ON e.source_doc_id = pd.doc_id
            WHERE pd.project_id = ?
            """,
            (project_y,),
        ).fetchall()

        # Verify counts
        assert len(entities_x) == 2  # Project X has 2 entities
        assert len(entities_y) == 3  # Project Y has 3 entities

        # Verify no cross-contamination
        x_names = [e[1] for e in entities_x]
        y_names = [e[1] for e in entities_y]

        for name in x_names:
            assert name not in y_names
        for name in y_names:
            assert name not in x_names

    def test_cross_project_relationship_query_isolation(
        self,
        db,
        create_project,
        create_document,
        create_entity,
        link_document_to_project,
    ):
        """Test that relationship queries are isolated by project."""
        # Create projects
        project1 = create_project(name="Project 1")
        project2 = create_project(name="Project 2")

        # Create documents
        doc1 = create_document(filename="doc1.txt")
        doc2 = create_document(filename="doc2.txt")

        link_document_to_project(doc1, project1)
        link_document_to_project(doc2, project2)

        # Create entities and relationships
        entity1 = create_entity(source_doc_id=doc1, name="Entity 1")
        entity2 = create_entity(source_doc_id=doc1, name="Entity 2")
        entity3 = create_entity(source_doc_id=doc2, name="Entity 3")
        entity4 = create_entity(source_doc_id=doc2, name="Entity 4")

        # Create relationships within each project
        db.conn.execute(
            """
            INSERT INTO relationships (source_entity_id, target_entity_id, relationship_type, source_doc_id)
            VALUES (?, ?, ?, ?)
            """,
            (entity1, entity2, "knows", doc1),
        )
        db.conn.execute(
            """
            INSERT INTO relationships (source_entity_id, target_entity_id, relationship_type, source_doc_id)
            VALUES (?, ?, ?, ?)
            """,
            (entity3, entity4, "works_with", doc2),
        )
        db.conn.commit()

        # Query relationships for Project 1
        rels_p1 = db.conn.execute(
            """
            SELECT r.id, r.source_entity_id, r.target_entity_id
            FROM relationships r
            JOIN project_documents pd ON r.source_doc_id = pd.doc_id
            WHERE pd.project_id = ?
            """,
            (project1,),
        ).fetchall()

        # Query relationships for Project 2
        rels_p2 = db.conn.execute(
            """
            SELECT r.id, r.source_entity_id, r.target_entity_id
            FROM relationships r
            JOIN project_documents pd ON r.source_doc_id = pd.doc_id
            WHERE pd.project_id = ?
            """,
            (project2,),
        ).fetchall()

        # Each project should only see its own relationships
        assert len(rels_p1) == 1
        assert rels_p1[0][1] == entity1
        assert rels_p1[0][2] == entity2

        assert len(rels_p2) == 1
        assert rels_p2[0][1] == entity3
        assert rels_p2[0][2] == entity4

    def test_document_removed_from_project_no_longer_accessible(
        self, db, create_project, create_document, link_document_to_project
    ):
        """Test that when a document is removed from a project, it's no longer accessible."""
        # Create project and document
        project = create_project(name="Test Project")
        doc = create_document(filename="temp.txt")

        # Link document to project
        link_document_to_project(doc, project)

        # Verify document is accessible
        docs = db.conn.execute(
            """
            SELECT d.id FROM documents d
            JOIN project_documents pd ON d.id = pd.doc_id
            WHERE pd.project_id = ?
            """,
            (project,),
        ).fetchall()
        assert len(docs) == 1

        # Remove document from project (but not delete document itself)
        db.conn.execute(
            "DELETE FROM project_documents WHERE project_id = ? AND doc_id = ?",
            (project, doc),
        )
        db.conn.commit()

        # Verify document is no longer accessible from project
        docs_after = db.conn.execute(
            """
            SELECT d.id FROM documents d
            JOIN project_documents pd ON d.id = pd.doc_id
            WHERE pd.project_id = ?
            """,
            (project,),
        ).fetchall()
        assert len(docs_after) == 0

        # But document still exists in database
        doc_exists = db.conn.execute(
            "SELECT id FROM documents WHERE id = ?", (doc,)
        ).fetchone()
        assert doc_exists is not None
