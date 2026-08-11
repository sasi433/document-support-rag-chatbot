import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_chat_interface_is_served_at_root() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert 'id="document-form"' in response.text
    assert 'id="upload-help"' in response.text
    assert 'id="documents-list"' in response.text
    assert 'id="documents-empty"' in response.text
    assert 'id="refresh-documents"' in response.text
    assert 'id="chat-form"' in response.text
    assert 'id="document-scope"' in response.text
    assert 'id="conversation-list"' in response.text
    assert 'id="conversation-empty"' in response.text
    assert 'id="clear-conversation"' in response.text


@pytest.mark.parametrize(
    ("path", "content_types"),
    [
        (
            "/static/app.js",
            ("application/javascript", "text/javascript"),
        ),
        ("/static/style.css", ("text/css",)),
    ],
)
def test_static_assets_are_served(
    path: str,
    content_types: tuple[str, ...],
) -> None:
    response = client.get(path)

    assert response.status_code == 200
    media_type = response.headers["content-type"].split(";", maxsplit=1)[0]
    assert media_type in content_types


def test_browser_interface_supports_document_management() -> None:
    response = client.get("/static/app.js")

    assert response.status_code == 200
    assert 'fetch("/documents")' in response.text
    assert 'method: "DELETE"' in response.text
    assert "encodeURIComponent(indexedDocument.filename)" in response.text
    assert "window.confirm" in response.text
    assert "await loadDocuments()" in response.text
    assert '"download-button"' in response.text


def test_browser_interface_links_documents_and_sources_to_downloads() -> None:
    response = client.get("/static/app.js")

    assert response.status_code == 200
    assert "function createDocumentDownloadLink" in response.text
    assert "encodeURIComponent(filename)" in response.text
    assert "source.filename" in response.text
    assert 'link.setAttribute("download", "")' in response.text


def test_browser_interface_renders_document_file_metadata() -> None:
    response = client.get("/static/app.js")

    assert response.status_code == 200
    assert "function formatFileSize" in response.text
    assert "function formatModifiedAt" in response.text
    assert "indexedDocument.size_bytes" in response.text
    assert "indexedDocument.modified_at" in response.text
    assert "if (indexedDocument.download_available)" in response.text
    assert "Original file unavailable" in response.text


def test_browser_interface_uses_server_upload_constraints() -> None:
    response = client.get("/static/app.js")

    assert response.status_code == 200
    assert 'fetch("/documents/capabilities")' in response.text
    assert "data.supported_extensions.join" in response.text
    assert (
        "selectedFile.size > uploadCapabilities.max_upload_size_bytes"
        in response.text
    )
    assert "validateSelectedFile(selectedFile)" in response.text


def test_browser_interface_supports_document_scoped_chat() -> None:
    response = client.get("/static/app.js")

    assert response.status_code == 200
    assert "renderDocumentScope(documents)" in response.text
    assert "documentScope.value ? [documentScope.value] : []" in response.text
    assert "JSON.stringify({ question, history, documents })" in response.text


def test_browser_interface_supports_conversation_history() -> None:
    response = client.get("/static/app.js")

    assert response.status_code == 200
    assert "const MAX_CONVERSATION_MESSAGES = 6" in response.text
    assert "conversationHistory.slice(-MAX_CONVERSATION_MESSAGES)" in response.text
    assert "JSON.stringify({ question, history, documents })" in response.text
    assert 'appendConversationMessage("user", question)' in response.text
    assert 'appendConversationMessage("assistant", data.answer' in response.text
    assert "conversationHistory.length = 0" in response.text
