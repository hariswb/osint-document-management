"""
Unit tests for listing created projects.
"""

import pytest


class TestProjectList:
    """Test suite for listing all projects."""

    def test_list_all_projects_basic(self, db, create_project):
        """Test listing all projects with basic information."""
        project_ids = []
        for i in range(3):
            pid = create_project(name=f"Project {i}")
            project_ids.append(pid)

        results = db.conn.execute(
            "SELECT id, name, description, status FROM projects ORDER BY id"
        ).fetchall()

        assert len(results) == 3
        for i, row in enumerate(results):
            assert row[0] == project_ids[i]
            assert row[1] == f"Project {i}"
            assert row[3] == "active"

    def test_list_projects_with_document_counts(
        self, db, create_project, create_document, link_document_to_project
    ):
        """Test listing all projects with their document counts."""
        project1 = create_project(name="Project With Docs")
        project2 = create_project(name="Project Without Docs")
        project3 = create_project(name="Another Project")

        doc1 = create_document(filename="doc1.txt")
        doc2 = create_document(filename="doc2.txt")
        link_document_to_project(doc1, project1)
        link_document_to_project(doc2, project1)

        doc3 = create_document(filename="doc3.txt")
        link_document_to_project(doc3, project3)

        results = db.conn.execute(
            """
            SELECT p.id, p.name, COUNT(pd.doc_id) as doc_count
            FROM projects p
            LEFT JOIN project_documents pd ON p.id = pd.project_id
            GROUP BY p.id, p.name
            ORDER BY p.id
            """
        ).fetchall()

        assert len(results) == 3
        project_counts = {row[0]: row[2] for row in results}
        assert project_counts[project1] == 2
        assert project_counts[project2] == 0
        assert project_counts[project3] == 1

    def test_list_projects_with_entity_counts(
        self,
        db,
        create_project,
        create_document,
        create_entity,
        link_document_to_project,
    ):
        """Test listing all projects with their entity counts."""
        project1 = create_project(name="Project With Entities")
        project2 = create_project(name="Project Without Entities")

        doc1 = create_document(filename="doc1.txt")
        doc2 = create_document(filename="doc2.txt")
        link_document_to_project(doc1, project1)
        link_document_to_project(doc2, project1)

        create_entity(source_doc_id=doc1, name="Entity 1")
        create_entity(source_doc_id=doc1, name="Entity 2")
        create_entity(source_doc_id=doc2, name="Entity 3")

        results = db.conn.execute(
            """
            SELECT p.id, p.name, COUNT(DISTINCT e.id) as entity_count
            FROM projects p
            LEFT JOIN project_documents pd ON p.id = pd.project_id
            LEFT JOIN entities e ON e.source_doc_id = pd.doc_id
            GROUP BY p.id, p.name
            ORDER BY p.id
            """
        ).fetchall()

        assert len(results) == 2
        project_entity_counts = {row[0]: row[2] for row in results}
        assert project_entity_counts[project1] == 3
        assert project_entity_counts[project2] == 0

    def test_list_projects_order_by_created_date_desc(self, db, create_project):
        """Test listing projects ordered by creation date (newest first)."""
        import time

        project_ids = []
        for i in range(3):
            pid = create_project(name=f"Order Test {i}")
            project_ids.append(pid)
            time.sleep(0.05)

        results = db.conn.execute(
            "SELECT id, name FROM projects ORDER BY created_at DESC"
        ).fetchall()

        assert results[0][0] == project_ids[-1]
        assert results[1][0] == project_ids[1]
        assert results[2][0] == project_ids[0]

    def test_list_projects_order_by_updated_date(self, db, create_project):
        """Test listing projects ordered by last update date."""
        import time

        project1 = create_project(name="Project 1")
        time.sleep(0.1)
        project2 = create_project(name="Project 2")
        time.sleep(0.1)
        project3 = create_project(name="Project 3")

        time.sleep(0.1)
        db.conn.execute(
            "UPDATE projects SET name = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            ("Updated Project 1", project1),
        )
        db.conn.commit()

        results = db.conn.execute(
            "SELECT id, name FROM projects ORDER BY updated_at DESC"
        ).fetchall()

        assert results[0][0] == project1

    def test_list_empty_projects_table(self, db):
        """Test listing projects when none exist."""
        results = db.conn.execute("SELECT id, name FROM projects").fetchall()

        assert len(results) == 0
        assert results == []

    def test_list_projects_select_by_id(self, db, create_project):
        """Test selecting a specific project by ID from the list."""
        project1 = create_project(name="First Project")
        project2 = create_project(name="Second Project")
        project3 = create_project(name="Third Project")

        selected = db.conn.execute(
            "SELECT id, name, description, status FROM projects WHERE id = ?",
            (project2,),
        ).fetchone()

        assert selected is not None
        assert selected[0] == project2
        assert selected[1] == "Second Project"

    def test_list_projects_filter_by_status(self, db, create_project):
        """Test filtering the project list by status."""
        active1 = create_project(name="Active Project 1")
        active2 = create_project(name="Active Project 2")
        archived = create_project(name="Archived Project")

        db.conn.execute(
            "UPDATE projects SET status = 'archived' WHERE id = ?", (archived,)
        )
        db.conn.commit()

        results = db.conn.execute(
            "SELECT id, name, status FROM projects WHERE status = 'active'"
        ).fetchall()

        assert len(results) == 2
        ids = [row[0] for row in results]
        assert active1 in ids
        assert active2 in ids
        assert archived not in ids

    def test_list_projects_with_complete_metadata(
        self,
        db,
        create_project,
        create_document,
        create_entity,
        link_document_to_project,
    ):
        """Test listing projects with complete metadata for display."""
        project = create_project(name="Complete Project", description="A test project")

        doc1 = create_document(filename="doc1.txt")
        doc2 = create_document(filename="doc2.txt")
        link_document_to_project(doc1, project)
        link_document_to_project(doc2, project)

        create_entity(source_doc_id=doc1, name="Entity 1")
        create_entity(source_doc_id=doc1, name="Entity 2")
        create_entity(source_doc_id=doc2, name="Entity 3")

        result = db.conn.execute(
            """
            SELECT 
                p.id, 
                p.name, 
                p.description, 
                p.status,
                p.created_at,
                COUNT(DISTINCT pd.doc_id) as doc_count,
                COUNT(DISTINCT e.id) as entity_count
            FROM projects p
            LEFT JOIN project_documents pd ON p.id = pd.project_id
            LEFT JOIN entities e ON e.source_doc_id = pd.doc_id
            WHERE p.id = ?
            GROUP BY p.id, p.name, p.description, p.status, p.created_at
            """,
            (project,),
        ).fetchone()

        assert result is not None
        assert result[0] == project
        assert result[1] == "Complete Project"
        assert result[2] == "A test project"
        assert result[3] == "active"
        assert result[5] == 2
        assert result[6] == 3
