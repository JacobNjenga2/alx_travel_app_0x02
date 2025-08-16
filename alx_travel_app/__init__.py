#!/usr/bin/env python3
"""
ALX Travel App initialization.

This module ensures that Celery is loaded when Django starts.
"""

import pymysql # type: ignore

pymysql.install_as_MySQLdb()

# Import Celery app
from .celery import app as celery_app

__all__ = ('celery_app',)
