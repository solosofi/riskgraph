import typer
from rich.console import Console
from rich.table import Table
from riskgraph.scorer import score_package

app = typer.Typer(help="RiskGraph - credit score for open-source packages")
console = Console()

@app.command()
def scan(package: str, ecosystem: str = "npm"):
    console.print(f"[bold blue]Scanning {package} ({ecosystem})...[/bold blue]")
    result = score_package(package, ecosystem)
    tbl = Table(title=f"Risk Report for {package}")
    tbl.add_column("Metric", style="cyan"); tbl.add_column("Value", style="magenta")
    tbl.add_row("Score", str(round(result.score, 1)))
    tbl.add_row("Level", result.level)
    for s in result.signals:
        tbl.add_row(f"  {s['name']}", s['detail'][:60])
    console.print(tbl)

def main():
    app()
if __name__ == "__main__":
    main()
