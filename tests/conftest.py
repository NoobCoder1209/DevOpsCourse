from __future__ import annotations

import pytest

from app.main import create_app


@pytest.fixture()
def client():
    app = create_app()
    app.testing = True
    with app.test_client() as c:
        yield c
