# -*- coding: utf-8 -*-
"""
"""
import os
from unittest.mock import MagicMock
from unittest.mock import patch

import flask
import pytest

from trendlines import app_factory


def test_create_app(tmp_path, monkeypatch, caplog):
    # We need to touch the file or else we'll hit the FileNotFoundError
    path = tmp_path / "foo.cfg"
    path.touch()
    monkeypatch.setenv(app_factory.CFG_VAR, str(path))

    rv = app_factory.create_app()
    assert isinstance(rv, flask.app.Flask)
    assert "Loaded config file" in caplog.text
    assert str(path) in caplog.text


def test_create_app_missing_user_config_file(tmp_path, monkeypatch, caplog):
    monkeypatch.setenv(app_factory.CFG_VAR, str(tmp_path / 'foo.cfg'))
    rv = app_factory.create_app()
    assert isinstance(rv, flask.app.Flask)
    assert "Failed to load config file" in caplog.text
    assert "was not found." in caplog.text


# XXX: Bad test: it's testing the log message from flask
# instead something I made
def test_create_app_missing_user_config_envvar(tmp_path, monkeypatch, caplog):
    monkeypatch.delenv(app_factory.CFG_VAR, raising=False)
    rv = app_factory.create_app()
    assert isinstance(rv, flask.app.Flask)
    assert "The environment variable" in caplog.text
    assert "is not set and as such configuration" in caplog.text


@patch("flask.Config.from_envvar",
       MagicMock(side_effect=Exception("foobar"))
)
def test_create_app_user_config_general_exception(caplog):
    rv = app_factory.create_app()
    assert isinstance(rv, flask.app.Flask)
    assert "An unknown error occured while reading from the" in caplog.text
    assert "foobar" in caplog.text
