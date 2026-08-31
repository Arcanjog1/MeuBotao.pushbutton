# -*- coding: utf-8 -*-
"""Casamento e comparacao entre gabarito e resultado."""

from . import match  # noqa: F401
from . import compare_projects  # noqa: F401

from .compare_projects import compare_projects as compare  # noqa: F401
from .compare_projects import classify_differences  # noqa: F401
