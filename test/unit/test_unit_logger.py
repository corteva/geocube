from mock import patch

from geocube.logger import log_to_console, log_to_file, get_logger


def test_log_to_console(capsys):
    log_to_console(False)  # clear any other loggers
    log_to_console(level="INFO")
    logm = get_logger()
    logm.info("here")
    captured = capsys.readouterr()
    assert "INFO-geocube: here" in captured.err


def test_log_to_console__warning(capsys):
    log_to_console(False)  # clear any other loggers
    log_to_console()
    logm = get_logger()
    logm.info("here")
    logm.warning("there")
    captured = capsys.readouterr()
    assert "INFO-geocube: here" not in captured.err
    assert "WARNING-geocube: there" in captured.err


@patch("geocube.logger.appdirs.user_log_dir")
def test_log_to_file(mock_user_log_dir, tmpdir):
    mock_user_log_dir.return_value = str(tmpdir)
    log_to_file(False)  # clear any other loggers
    log_to_file(level="INFO")
    logm = get_logger()
    logm.info("here")
    with open(tmpdir.join("geocube.log")) as logf:
        captured = logf.read()
    assert "INFO-geocube: here" in captured


@patch("geocube.logger.appdirs.user_log_dir")
def test_log_to_file__warning(mock_user_log_dir, tmpdir):
    mock_user_log_dir.return_value = str(tmpdir)
    log_to_file(False)  # clear any other loggers
    log_to_file()
    logm = get_logger()
    logm.info("here")
    logm.warning("there")
    with open(tmpdir.join("geocube.log")) as logf:
        captured = logf.read()
    assert "INFO-geocube: here" not in captured
    assert "WARNING-geocube: there" in captured
