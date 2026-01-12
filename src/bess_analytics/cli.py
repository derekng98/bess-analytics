import typer

from .config import load_config
from .pipeline import run_daily

app = typer.Typer(add_completion=False, help="BESS analytics CLI")


@app.command("hello")
def hello() -> None:
    """Sanity check command."""
    typer.echo("bess-analytics is installed and the CLI works ✅")


@app.command("version")
def version() -> None:
    """Print version."""
    typer.echo("0.1.0")


@app.command("run")
def run(config: str = typer.Option(..., "--config", "-c", help="Path to config.yaml")) -> None:
    """Generate daily energy table (per enclosure, per day)."""
    cfg = load_config(config)
    out_path = run_daily(cfg)
    typer.echo(f"Saved daily table: {out_path}")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
