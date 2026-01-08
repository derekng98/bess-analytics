import typer

app = typer.Typer(add_completion=False, help="BESS analytics CLI")

@app.command("hello")
def hello() -> None:
    """Sanity check command."""
    typer.echo("bess-analytics is installed and the CLI works ✅")

@app.command("version")
def version() -> None:
    """Print version."""
    typer.echo("0.1.0")

def main() -> None:
    app()

if __name__ == "__main__":
    main()
