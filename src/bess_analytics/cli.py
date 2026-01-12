import typer
from pathlib import Path
from .config import load_config
from .pipeline import run_daily
from importlib.metadata import PackageNotFoundError, version as pkg_version

app = typer.Typer(add_completion=False, help="BESS analytics CLI")


@app.command("hello")
def hello() -> None:
    """Sanity check command."""
    typer.echo("bess-analytics is installed and the CLI works ✅")


@app.command("version")
def version() -> None:
    """Print installed package version."""
    try:
        typer.echo(pkg_version("bess-analytics"))
    except PackageNotFoundError:
        typer.echo("unknown")


@app.command("run")
def run(config: str = typer.Option(..., "--config", "-c", help="Path to config.yaml")) -> None:
    """Generate daily energy + outliers + heatmap outputs."""
    cfg = load_config(config)
    daily_path = run_daily(cfg)

    out_dir = Path(cfg.output_dir)
    typer.echo(f"Saved daily table: {daily_path}")
    outliers_path = out_dir / cfg.outliers_file
    typer.echo(f"Saved outliers table: {outliers_path}")
    heatmap_path = out_dir / cfg.heatmap_file
    typer.echo(f"Saved discharged heatmap: {heatmap_path}")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
