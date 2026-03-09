"""
Pytest configuration and shared fixtures for OSINT CLI tests.
"""

import os
import pytest
import tempfile
from pathlib import Path

# Add src to path for imports
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from database import DatabaseManager


@pytest.fixture
def temp_db_path():
    """Create a temporary database file path."""
    # Create a temporary directory and return a path within it
    # DuckDB will create the database file itself
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test.db")
    yield db_path
    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)
    if os.path.exists(temp_dir):
        os.rmdir(temp_dir)


@pytest.fixture
def db(temp_db_path):
    """Create a fresh database instance for each test."""
    db = DatabaseManager(db_path=temp_db_path)
    yield db
    db.close()


@pytest.fixture
def sample_project_data():
    """Sample project data for testing."""
    return {
        "name": "Test Project",
        "description": "A test project for unit testing",
        "status": "active",
    }


@pytest.fixture
def sample_document_data():
    """Sample document data for testing."""
    return {
        "filename": "test_doc.txt",
        "file_path": "/tmp/test_doc.txt",
        "file_hash": "abc123hash",
        "doc_type": "text",
        "url": "https://example.com/test",
        "domain": "example.com",
        "publish_date": "2024-01-01",
    }


@pytest.fixture
def sample_entity_data():
    """Sample entity data for testing."""
    return {"name": "John Doe", "entity_type": "PERSON", "confidence": 0.95}


@pytest.fixture
def create_project(db, sample_project_data):
    """Helper fixture to create a project."""

    def _create(name=None, description=None):
        data = sample_project_data.copy()
        if name:
            data["name"] = name
        if description:
            data["description"] = description

        db.conn.execute(
            "INSERT INTO projects (name, description, status) VALUES (?, ?, ?)",
            (data["name"], data["description"], data["status"]),
        )
        db.conn.commit()
        result = db.conn.execute("SELECT currval('projects_id_seq')").fetchone()
        return result[0]

    return _create


@pytest.fixture
def create_document(db, sample_document_data):
    """Helper fixture to create a document."""

    def _create(**kwargs):
        data = sample_document_data.copy()
        data.update(kwargs)

        doc_id = db.insert_document(
            filename=data["filename"],
            file_path=data["file_path"],
            file_hash=data.get("file_hash"),
            doc_type=data.get("doc_type"),
            url=data.get("url"),
            domain=data.get("domain"),
            publish_date=data.get("publish_date"),
            status=data.get("status", "pending"),
        )
        return doc_id

    return _create


@pytest.fixture
def create_entity(db, sample_entity_data):
    """Helper fixture to create an entity."""

    def _create(source_doc_id=None, **kwargs):
        data = sample_entity_data.copy()
        data.update(kwargs)

        entity_id = db.insert_entity(
            name=data["name"],
            entity_type=data["entity_type"],
            confidence=data.get("confidence"),
            source_doc_id=source_doc_id,
        )
        return entity_id

    return _create


@pytest.fixture
def link_document_to_project(db):
    """Helper fixture to link a document to a project."""

    def _link(doc_id, project_id):
        db.add_document_to_project(doc_id, project_id)

    return _link
