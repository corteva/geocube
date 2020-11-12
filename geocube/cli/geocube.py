# -- coding: utf-8 --
"""
Main CLI endpoint for GeoCube
"""
import click
from click import group

import geocube.cli.commands as cmd_modules
from geocube import __version__, show_versions

CONTEXT_SETTINGS = {
    "help_option_names": ["-h", "--help"],
    "token_normalize_func": lambda x: x.replace("-", "_"),
}


def check_version(ctx, _, value):
    """
    Print current version, and check for latest version.

    Called via 'geocube --version'

    :param ctx: Application context object (click.Context)
    :param value: Passed in by Click
    :return None
    """
    if not value or ctx.resilient_parsing:
        return

    click.echo(f"geocube v{__version__}")

    ctx.exit()


def cli_show_version(ctx, _, value):
    """
    Print debugging version information.

    :param ctx: Application context object (click.Context)
    :param value: Passed in by Click
    :return None
    """
    if not value or ctx.resilient_parsing:
        return

    show_versions()

    ctx.exit()


@group(context_settings=CONTEXT_SETTINGS)
@click.option(
    "-v",
    "--version",
    is_flag=True,
    is_eager=True,
    expose_value=False,
    callback=check_version,
    help="Show the current version",
)
@click.option(
    "--show-versions",
    is_flag=True,
    is_eager=True,
    expose_value=False,
    callback=cli_show_version,
    help="Show debugging version information",
)
def geocube():
    """ Top-level command and entry point into the GeoCube CLI """


def _add_subcommands():
    """
    Individual commands (and sub-commands) are encapsulated in separate files
    under /commands. Collect these command groups, and add them underneath the
    top-level command (geocube).
    """
    geocube.add_command(cmd_modules.make_geocube.make_geocube)


_add_subcommands()
