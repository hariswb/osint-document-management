"""FastAPI backend server for OSINT NER Tool."""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from database import DatabaseManager
from search import SearchEngine
from scraper import AdaptiveScraper
from ner_extractor import IndonesianNERExtractor
from entity_resolver import EntityResolver, AliasManager
from relationship_extractor import RelationshipExtractor, RelationshipStore

app = FastAPI(
    title="OSINT NER API",
    description="Backend API for OSINT NER Desktop Application",
    version="0.1.0",
)

# Enable CORS for Tauri frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:1420", "tauri://localhost"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
db_manager = DatabaseManager()
search_engine = SearchEngine()
scraper = AdaptiveScraper()
ner_extractor = IndonesianNERExtractor()
entity_resolver = EntityResolver()
alias_manager = AliasManager(db_manager)
relationship_extractor = RelationshipExtractor()
relationship_store = RelationshipStore(db_manager)


# Pydantic models
class SearchResult(BaseModel):
    id: int
    title: str
    href: str
    body: str
    source: str


class Entity(BaseModel):
    id: int
    name: str
    entity_type: str
    confidence: Optional[float] = None
    source_doc_id: Optional[int] = None
    created_at: Optional[str] = None


class Relationship(BaseModel):
    id: int
    source_entity_id: int
    target_entity_id: int
    source_name: str
    target_name: str
    relationship_type: str
    confidence: Optional[float] = None
    evidence: Optional[str] = None
    source_doc_id: Optional[int] = None
    created_at: str


class EntityAlias(BaseModel):
    id: int
    entity_id: int
    alias_name: str
    confidence: Optional[float] = None
    created_at: str


class Document(BaseModel):
    id: int
    filename: str
    file_path: str
    file_hash: Optional[str] = None
    doc_type: Optional[str] = None
    processed_at: str


class EntityDetails(BaseModel):
    entity: Entity
    relationships: List[Relationship]
    aliases: List[EntityAlias]
    documents: List[Document]
    coOccurring: List[Entity]


class ScrapedArticle(BaseModel):
    url: str
    title: str
    content: str
    author: Optional[str] = None
    publish_date: Optional[str] = None
    word_count: int


class ProcessRequest(BaseModel):
    query: str
    max_results: int = 5
    region: str = "id-id"
    provider: str = "duckduckgo"


class ProcessResponse(BaseModel):
    success: bool
    message: str
    articles_processed: int
    entities_extracted: int


class UpdateEntityRequest(BaseModel):
    name: Optional[str] = None
    entity_type: Optional[str] = None


class DuplicateGroup(BaseModel):
    entity1: Dict
    entity2: Dict
    confidence: float
    suggested_action: str


class SearchResultItem(BaseModel):
    id: int
    title: str
    href: str
    body: str
    source: str
    domain: Optional[str] = None
    publish_date: Optional[str] = None


class AddSearchResultsRequest(BaseModel):
    project_id: int
    results: List[SearchResultItem]
    auto_process: bool = False


class AddSearchResultsResponse(BaseModel):
    success: bool
    message: str
    documents_added: int
    duplicates_skipped: int
    doc_ids: List[int]


class DocumentProcessRequest(BaseModel):
    ner_enabled: bool = True
    extract_relationships: bool = True
    entity_types: Optional[List[str]] = None


class DocumentProcessResponse(BaseModel):
    success: bool
    message: str
    entities_extracted: int
    doc_id: int


class BatchProcessRequest(BaseModel):
    doc_ids: List[int]
    options: DocumentProcessRequest = DocumentProcessRequest()


class BatchProcessResponse(BaseModel):
    success: bool
    message: str
    documents_processed: int
    total_entities_extracted: int
    errors: List[str]


# API Routes
@app.get("/")
async def root():
    return {"message": "OSINT NER API", "version": "0.1.0"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    ner_status = "loaded" if ner_extractor._loaded else "not_loaded"
    return {"status": "healthy", "database": "connected", "ner_model": ner_status}


@app.post("/api/ner/load")
async def load_ner_model():
    """Preload the NER model."""
    try:
        if not ner_extractor._loaded:
            ner_extractor.load_model()
        return {"success": True, "message": "NER model loaded successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to load NER model: {str(e)}"
        )


@app.get("/api/stats")
async def get_stats():
    """Get database statistics."""
    try:
        entity_count = db_manager.get_entity_count()
        doc_count = db_manager.get_document_count()
        return {
            "entities": entity_count,
            "documents": doc_count,
            "relationships": 0,  # TODO: implement
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/entities", response_model=List[Entity])
async def get_entities(
    entity_type: Optional[str] = None,
    project_id: Optional[int] = None,
    limit: int = 100,
    offset: int = 0,
):
    """Get entities from database, optionally filtered by project."""
    try:
        if project_id:
            # Get entities from specific project
            query = """
                SELECT DISTINCT e.id, e.name, e.entity_type, e.confidence, e.source_doc_id, e.created_at
                FROM entities e
                JOIN project_documents pd ON e.source_doc_id = pd.doc_id
                WHERE pd.project_id = ?
            """
            params: List = [project_id]

            if entity_type:
                query += " AND e.entity_type = ?"
                params.append(entity_type)

            query += " ORDER BY e.created_at DESC LIMIT ?"
            params.append(limit)

            cursor = db_manager.conn.execute(query, params)
            results = cursor.fetchall()
        else:
            results = db_manager.get_entities(entity_type=entity_type, limit=limit)

        entities = []
        for row in results:
            entities.append(
                Entity(
                    id=row[0],
                    name=row[1],
                    entity_type=row[2],
                    confidence=row[3],
                    source_doc_id=row[4],
                    created_at=str(row[5]) if row[5] else None,
                )
            )
        return entities
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/search")
async def search_web(request: ProcessRequest):
    """Search the web using configured provider (DuckDuckGo or Google)."""
    try:
        # Create search engine with specified region and provider
        region = request.region if request.region else "id-id"
        provider = request.provider if request.provider else "duckduckgo"
        engine = SearchEngine(
            max_results=request.max_results, region=region, provider=provider
        )
        results = engine.search(request.query, max_results=request.max_results)

        # Enrich results with domain and date
        enriched_results = []
        for i, r in enumerate(results[:10]):  # Max 10 results
            from urllib.parse import urlparse

            domain = urlparse(r.href).netloc
            if domain.startswith("www."):
                domain = domain[4:]

            enriched_results.append(
                {
                    "id": i,
                    "title": r.title,
                    "href": r.href,
                    "body": r.body,
                    "source": r.source,
                    "domain": domain,
                    "publish_date": None,  # Will be populated during scraping
                }
            )

        return {
            "query": request.query,
            "count": len(enriched_results),
            "results": enriched_results,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/scrape")
async def scrape_url(url: str):
    """Scrape a single URL."""
    try:
        article = scraper.scrape(url)
        if not article:
            raise HTTPException(status_code=404, detail="Failed to scrape URL")

        return {
            "url": article.url,
            "title": article.title,
            "content": article.content[:2000],  # Limit content
            "author": article.author,
            "publish_date": article.publish_date,
            "word_count": article.word_count,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/extract", response_model=List[dict])
async def extract_entities(text: str):
    """Extract entities from text."""
    try:
        entities = ner_extractor.extract(text)
        return [
            {
                "text": e.text,
                "entity_type": e.entity_type,
                "start": e.start,
                "end": e.end,
                "confidence": e.confidence,
            }
            for e in entities
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/process", response_model=ProcessResponse)
async def process_query(request: ProcessRequest):
    """Full pipeline: Search → Scrape → Extract → Store."""
    try:
        # Step 1: Search with specified region
        region = request.region if request.region else "id-id"
        engine = SearchEngine(max_results=request.max_results, region=region)
        search_results = engine.search(request.query, max_results=request.max_results)

        # Step 2: Scrape
        articles = []
        for result in search_results:
            article = scraper.scrape(result.href)
            if article:
                articles.append(article)

        # Step 3: Extract entities
        all_entities = []
        for article in articles:
            entities = ner_extractor.extract(article.content[:3000])
            all_entities.extend(entities)

        # Deduplicate
        unique_entities = list(
            {(e.text.lower(), e.entity_type): e for e in all_entities}.values()
        )

        # Step 4: Store
        stored_count = 0
        for entity in unique_entities:
            db_manager.insert_entity(
                name=entity.text,
                entity_type=entity.entity_type,
                confidence=entity.confidence,
            )
            stored_count += 1

        return ProcessResponse(
            success=True,
            message=f"Processed {len(articles)} articles",
            articles_processed=len(articles),
            entities_extracted=stored_count,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload and process a document."""
    try:
        # TODO: Implement document processing
        content = await file.read()
        return {
            "filename": file.filename,
            "size": len(content),
            "message": "Document uploaded successfully",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/entities/{entity_id}", response_model=EntityDetails)
async def get_entity_details(entity_id: int):
    """Get detailed information about an entity including relationships and aliases."""
    try:
        # Get entity
        entity_row = db_manager.conn.execute(
            "SELECT id, name, entity_type, confidence, source_doc_id, created_at FROM entities WHERE id = ?",
            (entity_id,),
        ).fetchone()

        if not entity_row:
            raise HTTPException(status_code=404, detail="Entity not found")

        entity = Entity(
            id=entity_row[0],
            name=entity_row[1],
            entity_type=entity_row[2],
            confidence=entity_row[3],
            source_doc_id=entity_row[4],
            created_at=str(entity_row[5]),
        )

        # Get relationships
        rels = relationship_store.get_relationships(entity_id=entity_id)
        relationships = [Relationship(**rel) for rel in rels]

        # Get aliases
        aliases_data = alias_manager.get_aliases(entity_id)
        aliases = [EntityAlias(**alias) for alias in aliases_data]

        # Get documents
        docs_result = db_manager.conn.execute(
            """
            SELECT DISTINCT d.id, d.filename, d.file_path, d.file_hash, d.doc_type, d.processed_at
            FROM documents d
            JOIN entities e ON e.source_doc_id = d.id
            WHERE e.id = ?
            """,
            (entity_id,),
        ).fetchall()
        documents = [
            Document(
                id=row[0],
                filename=row[1],
                file_path=row[2],
                file_hash=row[3],
                doc_type=row[4],
                processed_at=str(row[5]),
            )
            for row in docs_result
        ]

        # Get co-occurring entities (simplified: entities from same document)
        cooc_result = db_manager.conn.execute(
            """
            SELECT DISTINCT e.id, e.name, e.entity_type, e.confidence, e.source_doc_id, e.created_at
            FROM entities e
            JOIN entities e2 ON e.source_doc_id = e2.source_doc_id
            WHERE e2.id = ? AND e.id != ?
            LIMIT 10
            """,
            (entity_id, entity_id),
        ).fetchall()
        cooccurring = [
            Entity(
                id=row[0],
                name=row[1],
                entity_type=row[2],
                confidence=row[3],
                source_doc_id=row[4],
                created_at=str(row[5]),
            )
            for row in cooc_result
        ]

        return EntityDetails(
            entity=entity,
            relationships=relationships,
            aliases=aliases,
            documents=documents,
            coOccurring=cooccurring,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/api/entities/{entity_id}")
async def update_entity(entity_id: int, request: UpdateEntityRequest):
    """Update an entity's name or type."""
    try:
        updates = []
        params = []

        if request.name:
            updates.append("name = ?")
            params.append(request.name)

        if request.entity_type:
            updates.append("entity_type = ?")
            params.append(request.entity_type)

        if updates:
            params.append(entity_id)
            db_manager.conn.execute(
                f"UPDATE entities SET {', '.join(updates)} WHERE id = ?", params
            )
            db_manager.conn.commit()

        # Return updated entity
        row = db_manager.conn.execute(
            "SELECT id, name, entity_type, confidence, source_doc_id, created_at FROM entities WHERE id = ?",
            (entity_id,),
        ).fetchone()

        return Entity(
            id=row[0],
            name=row[1],
            entity_type=row[2],
            confidence=row[3],
            source_doc_id=row[4],
            created_at=str(row[5]),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/entities/{entity_id}")
async def delete_entity(entity_id: int):
    """Delete an entity and its relationships."""
    try:
        # Delete relationships first
        db_manager.conn.execute(
            "DELETE FROM relationships WHERE source_entity_id = ? OR target_entity_id = ?",
            (entity_id, entity_id),
        )

        # Delete aliases
        db_manager.conn.execute(
            "DELETE FROM entity_aliases WHERE entity_id = ?", (entity_id,)
        )

        # Delete entity mentions
        db_manager.conn.execute(
            "DELETE FROM entity_mentions WHERE entity_id = ?", (entity_id,)
        )

        # Delete entity
        db_manager.conn.execute("DELETE FROM entities WHERE id = ?", (entity_id,))

        db_manager.conn.commit()
        return {"success": True, "message": "Entity deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/relationships")
async def get_relationships(entity_id: Optional[int] = None):
    """Get relationships, optionally filtered by entity."""
    try:
        rels = relationship_store.get_relationships(entity_id=entity_id)
        return rels
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/duplicates")
async def find_duplicates():
    """Find potential duplicate entities."""
    try:
        duplicates = alias_manager.find_duplicates()
        return duplicates
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/entities/{target_id}/merge/{source_id}")
async def merge_entities(target_id: int, source_id: int):
    """Merge source entity into target entity."""
    try:
        success = alias_manager.merge_entities(target_id, source_id)
        if success:
            return {"success": True, "message": "Entities merged successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to merge entities")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Project management endpoints
@app.get("/api/projects")
async def get_projects():
    """Get all projects."""
    try:
        results = db_manager.conn.execute(
            """
            SELECT p.id, p.name, p.description, p.status, p.created_at, p.updated_at,
                   COUNT(pd.doc_id) as document_count
            FROM projects p
            LEFT JOIN project_documents pd ON p.id = pd.project_id
            GROUP BY p.id, p.name, p.description, p.status, p.created_at, p.updated_at
            ORDER BY p.updated_at DESC
            """
        ).fetchall()

        return [
            {
                "id": row[0],
                "name": row[1],
                "description": row[2],
                "status": row[3],
                "created_at": str(row[4]),
                "updated_at": str(row[5]),
                "document_count": row[6],
            }
            for row in results
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/projects")
async def create_project(request: dict):
    """Create a new project."""
    try:
        db_manager.conn.execute(
            """
            INSERT INTO projects (name, description, status)
            VALUES (?, ?, ?)
            """,
            (request.get("name"), request.get("description", ""), "active"),
        )
        db_manager.conn.commit()

        result = db_manager.conn.execute("SELECT currval('projects_id_seq')").fetchone()
        project_id = result[0]

        # Return the created project
        row = db_manager.conn.execute(
            "SELECT id, name, description, status, created_at, updated_at FROM projects WHERE id = ?",
            (project_id,),
        ).fetchone()

        return {
            "id": row[0],
            "name": row[1],
            "description": row[2],
            "status": row[3],
            "created_at": str(row[4]),
            "updated_at": str(row[5]),
            "document_count": 0,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/api/projects/{project_id}")
async def update_project(project_id: int, request: dict):
    """Update a project."""
    try:
        updates = []
        params = []

        if "name" in request:
            updates.append("name = ?")
            params.append(request["name"])

        if "description" in request:
            updates.append("description = ?")
            params.append(request["description"])

        if "status" in request:
            updates.append("status = ?")
            params.append(request["status"])

        if updates:
            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(project_id)
            db_manager.conn.execute(
                f"UPDATE projects SET {', '.join(updates)} WHERE id = ?", params
            )
            db_manager.conn.commit()

        # Return updated project
        row = db_manager.conn.execute(
            """
            SELECT p.id, p.name, p.description, p.status, p.created_at, p.updated_at,
                   COUNT(pd.doc_id) as document_count
            FROM projects p
            LEFT JOIN project_documents pd ON p.id = pd.project_id
            WHERE p.id = ?
            GROUP BY p.id
            """,
            (project_id,),
        ).fetchone()

        return {
            "id": row[0],
            "name": row[1],
            "description": row[2],
            "status": row[3],
            "created_at": str(row[4]),
            "updated_at": str(row[5]),
            "document_count": row[6],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/projects/{project_id}")
async def delete_project(project_id: int):
    """Delete a project."""
    try:
        # Remove project-document associations first
        db_manager.conn.execute(
            "DELETE FROM project_documents WHERE project_id = ?", (project_id,)
        )

        # Delete project
        db_manager.conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        db_manager.conn.commit()

        return {"success": True, "message": "Project deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/projects/{project_id}")
async def get_project(project_id: int):
    """Get project details with documents and entities."""
    try:
        # Get project
        row = db_manager.conn.execute(
            """
            SELECT p.id, p.name, p.description, p.status, p.created_at, p.updated_at
            FROM projects p
            WHERE p.id = ?
            """,
            (project_id,),
        ).fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Project not found")

        # Get project documents
        docs_result = db_manager.conn.execute(
            """
            SELECT d.id, d.filename, d.file_path, d.file_hash, d.doc_type, d.processed_at,
                   d.status, d.entity_count, d.domain
            FROM documents d
            JOIN project_documents pd ON d.id = pd.doc_id
            WHERE pd.project_id = ?
            ORDER BY d.created_at DESC
            """,
            (project_id,),
        ).fetchall()

        documents = [
            {
                "id": r[0],
                "filename": r[1],
                "file_path": r[2],
                "file_hash": r[3],
                "doc_type": r[4],
                "processed_at": str(r[5]),
                "status": r[6] or "pending",
                "entity_count": r[7] or 0,
                "domain": r[8],
            }
            for r in docs_result
        ]

        # Get entities from project documents
        entities_result = db_manager.conn.execute(
            """
            SELECT DISTINCT e.id, e.name, e.entity_type, e.confidence, e.source_doc_id, e.created_at
            FROM entities e
            JOIN project_documents pd ON e.source_doc_id = pd.doc_id
            WHERE pd.project_id = ?
            LIMIT 100
            """,
            (project_id,),
        ).fetchall()

        entities = [
            {
                "id": r[0],
                "name": r[1],
                "entity_type": r[2],
                "confidence": r[3],
                "source_doc_id": r[4],
                "created_at": str(r[5]),
            }
            for r in entities_result
        ]

        return {
            "id": row[0],
            "name": row[1],
            "description": row[2],
            "status": row[3],
            "created_at": str(row[4]),
            "updated_at": str(row[5]),
            "documents": documents,
            "entities": entities,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/projects/{project_id}/documents/{doc_id}")
async def add_document_to_project(project_id: int, doc_id: int):
    """Add a document to a project."""
    try:
        db_manager.conn.execute(
            """
            INSERT INTO project_documents (project_id, doc_id)
            VALUES (?, ?)
            ON CONFLICT DO NOTHING
            """,
            (project_id, doc_id),
        )

        # Update project timestamp
        db_manager.conn.execute(
            "UPDATE projects SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (project_id,),
        )

        db_manager.conn.commit()
        return {"success": True, "message": "Document added to project"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/projects/{project_id}/documents/{doc_id}")
async def remove_document_from_project(
    project_id: int, doc_id: int, cascade: bool = True
):
    """Remove a document from a project with optional cascade delete."""
    try:
        # Remove from project association first
        db_manager.conn.execute(
            "DELETE FROM project_documents WHERE project_id = ? AND doc_id = ?",
            (project_id, doc_id),
        )

        # Update project timestamp
        db_manager.conn.execute(
            "UPDATE projects SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (project_id,),
        )

        db_manager.conn.commit()

        # If cascade is enabled, delete document and all its entities
        if cascade:
            result = db_manager.delete_document_with_entities(doc_id)
            return {
                "success": True,
                "message": "Document removed from project and deleted with all associated entities",
                "cascade_result": result,
            }

        return {"success": True, "message": "Document removed from project"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/documents/{doc_id}/process", response_model=DocumentProcessResponse)
async def process_document(doc_id: int, request: DocumentProcessRequest):
    """Process a document to extract entities and relationships."""
    try:
        # Get document
        doc = db_manager.get_document(doc_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        doc_id_val, filename, file_path, file_hash, doc_type, processed_at = doc
        content = ""

        print(
            f"Processing document {doc_id_val}: {filename} (type: {doc_type}, path: {file_path})"
        )

        # Handle web documents (scrape from URL)
        if doc_type == "web" or (file_path and file_path.startswith("http")):
            print(f"Scraping URL: {file_path}")
            # Scrape the URL
            article = scraper.scrape(file_path)
            if article:
                content = article.content
                print(f"Scraped {len(content)} characters from URL")
                if not content or len(content.strip()) == 0:
                    # Content is empty but scraping succeeded - mark as processed with 0 entities
                    print("Warning: Scraped content is empty")
                    content = ""
            else:
                # Scraping failed completely
                raise HTTPException(
                    status_code=400,
                    detail=f"Unable to scrape this website. The site may block automated access or require JavaScript. Try a different URL or check if the site is accessible.",
                )
        else:
            # Read local file
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                print(f"Read {len(content)} characters from file")
            except Exception as e:
                raise HTTPException(
                    status_code=400, detail=f"Failed to read document: {str(e)}"
                )

        entities_extracted = 0

        # Extract entities if NER is enabled
        if request.ner_enabled:
            print("Extracting entities with NER...")
            try:
                entities = ner_extractor.extract(content)
                print(f"NER extracted {len(entities)} entities")

                # Filter by entity types if specified
                if request.entity_types:
                    entities = [
                        e for e in entities if e.entity_type in request.entity_types
                    ]
                    print(f"After filtering: {len(entities)} entities")

                # Store entities
                for entity in entities:
                    db_manager.insert_entity(
                        name=entity.text,
                        entity_type=entity.entity_type,
                        confidence=entity.confidence,
                        source_doc_id=doc_id_val,
                    )
                    entities_extracted += 1

                print(f"Stored {entities_extracted} entities")
            except Exception as e:
                print(f"NER extraction error: {e}")
                raise HTTPException(
                    status_code=500, detail=f"NER extraction failed: {str(e)}"
                )

        # Update document processed timestamp and status
        db_manager.update_document_processed_at(doc_id_val)
        db_manager.update_document_status(doc_id_val, "completed", entities_extracted)

        return DocumentProcessResponse(
            success=True,
            message=f"Document processed successfully. Extracted {entities_extracted} entities.",
            entities_extracted=entities_extracted,
            doc_id=doc_id_val,
        )
    except HTTPException:
        # Update status to error
        try:
            db_manager.update_document_status(doc_id, "error")
        except:
            pass
        raise
    except Exception as e:
        print(f"Processing error: {e}")
        # Update status to error
        try:
            db_manager.update_document_status(doc_id, "error")
        except:
            pass
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/documents/batch-process", response_model=BatchProcessResponse)
async def batch_process_documents(request: BatchProcessRequest):
    """Process multiple documents at once."""
    try:
        total_entities = 0
        documents_processed = 0
        errors = []

        for doc_id in request.doc_ids:
            try:
                # Get document
                doc = db_manager.get_document(doc_id)
                if not doc:
                    errors.append(f"Document {doc_id} not found")
                    continue

                doc_id_val, filename, file_path, file_hash, doc_type, processed_at = doc
                content = ""

                # Handle web documents (scrape from URL)
                if doc_type == "web" or file_path.startswith("http"):
                    # Scrape the URL
                    article = scraper.scrape(file_path)
                    if article:
                        content = article.content
                    else:
                        errors.append(
                            f"Failed to scrape document {doc_id}: {file_path}"
                        )
                        db_manager.update_document_status(doc_id, "error")
                        continue
                else:
                    # Read local file
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                    except Exception as e:
                        errors.append(f"Failed to read document {doc_id}: {str(e)}")
                        db_manager.update_document_status(doc_id, "error")
                        continue

                # Update status to processing
                db_manager.update_document_status(doc_id, "processing")

                # Extract entities if NER is enabled
                entities_extracted = 0
                if request.options.ner_enabled:
                    entities = ner_extractor.extract(content)

                    # Filter by entity types if specified
                    if request.options.entity_types:
                        entities = [
                            e
                            for e in entities
                            if e.entity_type in request.options.entity_types
                        ]

                    # Store entities
                    for entity in entities:
                        db_manager.insert_entity(
                            name=entity.text,
                            entity_type=entity.entity_type,
                            confidence=entity.confidence,
                            source_doc_id=doc_id,
                        )
                        entities_extracted += 1
                        total_entities += 1

                # Update document processed timestamp and status
                db_manager.update_document_processed_at(doc_id)
                db_manager.update_document_status(
                    doc_id, "completed", entities_extracted
                )
                documents_processed += 1

            except Exception as e:
                errors.append(f"Error processing document {doc_id}: {str(e)}")
                try:
                    db_manager.update_document_status(doc_id, "error")
                except:
                    pass

        return BatchProcessResponse(
            success=True,
            message=f"Batch processing complete. Processed {documents_processed} documents.",
            documents_processed=documents_processed,
            total_entities_extracted=total_entities,
            errors=errors,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/network")
async def get_network_data(
    project_id: Optional[int] = None,
    entity_types: Optional[str] = None,
    exclude_entities: Optional[str] = None,
):
    """Get all entities and relationships for network graph visualization.

    Args:
        project_id: Optional project ID to filter entities
        entity_types: Comma-separated list of entity types to include (e.g., "PER,ORG,GPE")
        exclude_entities: Comma-separated list of entity names to exclude
    """
    try:
        # Parse entity types filter
        type_filter = None
        if entity_types:
            type_filter = [t.strip().upper() for t in entity_types.split(",")]

        # Parse exclude entities filter
        exclude_filter = None
        if exclude_entities:
            exclude_filter = [e.strip().lower() for e in exclude_entities.split(",")]

        # One canonical node per unique (name, entity_type) using MIN(id)
        if project_id:
            query = """
                SELECT MIN(e.id) as id, MIN(e.name) as name, e.entity_type, MAX(e.confidence) as confidence
                FROM entities e
                JOIN project_documents pd ON e.source_doc_id = pd.doc_id
                WHERE pd.project_id = ?
            """
            params = [project_id]
        else:
            query = """
                SELECT MIN(id) as id, MIN(name) as name, entity_type, MAX(confidence) as confidence
                FROM entities
                WHERE 1=1
            """
            params = []

        if type_filter:
            type_placeholders = ", ".join(["?"] * len(type_filter))
            query += f" AND {'e.' if project_id else ''}entity_type IN ({type_placeholders})"
            params.extend(type_filter)

        query += f" GROUP BY LOWER({'e.' if project_id else ''}name), {'e.' if project_id else ''}entity_type"

        # Execute entity query
        cursor = db_manager.conn.execute(query, params)
        entity_rows = cursor.fetchall()

        # Process entities and apply exclusion filter
        nodes = []
        entity_ids = set()

        for row in entity_rows:
            entity_id = row[0]
            name = row[1]
            entity_type = row[2]
            confidence = row[3]

            # Skip if in exclude list
            if exclude_filter and name.lower() in exclude_filter:
                continue

            entity_ids.add(entity_id)
            nodes.append(
                {
                    "id": str(entity_id),
                    "name": name,
                    "type": entity_type,
                    "confidence": confidence,
                }
            )

        if not entity_ids:
            return {"nodes": [], "links": []}

        # Derive co-occurrence edges using name-based join mapped to canonical IDs.
        # Two entities are connected if they share a document; MIN(id) gives the same
        # canonical ID used in the nodes query above.
        if project_id:
            cooc_query = """
                SELECT
                    MIN(e1.id) as source_id,
                    MIN(e2.id) as target_id,
                    COUNT(DISTINCT e1.source_doc_id) as doc_count
                FROM entities e1
                JOIN entities e2
                    ON e1.source_doc_id = e2.source_doc_id
                    AND LOWER(e1.name) < LOWER(e2.name)
                JOIN project_documents pd ON e1.source_doc_id = pd.doc_id
                WHERE pd.project_id = ?
                GROUP BY LOWER(e1.name), e1.entity_type, LOWER(e2.name), e2.entity_type
            """
            cooc_params = [project_id]
        else:
            cooc_query = """
                SELECT
                    MIN(e1.id) as source_id,
                    MIN(e2.id) as target_id,
                    COUNT(DISTINCT e1.source_doc_id) as doc_count
                FROM entities e1
                JOIN entities e2
                    ON e1.source_doc_id = e2.source_doc_id
                    AND LOWER(e1.name) < LOWER(e2.name)
                GROUP BY LOWER(e1.name), e1.entity_type, LOWER(e2.name), e2.entity_type
            """
            cooc_params = []

        cooc_cursor = db_manager.conn.execute(cooc_query, cooc_params)
        cooc_rows = cooc_cursor.fetchall()

        # Only emit edges where both endpoints survived type/exclude filtering
        links = [
            {
                "source": str(row[0]),
                "target": str(row[1]),
                "relationship_type": "co-occurrence",
                "confidence": min(1.0, 0.5 + (row[2] - 1) * 0.1),
            }
            for row in cooc_rows
            if row[0] in entity_ids and row[1] in entity_ids
        ]

        return {"nodes": nodes, "links": links}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/search/add-to-project", response_model=AddSearchResultsResponse)
async def add_search_results_to_project(request: AddSearchResultsRequest):
    """Add search results to a project as pending documents.

    Skips duplicates based on URL.
    Optionally auto-process documents after adding.
    """
    try:
        # Verify project exists
        project = db_manager.conn.execute(
            "SELECT id FROM projects WHERE id = ?", (request.project_id,)
        ).fetchone()

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        doc_ids = []
        duplicates_skipped = 0
        processed_count = 0
        total_entities = 0

        for result in request.results:
            # Check if document with this URL already exists in project
            if db_manager.document_exists_by_url(result.href, request.project_id):
                duplicates_skipped += 1
                continue

            # Create document with pending status
            doc_id = db_manager.insert_document(
                filename=result.title or "Untitled",
                file_path=result.href,  # Store URL as file_path for web docs
                url=result.href,
                domain=result.domain,
                publish_date=result.publish_date,
                doc_type="web",
                status="pending",
            )

            # Associate with project
            db_manager.add_document_to_project(doc_id, request.project_id)
            doc_ids.append(doc_id)

            # Auto-process if enabled
            if request.auto_process and doc_id:
                try:
                    # Get document
                    doc = db_manager.get_document(doc_id)
                    if doc:
                        (
                            doc_id_val,
                            filename,
                            file_path,
                            file_hash,
                            doc_type,
                            processed_at,
                        ) = doc

                        # Scrape the URL
                        article = scraper.scrape(file_path)
                        if article and article.content:
                            # Extract entities
                            entities = ner_extractor.extract(article.content)

                            # Store entities
                            entities_count = 0
                            for entity in entities:
                                db_manager.insert_entity(
                                    name=entity.text,
                                    entity_type=entity.entity_type,
                                    confidence=entity.confidence,
                                    source_doc_id=doc_id_val,
                                )
                                entities_count += 1

                            # Update document status
                            db_manager.update_document_processed_at(doc_id_val)
                            db_manager.update_document_status(
                                doc_id_val, "completed", entities_count
                            )
                            processed_count += 1
                            total_entities += entities_count
                except Exception as e:
                    print(f"Auto-processing error for doc {doc_id}: {e}")
                    # Mark as error but continue
                    try:
                        db_manager.update_document_status(doc_id, "error")
                    except:
                        pass

        # Update project timestamp
        db_manager.conn.execute(
            "UPDATE projects SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (request.project_id,),
        )
        db_manager.conn.commit()

        # Build appropriate message
        if request.auto_process:
            message = f"Added {len(doc_ids)} documents, processed {processed_count} with {total_entities} entities"
        else:
            message = f"Added {len(doc_ids)} documents to project"

        return AddSearchResultsResponse(
            success=True,
            message=message,
            documents_added=len(doc_ids),
            duplicates_skipped=duplicates_skipped,
            doc_ids=doc_ids,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
