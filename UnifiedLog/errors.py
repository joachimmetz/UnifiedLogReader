# -*- coding: utf-8 -*-
"""This file contains the error classes."""

from __future__ import unicode_literals


class Error(Exception):
  """Base error class."""


class ParseError(Error):
  """Raised when a parse error occurred."""
