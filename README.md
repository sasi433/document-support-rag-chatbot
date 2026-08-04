# Document Support RAG Chatbot

A portfolio-scale retrieval-augmented generation (RAG) application for asking questions about support documents. The project accepts text, Markdown, and PDF files, indexes their content in a persistent vector store, and generates answers grounded in retrieved document chunks.

The application includes a FastAPI backend, a lightweight browser interface, structured source references, automated tests, linting, and Docker support.

## Features

- Upload `.txt`, `.md`, and `.pdf` documents.
- View indexed documents and their chunk counts.
- Remove uploaded documents and their indexed content.
- Extract and split document text into overlapping chunks.
- Generate embeddings with OpenAI.
- Store and search embeddings with persistent ChromaDB.
- Generate answers using only retrieved document context.
- Ask contextual follow-up questions using recent browser-session history.
- Return filename, chunk index, and a short snippet for each source.
- Use an explicit fallback when the documents do not contain an answer.
- Run through the browser, REST API, Docker, or Docker Compose.

## How it works

```text
Document -> Extract text -> Create chunks -> Generate embeddings -> ChromaDB
Question + recent history -> Retrieve chunks -> Generate answer -> Show sources
```

For each question, the application retrieves up to three relevant chunks. Recent conversation history can clarify follow-up intent, but the answer model is instructed to use document context as its only factual evidence. If the context is insufficient, the application returns:

```text
I don't know based on the provided documents.
```

Fallback responses contain an empty `sources` list.

## Technology

- Python 3.11
- FastAPI and Pydantic Settings
- OpenAI embeddings and response generation
- ChromaDB persistent vector storage
- Vanilla HTML, CSS, and JavaScript
- Pytest and Ruff
- Docker and Docker Compose

## Project structure

```text
app/
|-- api/          # Health, document upload, and chat routes
|-- core/         # Environment settings and logging
|-- schemas/      # API request and response models
|-- services/     # Loading, chunking, embeddings, retrieval, and Q&A
|-- static/       # Browser interface
`-- utils/        # Upload file handling
data/
|-- uploads/      # Locally uploaded documents
`-- chroma/       # Generated ChromaDB data
docs/             # Demo questions and validation notes
sample_docs/      # Fictional documents for demonstrations
tests/            # Automated test suite and fixtures
```

## Local setup (Windows PowerShell)

From the project root, create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install the pinned dependencies:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Create a local environment file:

```powershell
Copy-Item .env.example .env
```

Set `OPENAI_API_KEY` in `.env` before uploading documents or asking questions. The interface and health endpoint can run without a key, but ingestion and chat require one.

Never commit `.env`. It is ignored because it may contain secrets.

## Run locally

```powershell
python -m uvicorn app.main:app --reload
```

Available URLs:

- Browser interface: <http://127.0.0.1:8000/>
- Health check: <http://127.0.0.1:8000/health>
- Interactive API documentation: <http://127.0.0.1:8000/docs>

The health endpoint should return:

```json
{"status": "ok"}
```

## Browser demo

1. Start the application and open <http://127.0.0.1:8000/>.
2. Upload one of the files from `sample_docs/`, such as `company_faq.md`.
3. Confirm it appears under **Indexed documents** with its chunk count.
4. Ask: `What is the refund policy?`
5. Confirm the answer includes source cards with the filename, chunk index, and context snippet.
6. Ask the follow-up: `What about renewal charges?`
7. Confirm the answer understands the refund-policy context and remains grounded in the document.
8. Ask: `What is the CEO's personal phone number?`
9. Confirm the exact fallback message appears without sources.
10. Clear the conversation and confirm the transcript is emptied.
11. Delete the uploaded document and confirm it disappears from the indexed-document list.

The sample documents describe a fictional organization and contain no real credentials or personal data. More supported and fallback examples are available in [docs/demo_questions.md](docs/demo_questions.md).

## API usage

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Confirm the application is running |
| `GET` | `/documents` | List indexed documents and chunk counts |
| `POST` | `/documents/upload` | Save, chunk, embed, and index a document |
| `DELETE` | `/documents/{filename}` | Remove a document and its indexed chunks |
| `POST` | `/chat/ask` | Ask a question using indexed documents |

### Upload a document

```powershell
curl.exe -X POST `
  -F "file=@sample_docs/company_faq.md" `
  http://127.0.0.1:8000/documents/upload
```

Successful response:

```json
{
  "filename": "company_faq.md",
  "status": "uploaded"
}
```

Uploading another document with the same filename is rejected instead of overwriting the existing file.

### List indexed documents

```powershell
Invoke-RestMethod http://127.0.0.1:8000/documents
```

Each document includes its filename and the number of chunks stored in ChromaDB.

### Delete a document

```powershell
Invoke-RestMethod `
  -Method Delete `
  -Uri http://127.0.0.1:8000/documents/company_faq.md
```

Deletion removes both the uploaded file and all of its indexed chunks.

### Ask a question

```powershell
$body = @{ question = "What is the refund policy?" } | ConvertTo-Json
Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/chat/ask `
  -ContentType "application/json" `
  -Body $body
```

Response shape:

```json
{
  "answer": "The first subscription payment can be refunded when requested within 14 calendar days.",
  "sources": [
    {
      "filename": "company_faq.md",
      "chunk_index": 1,
      "snippet": "A customer may request a refund for their first subscription payment within 14 calendar days..."
    }
  ]
}
```

Follow-up requests may include up to six recent messages as complete, alternating user/assistant pairs:

```json
{
  "question": "What about renewal charges?",
  "history": [
    {
      "role": "user",
      "content": "What is the refund policy?"
    },
    {
      "role": "assistant",
      "content": "The first subscription payment may be refunded within 14 days."
    }
  ]
}
```

Browser conversation history stays in memory for the current page session only. Clearing the conversation or refreshing the page removes it.

## Configuration

Settings are loaded from environment variables and from `.env` when it is present.

| Variable | Default | Purpose |
| --- | --- | --- |
| `APP_NAME` | `document-support-rag-chatbot` | FastAPI application title |
| `APP_ENV` | `local` | Current application environment |
| `LOG_LEVEL` | `INFO` | Minimum console logging level |
| `UPLOAD_DIR` | `data/uploads` | Uploaded document directory |
| `OPENAI_API_KEY` | Not set | API key for embeddings and answers |
| `OPENAI_EMBEDDING_MODEL` | `text-embedding-3-small` | Embedding model |
| `OPENAI_CHAT_MODEL` | `gpt-5.6-terra` | Answer-generation model |
| `CHROMA_PERSIST_DIR` | `data/chroma` | Persistent vector database directory |
| `CHROMA_COLLECTION_NAME` | `support_documents` | ChromaDB collection name |

Uploaded documents and generated ChromaDB files remain local and are excluded from Git.

## Docker

Make sure Docker Desktop is running.

### Docker image

Build and run the application directly:

```powershell
docker build -t document-support-rag-chatbot .
docker run --rm -p 8000:8000 --env-file .env document-support-rag-chatbot
```

Data created by this command is removed with the container.

### Docker Compose

Docker Compose is recommended when you want uploaded documents and ChromaDB data to persist in the local `data/` directory:

```powershell
docker compose up --build
```

Stop and remove the container and network:

```powershell
docker compose down
```

The application can start without `.env` for interface and health checks. Upload and chat operations still require `OPENAI_API_KEY`.

## Tests and linting

Run the automated test suite:

```powershell
python -m pytest -q
```

Run Ruff:

```powershell
python -m ruff check .
```

Both commands should pass before committing changes.

## Project scope

This repository is a local, single-user portfolio demonstration. It intentionally does not include authentication, multi-user document isolation, persistent conversation storage, background processing, or production deployment infrastructure.
