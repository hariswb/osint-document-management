import typer
from rich.console import Console
from rich.panel import Panel
from src.database import DatabaseManager

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


if __name__ == "__main__":
    app()
