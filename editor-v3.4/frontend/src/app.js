import { fetchTree, fetchFile, saveFile, ApiError } from "./api.js";

const LANGUAGE_BY_EXT = {
  ".js": "javascript",
  ".mjs": "javascript",
  ".ts": "typescript",
  ".json": "json",
  ".py": "python",
  ".md": "markdown",
  ".html": "html",
  ".css": "css",
  ".yml": "yaml",
  ".yaml": "yaml",
  ".sh": "shell",
};

function languageForPath(path) {
  const dot = path.lastIndexOf(".");
  if (dot === -1) return "plaintext";
  return LANGUAGE_BY_EXT[path.slice(dot).toLowerCase()] || "plaintext";
}

function draftKey(path) {
  return `ocode-editor-draft:${window.location.host}:${path}`;
}

// -- state ------------------------------------------------------------------

const panes = [
  {
    editor: null,
    wrapper: document.getElementById("pane0"),
    editorContainer: document.getElementById("pane0-editor"),
    activeTabId: null,
    visible: true,
  },
  {
    editor: null,
    wrapper: document.getElementById("pane1"),
    editorContainer: document.getElementById("pane1-editor"),
    activeTabId: null,
    visible: false,
  },
];
const tabs = new Map(); // id -> tab record
const tabOrderByPane = { 0: [], 1: [] };
let nextTabId = 1;
let targetPane = 0;
let diffOriginalModel = null;

function activePane() {
  return targetPane;
}

function activeTab() {
  const pane = panes[activePane()];
  return pane.activeTabId ? tabs.get(pane.activeTabId) : null;
}

// -- tree ---------------------------------------------------------------------

async function renderTree() {
  const entries = await fetchTree();
  const root = document.getElementById("tree");
  root.innerHTML = "";
  root.setAttribute("role", "list");
  root.setAttribute("aria-label", "Workspace files");
  for (const entry of entries) {
    if (entry.is_dir) continue; // flat file list is enough for this bite's scope
    const li = document.createElement("div");
    li.setAttribute("role", "listitem");
    const btn = document.createElement("button");
    btn.className = "tree-item";
    btn.textContent = entry.path;
    btn.setAttribute("aria-label", `Open ${entry.path}`);
    btn.addEventListener("click", () => openFile(entry.path));
    li.appendChild(btn);
    root.appendChild(li);
  }
}

// -- Monaco setup ---------------------------------------------------------------

function ensurePaneEditor(paneIndex) {
  const pane = panes[paneIndex];
  if (pane.editor) return pane.editor;
  pane.editor = monaco.editor.create(pane.editorContainer, {
    value: "",
    language: "plaintext",
    automaticLayout: true,
    ariaLabel: `Editor pane ${paneIndex + 1}`,
  });
  return pane.editor;
}

// -- tabs -----------------------------------------------------------------------

async function openFile(path) {
  const paneIndex = activePane();
  const existing = tabOrderByPane[paneIndex]
    .map((id) => tabs.get(id))
    .find((t) => t.path === path);
  if (existing) {
    activateTab(paneIndex, existing.id);
    return;
  }

  const { content: serverContent, hash: savedHash } = await fetchFile(path);

  let liveContent = serverContent;
  let dirty = false;
  const draftRaw = localStorage.getItem(draftKey(path));
  if (draftRaw) {
    try {
      const draft = JSON.parse(draftRaw);
      if (draft.hash === savedHash && draft.content !== serverContent) {
        if (window.confirm(`Restore unsaved draft for ${path} from a previous session?`)) {
          liveContent = draft.content;
          dirty = true;
        } else {
          localStorage.removeItem(draftKey(path));
        }
      } else if (draft.hash !== savedHash) {
        // The file changed on disk since the draft was taken; the draft is
        // stale relative to a different base, so don't offer to restore it
        // silently — drop it rather than risk a confusing merge.
        localStorage.removeItem(draftKey(path));
      }
    } catch {
      localStorage.removeItem(draftKey(path));
    }
  }

  const id = nextTabId++;
  const uri = monaco.Uri.parse(`inmemory://ocode-editor/tab-${id}/${path}`);
  const model = monaco.editor.createModel(liveContent, languageForPath(path), uri);

  const tab = { id, path, model, savedContent: serverContent, savedHash, dirty, pane: paneIndex };
  tabs.set(id, tab);
  tabOrderByPane[paneIndex].push(id);

  model.onDidChangeContent(() => onModelChanged(tab));

  renderTabBar(paneIndex);
  activateTab(paneIndex, id);
  if (dirty) persistDraft(tab);
}

function onModelChanged(tab) {
  const value = tab.model.getValue();
  tab.dirty = value !== tab.savedContent;
  persistDraft(tab);
  renderTabBar(tab.pane);
}

let draftDebounce = new Map();
function persistDraft(tab) {
  clearTimeout(draftDebounce.get(tab.id));
  draftDebounce.set(
    tab.id,
    setTimeout(() => {
      if (tab.dirty) {
        localStorage.setItem(
          draftKey(tab.path),
          JSON.stringify({ content: tab.model.getValue(), hash: tab.savedHash })
        );
      } else {
        localStorage.removeItem(draftKey(tab.path));
      }
    }, 200)
  );
}

function activateTab(paneIndex, tabId) {
  const pane = panes[paneIndex];
  pane.visible = true;
  pane.wrapper.classList.remove("hidden");
  const editor = ensurePaneEditor(paneIndex);
  const tab = tabs.get(tabId);
  editor.setModel(tab.model);
  pane.activeTabId = tabId;
  renderTabBar(paneIndex);
  updateWindowTitle();
}

function closeTab(paneIndex, tabId) {
  const tab = tabs.get(tabId);
  if (tab.dirty && !window.confirm(`${tab.path} has unsaved changes. Close anyway?`)) {
    return;
  }
  const order = tabOrderByPane[paneIndex];
  const idx = order.indexOf(tabId);
  if (idx !== -1) order.splice(idx, 1);
  tabs.delete(tabId);
  localStorage.removeItem(draftKey(tab.path));
  tab.model.dispose();

  const pane = panes[paneIndex];
  if (pane.activeTabId === tabId) {
    const next = order[idx] ?? order[idx - 1];
    if (next !== undefined) {
      activateTab(paneIndex, next);
    } else {
      pane.activeTabId = null;
      pane.editor.setModel(monaco.editor.createModel("", "plaintext"));
    }
  }
  renderTabBar(paneIndex);
}

async function saveTab(tab) {
  const value = tab.model.getValue();
  try {
    const { hash } = await saveFile(tab.path, value, tab.savedHash);
    tab.savedHash = hash;
    tab.savedContent = value;
    tab.dirty = false;
    localStorage.removeItem(draftKey(tab.path));
    renderTabBar(tab.pane);
    setStatus(`Saved ${tab.path}`);
  } catch (err) {
    if (err instanceof ApiError && err.status === 409) {
      window.alert(
        `Save conflict: ${tab.path} was modified on disk since it was opened. Reload the file and reapply your change.`
      );
    } else {
      window.alert(`Save failed: ${err.message}`);
    }
  }
}

function renderTabBar(paneIndex) {
  const bar = document.getElementById(`tabbar${paneIndex}`);
  bar.innerHTML = "";
  bar.setAttribute("role", "tablist");
  bar.setAttribute("aria-label", `Open files in pane ${paneIndex + 1}`);
  const pane = panes[paneIndex];
  for (const id of tabOrderByPane[paneIndex]) {
    const tab = tabs.get(id);
    const el = document.createElement("div");
    el.className = "tab" + (pane.activeTabId === id ? " active" : "");
    el.setAttribute("role", "tab");
    el.setAttribute("aria-selected", String(pane.activeTabId === id));
    el.setAttribute(
      "aria-label",
      `${tab.path}${tab.dirty ? " (unsaved changes)" : ""}`
    );
    el.tabIndex = 0;

    const label = document.createElement("span");
    label.className = "tab-label";
    label.textContent = (tab.dirty ? "● " : "") + tab.path;
    el.appendChild(label);

    const closeBtn = document.createElement("button");
    closeBtn.className = "tab-close";
    closeBtn.textContent = "×";
    closeBtn.setAttribute("aria-label", `Close ${tab.path}`);
    closeBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      closeTab(paneIndex, id);
    });
    el.appendChild(closeBtn);

    el.addEventListener("click", () => activateTab(paneIndex, id));
    el.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        activateTab(paneIndex, id);
      }
    });

    bar.appendChild(el);
  }
}

function updateWindowTitle() {
  const tab = activeTab();
  document.title = tab ? `${tab.dirty ? "● " : ""}${tab.path} — OCode Editor` : "OCode Editor";
}

function setStatus(text) {
  document.getElementById("status").textContent = text;
}

// -- toolbar actions ------------------------------------------------------------

function currentPaneEditor() {
  return panes[activePane()].editor;
}

document.getElementById("btn-save").addEventListener("click", () => {
  const tab = activeTab();
  if (tab) saveTab(tab);
});

document.getElementById("btn-find").addEventListener("click", () => {
  const editor = currentPaneEditor();
  if (editor) editor.getAction("actions.find").run();
});

document.getElementById("btn-replace").addEventListener("click", () => {
  const editor = currentPaneEditor();
  if (editor) editor.getAction("editor.action.startFindReplaceAction").run();
});

document.getElementById("btn-format").addEventListener("click", () => {
  const editor = currentPaneEditor();
  if (editor) editor.getAction("editor.action.formatDocument").run();
});

document.getElementById("btn-split").addEventListener("click", () => {
  const pane2 = panes[1];
  pane2.visible = !pane2.visible;
  pane2.wrapper.classList.toggle("hidden", !pane2.visible);
  document.getElementById("editors").classList.toggle("split", pane2.visible);
  if (pane2.visible) ensurePaneEditor(1);
  document.getElementById("pane-select").classList.toggle("hidden", !pane2.visible);
});

document.getElementById("pane-select").addEventListener("change", (e) => {
  targetPane = Number(e.target.value);
});

document.getElementById("btn-diff").addEventListener("click", () => {
  const tab = activeTab();
  if (!tab) return;
  const overlay = document.getElementById("diff-overlay");
  overlay.classList.remove("hidden");
  const container = document.getElementById("diff-container");
  container.innerHTML = "";
  const diffEditor = monaco.editor.createDiffEditor(container, { automaticLayout: true, readOnly: true });
  diffOriginalModel = monaco.editor.createModel(tab.savedContent, tab.model.getLanguageId());
  diffEditor.setModel({ original: diffOriginalModel, modified: tab.model });
  overlay._diffEditor = diffEditor;
});

document.getElementById("btn-diff-close").addEventListener("click", () => {
  const overlay = document.getElementById("diff-overlay");
  overlay.classList.add("hidden");
  if (overlay._diffEditor) {
    overlay._diffEditor.dispose();
    overlay._diffEditor = null;
  }
  if (diffOriginalModel) {
    diffOriginalModel.dispose();
    diffOriginalModel = null;
  }
});

window.addEventListener("beforeunload", (e) => {
  const anyDirty = [...tabs.values()].some((t) => t.dirty);
  if (anyDirty) {
    e.preventDefault();
    e.returnValue = "";
  }
});

window.addEventListener("keydown", (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key === "s") {
    e.preventDefault();
    const tab = activeTab();
    if (tab) saveTab(tab);
  }
});

// -- init -------------------------------------------------------------------

export async function init() {
  ensurePaneEditor(0);
  await renderTree();
  setStatus("Ready");
}
