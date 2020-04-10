import click
from mock import MagicMock, patch

from geocube.cli.geocube import check_version, cli_show_version


@patch("geocube.cli.geocube.__version__", "1.1")
def test_check_version(capsys):
    context = MagicMock(click.Context)
    context.resilient_parsing = False
    check_version(context, "str", "str")

    stdout = capsys.readouterr()[0]
    assert "geocube v1.1" in stdout


def test_cli_show_versions(capsys):
    context = MagicMock(click.Context)
    context.resilient_parsing = False
    cli_show_version(context, "str", "str")

    stdout = capsys.readouterr()[0]
    assert "geocube v" in stdout
    assert "GDAL deps" in stdout
    assert "Python deps" in stdout
    assert "System" in stdout
