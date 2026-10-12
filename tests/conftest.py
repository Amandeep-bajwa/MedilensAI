import sys
import os
import pytest

# Ensure backend directory is in python path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.core.rate_limit import limiter

@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """
    Resets in-memory rate limit storage before each test to prevent
    rate limit threshold leakage across test scenarios while preserving
    rate limit enforcement within isolated test runs.
    """
    limiter.reset()
    yield
    limiter.reset()
