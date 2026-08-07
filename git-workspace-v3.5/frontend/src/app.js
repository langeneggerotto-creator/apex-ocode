import { api } from "./api.js";
import { renderDiff } from "./diff.js";

const $ = (id) => document.getElementById(id);

const state = {
  selected: null, // { path, staged }
};

function setStatusMsg(text, isError = false) {
  const el = $("status-msg");
  el.textContent = text;
  el.classList.toggle("error", isError);
}

async function guarded(fn, okMsg) {
  try {
    await fn();
    if (okMsg) setStatusMsg(okMsg);
    await refreshAll();
  } catch (err) {
    setStatusMsg(String(err.message || err), true);
  }
}

function li(path, actions) {
  const item = document.createElement("li");
  const label = document.createElement("button");
  label.className = "file-name";
  label.textContent = path;
  label.addEventListener("click", () => selectFile(path, actions.staged === true));
  item.appendChild(label);
  for (const [text, handler] of actions.buttons) {
    const btn = document.createElement("button");
    btn.className = "file-action";
    btn.textContent = text;
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      handler(path);
    });
    item.appendChild(btn);
  }
  return item;
}

function renderFileList(ulId, paths, buildActions) {
  const ul = $(ulId);
  ul.textContent = "";
  for (const path of paths) {
    ul.appendChild(li(path, buildActions(path)));
  }
}

async function selectFile(path, staged) {
  state.selected = { path, staged };
  $("diff-file-label").textContent = `${path}${staged ? " (staged)" : ""}`;
  try {
    const { diff } = await api.diff(path, staged);
    renderDiff($("diff-content"), diff);
  } catch (err) {
    renderDiff($("diff-content"), "");
    setStatusMsg(String(err.message || err), true);
  }
}

async function refreshStatus() {
  const status = await api.status();
  renderFileList("list-staged", status.staged, () => ({
    staged: true,
    buttons: [["Unstage", (p) => guarded(() => api.unstage([p]))]],
  }));
  renderFileList("list-unstaged", status.unstaged, () => ({
    staged: false,
    buttons: [
      ["Stage", (p) => guarded(() => api.stage([p]))],
      ["Discard", (p) => guarded(() => api.restore(p))],
    ],
  }));
  renderFileList("list-untracked", status.untracked, () => ({
    staged: false,
    buttons: [["Stage", (p) => guarded(() => api.stage([p]))]],
  }));
  renderFileList("list-conflicted", status.conflicted, () => ({
    staged: false,
    buttons: [
      ["Keep ours", (p) => guarded(() => api.resolve(p, "ours"), `resolved ${p} (ours)`)],
      ["Keep theirs", (p) => guarded(() => api.resolve(p, "theirs"), `resolved ${p} (theirs)`)],
      ["Mark resolved", (p) => guarded(() => api.resolve(p, "resolved"), `marked ${p} resolved`)],
    ],
  }));

  const hasConflicts = status.conflicted.length > 0;
  $("conflict-banner").classList.toggle("hidden", !hasConflicts);
}

async function refreshBranches() {
  const branches = await api.branches();
  const select = $("branch-select");
  select.textContent = "";
  let current = "";
  for (const b of branches) {
    const opt = document.createElement("option");
    opt.value = b.name;
    opt.textContent = b.name;
    if (b.is_current) {
      opt.selected = true;
      current = b.name;
    }
    select.appendChild(opt);
  }
  $("branch-label").textContent = current ? `On ${current}` : "(detached)";
}

async function refreshTags() {
  const { tags } = await api.tags();
  const ul = $("list-tags");
  ul.textContent = "";
  for (const t of tags) {
    const item = document.createElement("li");
    item.textContent = t;
    ul.appendChild(item);
  }
}

async function refreshStash() {
  const { stash } = await api.stashList();
  const ul = $("list-stash");
  ul.textContent = "";
  stash.forEach((entry, index) => {
    const item = document.createElement("li");
    const label = document.createElement("span");
    label.textContent = entry;
    item.appendChild(label);
    const popBtn = document.createElement("button");
    popBtn.textContent = "Pop";
    popBtn.addEventListener("click", () => guarded(() => api.stashPop(index), `popped ${entry}`));
    item.appendChild(popBtn);
    const dropBtn = document.createElement("button");
    dropBtn.textContent = "Drop";
    dropBtn.addEventListener("click", () => guarded(() => api.stashDrop(index), `dropped ${entry}`));
    item.appendChild(dropBtn);
    ul.appendChild(item);
  });
}

async function refreshHistory() {
  const commits = await api.log(50);
  const ul = $("list-history");
  ul.textContent = "";
  for (const c of commits) {
    const item = document.createElement("li");
    item.innerHTML = "";
    const sha = document.createElement("span");
    sha.className = "commit-sha";
    sha.textContent = c.sha.slice(0, 8);
    const subject = document.createElement("span");
    subject.className = "commit-subject";
    subject.textContent = c.subject;
    item.appendChild(sha);
    item.appendChild(subject);
    ul.appendChild(item);
  }
}

async function refreshAll() {
  await Promise.all([refreshStatus(), refreshBranches(), refreshTags(), refreshStash(), refreshHistory()]);
}

function wireToolbar() {
  $("branch-select").addEventListener("change", (e) => {
    guarded(() => api.switchBranch(e.target.value), `switched to ${e.target.value}`);
  });

  $("btn-new-branch").addEventListener("click", () => {
    const name = prompt("New branch name:");
    if (name) guarded(() => api.createBranch(name), `created branch ${name}`);
  });

  $("btn-new-tag").addEventListener("click", () => {
    const name = prompt("New tag name:");
    if (name) guarded(() => api.createTag(name), `created tag ${name}`);
  });

  $("btn-commit").addEventListener("click", () => {
    const message = $("commit-message").value.trim();
    if (!message) {
      setStatusMsg("commit message is required", true);
      return;
    }
    guarded(async () => {
      await api.commit(message);
      $("commit-message").value = "";
    }, "committed");
  });

  $("btn-stash-save").addEventListener("click", () => {
    const message = prompt("Stash message (optional):") || undefined;
    guarded(() => api.stashSave(message), "stashed changes");
  });

  $("btn-abort").addEventListener("click", () => {
    guarded(async () => {
      // Any of the three abort operations is a no-op if that particular
      // operation isn't the one in progress (check=False in gitservice),
      // so trying all three is safe and covers merge/rebase/cherry-pick.
      await api.mergeAbort();
      await api.rebaseAbort();
      await api.cherryPickAbort();
    }, "aborted");
  });

  for (const btn of document.querySelectorAll(".tab-btn")) {
    btn.addEventListener("click", () => {
      for (const b of document.querySelectorAll(".tab-btn")) {
        b.classList.toggle("active", b === btn);
        b.setAttribute("aria-selected", b === btn ? "true" : "false");
      }
      for (const panel of document.querySelectorAll(".tab-content")) {
        panel.classList.toggle("hidden", panel.id !== `tab-${btn.dataset.tab}`);
      }
    });
  }
}

async function init() {
  wireToolbar();
  await refreshAll();
  setStatusMsg("ready");
}

init();
