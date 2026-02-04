import typer

from ops_cli.batch import app as batch_app
from ops_cli.kafka import app as kafka_app

app = typer.Typer(help="CLI apps for batch/consumer workloads")
app.add_typer(batch_app, name="batch")
app.add_typer(kafka_app, name="kafka")


@app.command()
def ping() -> None:
    """Health check for CLI."""
    typer.echo("ok")
