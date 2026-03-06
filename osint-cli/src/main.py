import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import typer
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from src.database import DatabaseManager
from src.search import SearchEngine
from src.scraper import AdaptiveScraper
from src.ner_extractor import IndonesianNERExtractor
from src.text_processor import ArticleRanker

app = typer.Typer()
console = Console()


@app.command()
def init():
    """Initialize the database"""
    console.print(Panel("Initializing OSINT database...", style="blue"))
    db = DatabaseManager()
    console.print(Panel("Database initialized successfully!", style="green"))
    db.close()


@app.command()
def version():
    """Show version"""
    console.print("OSINT CLI v0.1.0")


@app.command()
def search(
    query: str,
    max_results: int = 10,
    news_only: bool = False,
    scrape_results: bool = False,
    extract_entities: bool = False,
):
    """
    Search the web using DuckDuckGo.

    Args:
        query: Search query string
        max_results: Maximum number of results
        news_only: Search for news articles only
        scrape_results: Scrape and display article content
        extract_entities: Extract named entities from scraped content
    """
    console.print(Panel(f"Searching for: {query}", style="blue"))

    search_engine = SearchEngine(max_results=max_results)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Searching...", total=None)

        if news_only:
            results = search_engine.search_news(query, max_results=max_results)
        else:
            results = search_engine.search(query, max_results=max_results)

        progress.update(task, completed=True)

    if not results:
        console.print("[red]No results found.[/red]")
        return

    # Display results
    table = Table(title="Search Results")
    table.add_column("#", style="cyan", width=4)
    table.add_column("Title", style="green")
    table.add_column("URL", style="blue")

    for i, result in enumerate(results, 1):
        table.add_row(
            str(i),
            result.title[:50] + "..." if len(result.title) > 50 else result.title,
            result.href[:60] + "..." if len(result.href) > 60 else result.href,
        )

    console.print(table)

    # Scrape if requested
    if scrape_results:
        console.print("\n[blue]Scraping articles...[/blue]")
        scraper = AdaptiveScraper()
        articles = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            for i, result in enumerate(results[:5], 1):  # Limit to first 5 for scraping
                task = progress.add_task(
                    f"Scraping article {i}/{min(5, len(results))}...", total=None
                )
                article = scraper.scrape(result.href)
                if article:
                    articles.append(article)
                    console.print(
                        f"[green]✓[/green] Scraped: {article.title[:50]}... ({article.word_count} words)"
                    )
                else:
                    console.print(
                        f"[red]✗[/red] Failed to scrape: {result.href[:50]}..."
                    )
                progress.update(task, completed=True)

        if articles and extract_entities:
            console.print("\n[blue]Extracting entities...[/blue]")
            ner = IndonesianNERExtractor()

            for article in articles:
                console.print(f"\n[bold]{article.title}[/bold]")
                entities = ner.extract(article.content[:2000])  # Limit content length

                if entities:
                    entity_table = Table()
                    entity_table.add_column("Entity", style="green")
                    entity_table.add_column("Type", style="cyan")
                    entity_table.add_column("Confidence", style="yellow")

                    for entity in entities[:10]:  # Show top 10
                        entity_table.add_row(
                            entity.text[:40],
                            entity.entity_type,
                            f"{entity.confidence:.2f}",
                        )
                    console.print(entity_table)
                else:
                    console.print("[dim]No entities found.[/dim]")


@app.command()
def scrape(url: str, extract_entities: bool = False):
    """
    Scrape a single URL.

    Args:
        url: URL to scrape
        extract_entities: Extract named entities from content
    """
    console.print(Panel(f"Scraping: {url}", style="blue"))

    scraper = AdaptiveScraper()
    article = scraper.scrape(url)

    if not article:
        console.print("[red]Failed to scrape the URL.[/red]")
        return

    console.print(f"\n[bold]Title:[/bold] {article.title}")
    console.print(f"[bold]Word Count:[/bold] {article.word_count}")
    if article.author:
        console.print(f"[bold]Author:[/bold] {article.author}")
    if article.publish_date:
        console.print(f"[bold]Date:[/bold] {article.publish_date}")

    console.print(f"\n[bold]Content:[/bold]\n{article.content[:1000]}...")

    if extract_entities:
        console.print("\n[blue]Extracting entities...[/blue]")
        ner = IndonesianNERExtractor()
        entities = ner.extract(article.content)

        if entities:
            entity_table = Table(title="Extracted Entities")
            entity_table.add_column("Entity", style="green")
            entity_table.add_column("Type", style="cyan")
            entity_table.add_column("Confidence", style="yellow")

            for entity in entities[:15]:
                entity_table.add_row(
                    entity.text[:40], entity.entity_type, f"{entity.confidence:.2f}"
                )
            console.print(entity_table)

            # Show summary
            summary = ner.get_entity_summary(entities)
            console.print("\n[bold]Entity Summary:[/bold]")
            for entity_type, names in summary.items():
                console.print(f"[cyan]{entity_type}:[/cyan] {', '.join(names[:10])}")
        else:
            console.print("[dim]No entities found.[/dim]")


@app.command()
def ner(text: str, show_summary: bool = True, store: bool = False):
    """
    Extract named entities from text.

    Args:
        text: Input text to analyze
        show_summary: Show entity type summary
        store: Store extracted entities in database
    """
    console.print(Panel("Extracting Named Entities", style="blue"))

    extractor = IndonesianNERExtractor()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task("Loading NER model...", total=None)
        entities = extractor.extract(text)

    if not entities:
        console.print("[yellow]No entities found in the text.[/yellow]")
        return

    # Display entities
    table = Table(title=f"Found {len(entities)} Entities")
    table.add_column("Entity", style="green")
    table.add_column("Type", style="cyan")
    table.add_column("Confidence", style="yellow")

    for entity in entities:
        table.add_row(entity.text[:50], entity.entity_type, f"{entity.confidence:.2f}")

    console.print(table)

    if show_summary:
        summary = extractor.get_entity_summary(entities)
        console.print("\n[bold]Summary by Type:[/bold]")

        summary_table = Table()
        summary_table.add_column("Type", style="cyan")
        summary_table.add_column("Count", style="yellow")
        summary_table.add_column("Examples", style="green")

        for entity_type, names in sorted(summary.items()):
            summary_table.add_row(entity_type, str(len(names)), ", ".join(names[:5]))

        console.print(summary_table)

    # Store entities if requested
    if store:
        console.print("\n[blue]Storing entities in database...[/blue]")
        db = DatabaseManager()

        # Create a document entry for this text
        doc_id = db.insert_document(
            filename="cli_input", file_path="memory", doc_type="text"
        )

        # Store each entity
        stored_count = 0
        for entity in entities:
            db.insert_entity(
                name=entity.text,
                entity_type=entity.entity_type,
                confidence=entity.confidence,
                source_doc_id=doc_id,
            )
            stored_count += 1

        console.print(f"[green]✓ Stored {stored_count} entities[/green]")
        db.close()


@app.command()
def entities(entity_type: Optional[str] = None, limit: int = 50):
    """
    List stored entities from the database.

    Args:
        entity_type: Filter by entity type (PERSON, ORGANIZATION, LOCATION, etc.)
        limit: Maximum number of entities to show
    """
    console.print(Panel("Stored Entities", style="blue"))

    db = DatabaseManager()

    entity_count = db.get_entity_count()
    doc_count = db.get_document_count()

    console.print(
        f"[dim]Total entities: {entity_count} | Total documents: {doc_count}[/dim]\n"
    )

    results = db.get_entities(entity_type=entity_type, limit=limit)

    if not results:
        console.print("[yellow]No entities found in the database.[/yellow]")
        db.close()
        return

    table = Table(title=f"Showing {len(results)} Entities")
    table.add_column("ID", style="dim", width=6)
    table.add_column("Name", style="green")
    table.add_column("Type", style="cyan")
    table.add_column("Confidence", style="yellow", width=10)
    table.add_column("Created", style="dim")

    for row in results:
        table.add_row(
            str(row[0]),
            row[1][:40],
            row[2],
            f"{row[3]:.2f}" if row[3] else "-",
            str(row[5])[:16] if row[5] else "-",
        )

    console.print(table)
    db.close()


@app.command()
def process(query: str, max_results: int = 5, store: bool = True):
    """
    Full pipeline: Search → Scrape → Extract → Store.

    Args:
        query: Search query
        max_results: Maximum number of articles to process
        store: Store extracted entities in database
    """
    console.print(Panel(f"Processing: {query}", style="blue bold"))

    # Step 1: Search
    console.print("\n[blue]Step 1: Searching...[/blue]")
    search_engine = SearchEngine(max_results=max_results)
    search_results = search_engine.search(query, max_results=max_results)

    if not search_results:
        console.print("[red]No search results found.[/red]")
        return

    console.print(f"[green]Found {len(search_results)} results[/green]")

    # Step 2: Scrape
    console.print("\n[blue]Step 2: Scraping articles...[/blue]")
    scraper = AdaptiveScraper()
    articles = []

    for result in search_results:
        article = scraper.scrape(result.href)
        if article:
            articles.append(article)
            console.print(
                f"  [green]✓[/green] {article.title[:50]}... ({article.word_count} words)"
            )
        else:
            console.print(f"  [red]✗[/red] Failed: {result.href[:50]}...")

    if not articles:
        console.print("[red]No articles could be scraped.[/red]")
        return

    # Step 3: Extract Entities
    console.print("\n[blue]Step 3: Extracting entities...[/blue]")
    ner = IndonesianNERExtractor()
    all_entities = []

    for article in articles:
        entities = ner.extract(article.content[:3000])  # Limit content
        all_entities.extend(entities)
        console.print(
            f"  Extracted {len(entities)} entities from: {article.title[:40]}..."
        )

    if not all_entities:
        console.print("[yellow]No entities found in the articles.[/yellow]")
        return

    # Deduplicate entities
    unique_entities = list(
        {(e.text.lower(), e.entity_type): e for e in all_entities}.values()
    )
    console.print(f"[green]Total unique entities: {len(unique_entities)}[/green]")

    # Show entity summary
    summary = ner.get_entity_summary(unique_entities)
    summary_table = Table(title="Entity Summary")
    summary_table.add_column("Type", style="cyan")
    summary_table.add_column("Count", style="yellow")
    summary_table.add_column("Examples", style="green")

    for entity_type, names in sorted(summary.items(), key=lambda x: -len(x[1]))[:10]:
        summary_table.add_row(entity_type, str(len(names)), ", ".join(names[:5]))

    console.print(summary_table)

    # Step 4: Store
    if store:
        console.print("\n[blue]Step 4: Storing in database...[/blue]")
        db = DatabaseManager()

        # Store entities
        stored = 0
        for entity in unique_entities:
            db.insert_entity(
                name=entity.text,
                entity_type=entity.entity_type,
                confidence=entity.confidence,
            )
            stored += 1

        console.print(f"[green]✓ Stored {stored} entities[/green]")
        db.close()

    console.print("\n[green bold]Processing complete![/green bold]")


if __name__ == "__main__":
    app()
