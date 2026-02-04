import typer

from internal_api.batch.app import app as batch_app

app = typer.Typer(help="internal-api micro batch commands")
app.add_typer(batch_app, name="batch")


@app.command()
def ping() -> None:
    """Health check for CLI."""
    typer.echo("ok")
