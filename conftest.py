"""Root conftest — adds the project root to sys.path so cogs can be imported."""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

# Exclude the integration smoke test from automatic collection —
# it requires a live AMP instance and populated .env to run.
collect_ignore = ["tests/smoke_test.py"]
