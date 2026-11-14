"use strict";

const base = document.documentElement.dataset.base || "";
const fileInput = document.getElementById("file-input");
const dropzone = document.getElementById("dropzone");
const importButton = document.getElementById("import-button");
const message = document.getElementById("import-message");

function setMessage(text, tone = "") {
  message.textContent = text;
  message.className = `feedback ${tone}`;
}

function selectedFile(file) {
  if (!file) return;
  document.getElementById("drop-title").textContent = file.name;
  document.getElementById("drop-caption").textContent = `${(file.size / 1024).toFixed(1)} KB · Ready to stage`;
  importButton.disabled = !file.name.toLowerCase().endsWith(".json") || file.size > 2 * 1024 * 1024;
  if (importButton.disabled) setMessage("Select a .json file no larger than 2 MB.", "error");
  else setMessage("");
}

dropzone.addEventListener("click", () => fileInput.click());
dropzone.addEventListener("keydown", event => {
  if (event.key === "Enter" || event.key === " ") { event.preventDefault(); fileInput.click(); }
});
fileInput.addEventListener("change", () => selectedFile(fileInput.files[0]));
["dragenter", "dragover"].forEach(type => dropzone.addEventListener(type, event => {
  event.preventDefault(); dropzone.classList.add("drag-over");
}));
["dragleave", "drop"].forEach(type => dropzone.addEventListener(type, event => {
  event.preventDefault(); dropzone.classList.remove("drag-over");
}));
dropzone.addEventListener("drop", event => {
  const file = event.dataTransfer.files[0];
  if (!file) return;
  const transfer = new DataTransfer(); transfer.items.add(file);
  fileInput.files = transfer.files;
  selectedFile(file);
});

function textNode(element, content, className) {
  const node = document.createElement(element);
  node.textContent = content;
  if (className) node.className = className;
  return node;
}

function renderState(state) {
  const knowledge = state.knowledge;
  const datasets = state.datasets || [];
  document.getElementById("metric-knowledge").textContent = knowledge ? "Ready" : "Not loaded";
  document.getElementById("metric-datasets").textContent = String(datasets.length);
  document.getElementById("metric-drafts").textContent = String(datasets.reduce((total, dataset) => total + (dataset.content_count || 0), 0));
  document.getElementById("dataset-count").textContent = `${datasets.length} imported`;
  document.getElementById("knowledge-empty").hidden = !!knowledge;
  document.getElementById("knowledge-loaded").hidden = !knowledge;
  if (knowledge) {
    document.getElementById("knowledge-name").textContent = knowledge.name;
    document.getElementById("knowledge-goal").textContent = knowledge.primary_goal;
    document.getElementById("knowledge-filename").textContent = `Source: ${knowledge.filename}`;
    const tags = document.getElementById("knowledge-audiences");
    tags.replaceChildren(...(knowledge.audiences || []).map(audience => textNode("span", audience, "tag")));
  }
  const list = document.getElementById("dataset-list");
  list.replaceChildren();
  document.getElementById("dataset-empty").hidden = datasets.length > 0;
  datasets.forEach(dataset => {
    const card = textNode("article", "", "dataset-row");
    const icon = textNode("div", "{}", "dataset-icon");
    const info = textNode("div", "", "dataset-info");
    info.append(textNode("h3", dataset.name));
    info.append(textNode("p", `${dataset.filename} · ${dataset.campaigns?.length || 0} campaign(s) · ${dataset.daily_plan_count || 0} daily plans`));
    const figures = textNode("div", "", "dataset-figures");
    figures.append(textNode("strong", `${dataset.content_count || 0} drafts`));
    figures.append(textNode("span", "Needs human review", "review-pill"));
    card.append(icon, info, figures);
    list.append(card);
  });
}

async function refresh() {
  const request = await fetch(`${base}/api/state`, {cache: "no-store"});
  if (!request.ok) throw new Error("Could not load local workspace state.");
  renderState(await request.json());
}

document.getElementById("import-form").addEventListener("submit", async event => {
  event.preventDefault();
  if (!fileInput.files[0]) return;
  importButton.disabled = true;
  importButton.textContent = "Validating and staging…";
  setMessage("Checking your JSON structure…");
  try {
    const payload = new FormData();
    payload.append("file", fileInput.files[0]);
    const request = await fetch(`${base}/api/import`, {method: "POST", body: payload});
    const result = await request.json();
    if (!request.ok || !result.ok) throw new Error(result.error || "Could not stage this file.");
    setMessage(result.duplicate ? "File was already staged. Workspace is up to date." : `${result.kind === "knowledge" ? "Knowledge" : "Dataset"} imported successfully.`, "success");
    await refresh();
  } catch (error) { setMessage(error.message || "Upload failed.", "error"); }
  finally { importButton.disabled = false; importButton.textContent = "Stage JSON file →"; }
});

refresh().catch(error => setMessage(error.message, "error"));
