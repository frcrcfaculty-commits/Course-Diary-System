"""Vercel entry point: expose the Flask app that lives in src/app.py."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from app import app  # noqa: E402,F401
