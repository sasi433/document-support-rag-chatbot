const documentForm = document.querySelector("#document-form");
const fileInput = document.querySelector("#document-file");
const fileLabel = document.querySelector("#file-label");
const uploadHelp = document.querySelector("#upload-help");
const uploadButton = document.querySelector("#upload-button");
const uploadStatus = document.querySelector("#upload-status");
const refreshDocumentsButton = document.querySelector("#refresh-documents");
const documentsStatus = document.querySelector("#documents-status");
const documentsEmpty = document.querySelector("#documents-empty");
const documentsList = document.querySelector("#documents-list");

const chatForm = document.querySelector("#chat-form");
const documentScope = document.querySelector("#document-scope");
const questionInput = document.querySelector("#question");
const askButton = document.querySelector("#ask-button");
const chatStatus = document.querySelector("#chat-status");
const clearConversationButton = document.querySelector("#clear-conversation");
const conversationEmpty = document.querySelector("#conversation-empty");
const conversationList = document.querySelector("#conversation-list");

const MAX_CONVERSATION_MESSAGES = 6;
const conversationHistory = [];
let uploadCapabilities = null;

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

function createDocumentDownloadLink(filename, label, className) {
  const link = document.createElement("a");
  link.className = className;
  link.href = `/documents/${encodeURIComponent(filename)}/download`;
  link.textContent = label;
  link.setAttribute("download", "");
  link.setAttribute("aria-label", `Download ${filename}`);
  return link;
}

function formatFileSize(sizeBytes) {
  const megabyte = 1024 * 1024;
  const sizeInMegabytes = sizeBytes / megabyte;
  const displayedSize = Number.isInteger(sizeInMegabytes)
    ? sizeInMegabytes
    : sizeInMegabytes.toFixed(1);
  return `${displayedSize} MB`;
}

function validateSelectedFile(selectedFile) {
  if (!uploadCapabilities) {
    return "";
  }

  const normalizedFilename = selectedFile.name.toLowerCase();
  const supported = uploadCapabilities.supported_extensions.some((extension) =>
    normalizedFilename.endsWith(extension),
  );

  if (!supported) {
    const extensions = uploadCapabilities.supported_extensions
      .join(", ")
      .toUpperCase();
    return `Choose a supported document (${extensions}).`;
  }

  if (selectedFile.size > uploadCapabilities.max_upload_size_bytes) {
    const maximumSize = formatFileSize(
      uploadCapabilities.max_upload_size_bytes,
    );
    return `${selectedFile.name} is too large. Maximum upload size is ${maximumSize}.`;
  }

  return "";
}

async function loadUploadCapabilities() {
  try {
    const response = await fetch("/documents/capabilities");
    if (!response.ok) {
      throw new Error(await getErrorMessage(response));
    }

    const data = await response.json();
    if (
      !Array.isArray(data.supported_extensions) ||
      data.supported_extensions.length === 0 ||
      !Number.isInteger(data.max_upload_size_bytes) ||
      data.max_upload_size_bytes <= 0
    ) {
      throw new Error("The server returned invalid upload limits.");
    }

    uploadCapabilities = data;
    fileInput.accept = data.supported_extensions.join(",");
    uploadHelp.textContent = `Maximum size: ${formatFileSize(
      data.max_upload_size_bytes,
    )}`;

    const selectedFile = fileInput.files[0];
    if (selectedFile) {
      const validationMessage = validateSelectedFile(selectedFile);
      setStatus(
        uploadStatus,
        validationMessage,
        validationMessage ? "error" : "",
      );
    }
  } catch {
    uploadHelp.textContent = "TXT, Markdown, or PDF; server upload limit applies";
  }
}

function createSourcesPanel(sources) {
  const panel = document.createElement("section");
  panel.className = "sources-panel";
  panel.setAttribute("aria-label", "Sources for this answer");

  const label = document.createElement("p");
  label.className = "answer-label";
  label.textContent = "Sources";

  const list = document.createElement("ul");
  list.className = "sources-list";

  for (const source of sources) {
    const item = document.createElement("li");
    item.className = "source-item";

    const metadata = document.createElement("div");
    metadata.className = "source-metadata";

    const filename = createDocumentDownloadLink(
      source.filename,
      source.filename,
      "source-link",
    );

    const chunk = document.createElement("span");
    chunk.textContent = `Chunk ${source.chunk_index}`;

    const snippet = document.createElement("p");
    snippet.className = "source-snippet";
    snippet.textContent = source.snippet;

    metadata.append(filename, chunk);
    item.append(metadata, snippet);
    list.append(item);
  }

  panel.append(label, list);
  return panel;
}

function appendConversationMessage(role, content, sources = []) {
  const item = document.createElement("li");
  item.className = `conversation-message ${role}-message`;

  const roleLabel = document.createElement("p");
  roleLabel.className = "message-role";
  roleLabel.textContent = role === "user" ? "You" : "Assistant";

  const messageContent = document.createElement("p");
  messageContent.className = "message-content";
  messageContent.textContent = content;

  item.append(roleLabel, messageContent);
  if (role === "assistant" && Array.isArray(sources) && sources.length > 0) {
    item.append(createSourcesPanel(sources));
  }

  conversationList.append(item);
  conversationEmpty.hidden = true;
  clearConversationButton.disabled = false;
  item.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function rememberConversation(question, answer) {
  conversationHistory.push(
    { role: "user", content: question },
    { role: "assistant", content: answer },
  );

  if (conversationHistory.length > MAX_CONVERSATION_MESSAGES) {
    conversationHistory.splice(
      0,
      conversationHistory.length - MAX_CONVERSATION_MESSAGES,
    );
  }
}

function clearConversation() {
  conversationHistory.length = 0;
  conversationList.replaceChildren();
  conversationEmpty.hidden = false;
  clearConversationButton.disabled = true;
  setStatus(chatStatus, "");
  questionInput.focus();
}

function renderDocuments(documents) {
  renderDocumentScope(documents);
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

    const actions = document.createElement("div");
    actions.className = "document-actions";

    const downloadLink = createDocumentDownloadLink(
      indexedDocument.filename,
      "Download",
      "download-button",
    );

    const deleteButton = document.createElement("button");
    deleteButton.className = "delete-button";
    deleteButton.type = "button";
    deleteButton.textContent = "Delete";
    deleteButton.setAttribute("aria-label", `Delete ${indexedDocument.filename}`);
    deleteButton.addEventListener("click", () =>
      deleteDocument(indexedDocument, deleteButton),
    );

    actions.append(downloadLink, deleteButton);
    details.append(filename, chunkCount);
    item.append(details, actions);
    documentsList.append(item);
  }
}

function renderDocumentScope(documents) {
  const previousSelection = documentScope.value;
  const allDocumentsOption = document.createElement("option");
  allDocumentsOption.value = "";
  allDocumentsOption.textContent = "All indexed documents";
  documentScope.replaceChildren(allDocumentsOption);

  for (const indexedDocument of documents) {
    const option = document.createElement("option");
    option.value = indexedDocument.filename;
    option.textContent = indexedDocument.filename;
    documentScope.append(option);
  }

  const previousDocumentStillExists = documents.some(
    (indexedDocument) => indexedDocument.filename === previousSelection,
  );
  documentScope.value = previousDocumentStillExists ? previousSelection : "";
  documentScope.disabled = documents.length === 0;
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
  const validationMessage = selectedFile
    ? validateSelectedFile(selectedFile)
    : "";
  setStatus(uploadStatus, validationMessage, validationMessage ? "error" : "");
});

documentForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  const selectedFile = fileInput.files[0];
  if (!selectedFile) {
    setStatus(uploadStatus, "Choose a document before uploading.", "error");
    return;
  }

  const validationMessage = validateSelectedFile(selectedFile);
  if (validationMessage) {
    setStatus(uploadStatus, validationMessage, "error");
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
loadUploadCapabilities();
loadDocuments();

chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  const question = questionInput.value.trim();
  if (!question) {
    setStatus(chatStatus, "Enter a question first.", "error");
    return;
  }

  setButtonBusy(askButton, true, "Thinking...", "Ask documents");
  clearConversationButton.disabled = true;
  setStatus(chatStatus, "Searching indexed documents...");
  const history = conversationHistory.slice(-MAX_CONVERSATION_MESSAGES);
  const documents = documentScope.value ? [documentScope.value] : [];

  try {
    const response = await fetch("/chat/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, history, documents }),
    });

    if (!response.ok) {
      throw new Error(await getErrorMessage(response));
    }

    const data = await response.json();
    appendConversationMessage("user", question);
    appendConversationMessage("assistant", data.answer, data.sources);
    rememberConversation(question, data.answer);
    questionInput.value = "";
    questionInput.focus();
    setStatus(chatStatus, "");
  } catch (error) {
    setStatus(chatStatus, error.message, "error");
  } finally {
    setButtonBusy(askButton, false, "Thinking...", "Ask documents");
    clearConversationButton.disabled = conversationHistory.length === 0;
  }
});

clearConversationButton.addEventListener("click", clearConversation);
