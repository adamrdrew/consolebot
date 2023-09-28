import click
from consolebot import query, repodata

class DefaultGroup(click.Group):

    def __init__(self, *args, **kwargs):
        # Set our default command name
        self.default_cmd_name = kwargs.pop("default_cmd_name")
        super(DefaultGroup, self).__init__(*args, **kwargs)

    def resolve_command(self, ctx, args):
        # If first arg matches a known command, use normal resolution
        if args and args[0] in self.list_commands(ctx):
            return super(DefaultGroup, self).resolve_command(ctx, args)
            
        # Otherwise, use the default command and the entire arg list
        default_cmd = self.get_command(ctx, self.default_cmd_name)
        return self.default_cmd_name, default_cmd, args

        
        # Otherwise, use the default command and the entire arg list
        default_cmd = self.get_command(ctx, self.default_cmd_name)
        return default_cmd, args

@click.group(cls=DefaultGroup, default_cmd_name='ask')
def cli():
    pass

@click.command(name="ask", context_settings={"ignore_unknown_options": True})
@click.argument('user_query', nargs=-1, required=False)
def ask_command(user_query):
    if user_query:
        user_query = ' '.join(user_query)
        query.run(user_query)
    else:
        click.echo("Please provide a query.")

@click.command()
def refresh():
    repodata.get()


cli.add_command(ask_command)
cli.add_command(refresh)

if __name__ == "__main__":
    cli()
