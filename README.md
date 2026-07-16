# Document Support RAG Chatbot

A portfolio project for building a document-support chatbot. Day 1 provides a minimal FastAPI foundation; document ingestion, retrieval, and a user interface will be added in later stages.

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
