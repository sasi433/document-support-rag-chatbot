const documentForm = document.querySelector("#document-form");
const fileInput = document.querySelector("#document-file");
const fileLabel = document.querySelector("#file-label");
const uploadButton = document.querySelector("#upload-button");
const uploadStatus = document.querySelector("#upload-status");

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
    questionInput.focus();
  } catch (error) {
    setStatus(uploadStatus, error.message, "error");
  } finally {
    setButtonBusy(uploadButton, false, "Uploading...", "Upload and index");
  }
});

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
