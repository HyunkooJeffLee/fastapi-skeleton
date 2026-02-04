import typer

app = typer.Typer(help="Micro batch commands")


@app.command("sample")
def sample() -> None:
    """Placeholder micro batch command."""
    typer.echo("batch sample")
