import click
from consolebot import run_query, get_data

@click.command()
@click.argument('query', nargs=-1)
def query(query):
    query = ' '.join(query)
    run_query(query)

@click.command()
def get():
    get_data()