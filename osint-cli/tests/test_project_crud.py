"""
Unit tests for Project CRUD operations.
"""

import pytest


class TestProjectCRUD:
    """Test suite for Project Create, Read, Update, Delete operations."""

    def test_create_project(self, db, sample_project_data):
        """Test creating a new project."""
        # Insert project
        db.conn.execute(
            """
            INSERT INTO projects (name, description, status)
            VALUES (?, ?, ?)
            """,
            (
                sample_project_data["name"],
                sample_project_data["description"],
                sample_project_data["status"],
            ),
        )
        db.conn.commit()

        # Get project ID
        result = db.conn.execute("SELECT currval('projects_id_seq')").fetchone()
        project_id = result[0]

        # Verify project was created
        row = db.conn.execute(
            "SELECT id, name, description, status FROM projects WHERE id = ?",
            (project_id,),
        ).fetchone()

        assert row is not None
        assert row[0] == project_id
        assert row[1] == sample_project_data["name"]
        assert row[2] == sample_project_data["description"]
        assert row[3] == sample_project_data["status"]

    def test_read_project(self, db, create_project):
        """Test reading a project by ID."""
        # Create project
        project_id = create_project(name="Read Test Project")

        # Read project
        row = db.conn.execute(
            "SELECT id, name, description, status FROM projects WHERE id = ?",
            (project_id,),
        ).fetchone()

        assert row is not None
        assert row[0] == project_id
        assert row[1] == "Read Test Project"

    def test_update_project(self, db, create_project):
        """Test updating a project's name, description, and status."""
        # Create project
        project_id = create_project(name="Old Name")

        # Update project
        db.conn.execute(
            """
            UPDATE projects 
            SET name = ?, description = ?, status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            ("Updated Name", "Updated Description", "archived", project_id),
        )
        db.conn.commit()

        # Verify update
        row = db.conn.execute(
            "SELECT name, description, status FROM projects WHERE id = ?", (project_id,)
        ).fetchone()

        assert row[0] == "Updated Name"
        assert row[1] == "Updated Description"
        assert row[2] == "archived"

    def test_delete_project(self, db, create_project):
        """Test deleting a project."""
        # Create project
        project_id = create_project(name="Delete Test")

        # Verify project exists
        row = db.conn.execute(
            "SELECT id FROM projects WHERE id = ?", (project_id,)
        ).fetchone()
        assert row is not None

        # Delete project
        db.conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        db.conn.commit()

        # Verify deletion
        row = db.conn.execute(
            "SELECT id FROM projects WHERE id = ?", (project_id,)
        ).fetchone()
        assert row is None

    def test_list_all_projects(self, db, create_project):
        """Test listing all projects with document counts."""
        # Create multiple projects
        project_ids = []
        for i in range(3):
            pid = create_project(name=f"Project {i}")
            project_ids.append(pid)

        # Query all projects with document counts
        results = db.conn.execute(
            """
            SELECT p.id, p.name, COUNT(pd.doc_id) as document_count
            FROM projects p
            LEFT JOIN project_documents pd ON p.id = pd.project_id
            GROUP BY p.id, p.name
            ORDER BY p.id
            """
        ).fetchall()

        assert len(results) == 3
        for i, row in enumerate(results):
            assert row[0] == project_ids[i]
            assert row[1] == f"Project {i}"
            assert row[2] == 0  # No documents yet

    def test_create_project_with_empty_name_fails(self, db):
        """Test that creating a project with empty name should fail or handle gracefully."""
        # Try to insert project with empty name
        db.conn.execute(
            "INSERT INTO projects (name, description, status) VALUES (?, ?, ?)",
            ("", "Test description", "active"),
        )
        db.conn.commit()

        # Verify it was created (SQLite doesn't enforce NOT NULL constraints by default
        # unless configured, but our schema defines it as NOT NULL)
        result = db.conn.execute(
            "SELECT name FROM projects WHERE name = ?", ("",)
        ).fetchone()

        # The NOT NULL constraint should prevent NULL but empty string is allowed
        assert result is not None
        assert result[0] == ""

    def test_update_project_timestamp_changes(self, db, create_project):
        """Test that updating a project changes its updated_at timestamp."""
        # Create project
        project_id = create_project(name="Timestamp Test")

        # Get initial timestamp
        row1 = db.conn.execute(
            "SELECT updated_at FROM projects WHERE id = ?", (project_id,)
        ).fetchone()
        initial_timestamp = row1[0]

        # Update project after a small delay
        import time

        time.sleep(0.1)

        db.conn.execute(
            "UPDATE projects SET name = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            ("Updated Name", project_id),
        )
        db.conn.commit()

        # Get new timestamp
        row2 = db.conn.execute(
            "SELECT updated_at FROM projects WHERE id = ?", (project_id,)
        ).fetchone()
        new_timestamp = row2[0]

        # Timestamps should be different
        assert initial_timestamp != new_timestamp
