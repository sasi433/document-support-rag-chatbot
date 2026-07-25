# Document Support RAG Chatbot

A portfolio project for building a document-support chatbot. The current API accepts support documents, extracts and chunks their text, creates embeddings, and indexes those chunks in a persistent local vector store. Retrieval, answer generation, and a user interface will be added in later stages.

## Project structure

```text
app/
|-- api/          # API route modules
|-- core/         # Application configuration
|-- schemas/      # Future request and response models
|-- services/     # Future business logic
`-- static/       # Future static UI files
sample_docs/      # Future example documents
tests/            # Future automated tests
```

## Local setup (Windows PowerShell)

From the project root, create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install the dependencies:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Optionally create a local environment file from the example:

```powershell
Copy-Item .env.example .env
```

The app uses the default settings when `.env` is absent. If you create `.env`, keep it local and do not commit it because environment files may contain secrets in the future.

Available settings:

| Variable | Default | Purpose |
| --- | --- | --- |
| `APP_NAME` | `document-support-rag-chatbot` | FastAPI application name |
| `APP_ENV` | `local` | Current application environment |
| `LOG_LEVEL` | `INFO` | Minimum console logging level |
| `UPLOAD_DIR` | `data/uploads` | Local document upload directory |
| `OPENAI_API_KEY` | Not set | OpenAI API key used to create embeddings |
| `OPENAI_EMBEDDING_MODEL` | `text-embedding-3-small` | OpenAI model used to create embeddings |
| `CHROMA_PERSIST_DIR` | `data/chroma` | Local directory for persistent vector data |
| `CHROMA_COLLECTION_NAME` | `support_documents` | Chroma collection used for document chunks |

Chroma creates its database files inside `data/chroma` by default. These generated files stay local and are not committed to Git.

Uploading a supported `.txt`, `.md`, or `.pdf` document requires `OPENAI_API_KEY`. The upload endpoint returns success only after the document has been chunked, embedded, and indexed in Chroma.

## Run the app

```powershell
python -m uvicorn app.main:app --reload
```

Open the health check at <http://127.0.0.1:8000/health>. It should return:

```json
{"status": "ok"}
```

You can also test it from PowerShell:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```
