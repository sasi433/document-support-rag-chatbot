import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_chat_interface_is_served_at_root() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert 'id="document-form"' in response.text
    assert 'id="chat-form"' in response.text
    assert 'id="sources-panel"' in response.text
    assert 'id="sources-list"' in response.text


@pytest.mark.parametrize(
    ("path", "content_type"),
    [
        ("/static/app.js", "application/javascript"),
        ("/static/style.css", "text/css"),
    ],
)
def test_static_assets_are_served(path: str, content_type: str) -> None:
    response = client.get(path)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith(content_type)
