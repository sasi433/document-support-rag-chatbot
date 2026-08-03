const documentForm = document.querySelector("#document-form");
const fileInput = document.querySelector("#document-file");
const fileLabel = document.querySelector("#file-label");
const uploadButton = document.querySelector("#upload-button");
const uploadStatus = document.querySelector("#upload-status");
const refreshDocumentsButton = document.querySelector("#refresh-documents");
const documentsStatus = document.querySelector("#documents-status");
const documentsEmpty = document.querySelector("#documents-empty");
const documentsList = document.querySelector("#documents-list");

const chatForm = document.querySelector("#chat-form");
const questionInput = document.querySelector("#question");
const askButton = document.querySelector("#ask-button");
const chatStatus = document.querySelector("#chat-status");
const answerPanel = document.querySelector("#answer-panel");
const answerText = document.querySelector("#answer-text");
const sourcesPanel = document.querySelector("#sources-panel");
const sourcesList = document.querySelector("#sources-list");

function setStatus(element, message, type = "") {
  element.textContent = message;
  element.className = `form-status ${type}`.trim();
}

function setButtonBusy(button, isBusy, busyLabel, readyLabel) {
  button.disabled = isBusy;
  button.textContent = isBusy ? busyLabel : readyLabel;
}

async function getErrorMessage(response) {
  try {
    const data = await response.json();

    if (typeof data.detail === "string") {
      return data.detail;
    }
  } catch {
    // Use the generic message below when the server does not return JSON.
  }

  return `Request failed with status ${response.status}.`;
}

function renderSources(sources) {
  sourcesList.replaceChildren();

  if (!Array.isArray(sources) || sources.length === 0) {
    sourcesPanel.hidden = true;
    return;
  }

  for (const source of sources) {
    const item = document.createElement("li");
    item.className = "source-item";

    const metadata = document.createElement("div");
    metadata.className = "source-metadata";

    const filename = document.createElement("strong");
    filename.textContent = source.filename;

    const chunk = document.createElement("span");
    chunk.textContent = `Chunk ${source.chunk_index}`;

    const snippet = document.createElement("p");
    snippet.className = "source-snippet";
    snippet.textContent = source.snippet;

    metadata.append(filename, chunk);
    item.append(metadata, snippet);
    sourcesList.append(item);
  }

  sourcesPanel.hidden = false;
}

function renderDocuments(documents) {
  documentsList.replaceChildren();
  documentsEmpty.hidden = documents.length !== 0;

  for (const indexedDocument of documents) {
    const item = document.createElement("li");
    item.className = "document-item";

    const details = document.createElement("div");
    details.className = "document-details";

    const filename = document.createElement("strong");
    filename.textContent = indexedDocument.filename;

    const chunkCount = document.createElement("span");
    const chunkLabel = indexedDocument.chunk_count === 1 ? "chunk" : "chunks";
    chunkCount.textContent = `${indexedDocument.chunk_count} ${chunkLabel}`;

    const deleteButton = document.createElement("button");
    deleteButton.className = "delete-button";
    deleteButton.type = "button";
    deleteButton.textContent = "Delete";
    deleteButton.setAttribute("aria-label", `Delete ${indexedDocument.filename}`);
    deleteButton.addEventListener("click", () =>
      deleteDocument(indexedDocument, deleteButton),
    );

    details.append(filename, chunkCount);
    item.append(details, deleteButton);
    documentsList.append(item);
  }
}

async function loadDocuments() {
  setButtonBusy(refreshDocumentsButton, true, "Loading...", "Refresh");
  setStatus(documentsStatus, "Loading indexed documents...");

  try {
    const response = await fetch("/documents");

    if (!response.ok) {
      throw new Error(await getErrorMessage(response));
    }

    const data = await response.json();
    renderDocuments(Array.isArray(data.documents) ? data.documents : []);
    setStatus(documentsStatus, "");
    return true;
  } catch (error) {
    setStatus(documentsStatus, error.message, "error");
    return false;
  } finally {
    setButtonBusy(refreshDocumentsButton, false, "Loading...", "Refresh");
  }
}

async function deleteDocument(indexedDocument, button) {
  const confirmed = window.confirm(
    `Delete ${indexedDocument.filename}? This removes its uploaded file and indexed content.`,
  );
  if (!confirmed) {
    return;
  }

  setButtonBusy(button, true, "Deleting...", "Delete");
  setStatus(documentsStatus, `Deleting ${indexedDocument.filename}...`);

  try {
    const encodedFilename = encodeURIComponent(indexedDocument.filename);
    const response = await fetch(`/documents/${encodedFilename}`, {
      method: "DELETE",
    });

    if (!response.ok) {
      throw new Error(await getErrorMessage(response));
    }

    if (await loadDocuments()) {
      setStatus(
        documentsStatus,
        `${indexedDocument.filename} was deleted.`,
        "success",
      );
    }
  } catch (error) {
    setStatus(documentsStatus, error.message, "error");
  } finally {
    setButtonBusy(button, false, "Deleting...", "Delete");
  }
}

fileInput.addEventListener("change", () => {
  const selectedFile = fileInput.files[0];
  fileLabel.textContent = selectedFile ? selectedFile.name : "Choose a document";
  setStatus(uploadStatus, "");
});

documentForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  const selectedFile = fileInput.files[0];
  if (!selectedFile) {
    setStatus(uploadStatus, "Choose a document before uploading.", "error");
    return;
  }

  const formData = new FormData();
  formData.append("file", selectedFile);

  setButtonBusy(uploadButton, true, "Uploading...", "Upload and index");
  setStatus(uploadStatus, "Uploading and indexing your document...");

  try {
    const response = await fetch("/documents/upload", {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      throw new Error(await getErrorMessage(response));
    }

    const data = await response.json();
    setStatus(uploadStatus, `${data.filename} is ready for questions.`, "success");
    documentForm.reset();
    fileLabel.textContent = "Choose a document";
    await loadDocuments();
    questionInput.focus();
  } catch (error) {
    setStatus(uploadStatus, error.message, "error");
  } finally {
    setButtonBusy(uploadButton, false, "Uploading...", "Upload and index");
  }
});

refreshDocumentsButton.addEventListener("click", loadDocuments);
loadDocuments();

chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  const question = questionInput.value.trim();
  if (!question) {
    setStatus(chatStatus, "Enter a question first.", "error");
    return;
  }

  setButtonBusy(askButton, true, "Thinking...", "Ask documents");
  setStatus(chatStatus, "Searching indexed documents...");
  answerPanel.hidden = true;
  renderSources([]);

  try {
    const response = await fetch("/chat/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });

    if (!response.ok) {
      throw new Error(await getErrorMessage(response));
    }

    const data = await response.json();
    answerText.textContent = data.answer;
    renderSources(data.sources);
    answerPanel.hidden = false;
    setStatus(chatStatus, "");
  } catch (error) {
    setStatus(chatStatus, error.message, "error");
  } finally {
    setButtonBusy(askButton, false, "Thinking...", "Ask documents");
  }
});
