"""FastAPI backend server for OSINT NER Tool."""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from typing import List, Optional
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from database import DatabaseManager
from search import SearchEngine
from scraper import AdaptiveScraper
from ner_extractor import IndonesianNERExtractor

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
    confidence: Optional[float]
    source_doc_id: Optional[int]
    created_at: str


class ScrapedArticle(BaseModel):
    url: str
    title: str
    content: str
    author: Optional[str]
    publish_date: Optional[str]
    word_count: int


class ProcessRequest(BaseModel):
    query: str
    max_results: int = 5


class ProcessResponse(BaseModel):
    success: bool
    message: str
    articles_processed: int
    entities_extracted: int


# API Routes
@app.get("/")
async def root():
    return {"message": "OSINT NER API", "version": "0.1.0"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "database": "connected"}


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
    entity_type: Optional[str] = None, limit: int = 100, offset: int = 0
):
    """Get entities from database."""
    try:
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
    """Search the web using DuckDuckGo."""
    try:
        results = search_engine.search(request.query, max_results=request.max_results)
        return {
            "query": request.query,
            "count": len(results),
            "results": [
                {
                    "id": i,
                    "title": r.title,
                    "href": r.href,
                    "body": r.body,
                    "source": r.source,
                }
                for i, r in enumerate(results)
            ],
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
        # Step 1: Search
        search_results = search_engine.search(
            request.query, max_results=request.max_results
        )

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


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
