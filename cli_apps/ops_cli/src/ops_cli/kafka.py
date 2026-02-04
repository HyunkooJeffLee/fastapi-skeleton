import typer

app = typer.Typer(help="Kafka consumer commands")


@app.command("sample")
def sample() -> None:
    """Placeholder kafka consumer command."""
    typer.echo("kafka sample")
