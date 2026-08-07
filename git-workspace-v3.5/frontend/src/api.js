// Thin fetch wrapper over the /api/git/* JSON API in server/httpserver.py.
// Every function returns the parsed JSON body; non-2xx responses throw an
// Error whose message is the server's {"error": ...} text, so callers can
// show it directly rather than a generic "request failed".

async function call(method, path, body) {
  const opts = { method, headers: {} };
  if (body !== undefined) {
    opts.headers["Content-Type"] = "application/json";
    opts.body = JSON.stringify(body);
  }
  const res = await fetch(path, opts);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.error || `request failed (${res.status})`);
  }
  return data;
}

export const api = {
  status: () => call("GET", "/api/git/status"),
  diff: (path, staged) => call("GET", `/api/git/diff?path=${encodeURIComponent(path)}&staged=${staged ? "1" : "0"}`),
  log: (limit = 50) => call("GET", `/api/git/log?limit=${limit}`),
  branches: () => call("GET", "/api/git/branches"),
  tags: () => call("GET", "/api/git/tags"),
  stashList: () => call("GET", "/api/git/stash"),
  conflicts: () => call("GET", "/api/git/conflicts"),

  stage: (paths) => call("POST", "/api/git/stage", { paths }),
  unstage: (paths) => call("POST", "/api/git/unstage", { paths }),
  commit: (message) => call("POST", "/api/git/commit", { message }),
  createBranch: (name) => call("POST", "/api/git/branch", { name }),
  deleteBranch: (name) => call("DELETE", `/api/git/branch?name=${encodeURIComponent(name)}`),
  switchBranch: (name) => call("POST", "/api/git/switch", { name }),
  createTag: (name) => call("POST", "/api/git/tag", { name }),
  stashSave: (message) => call("POST", "/api/git/stash/save", { message }),
  stashPop: (index = 0) => call("POST", "/api/git/stash/pop", { index }),
  stashDrop: (index = 0) => call("POST", "/api/git/stash/drop", { index }),
  restore: (path) => call("POST", "/api/git/restore", { path }),
  cherryPick: (sha) => call("POST", "/api/git/cherry-pick", { sha }),
  cherryPickAbort: () => call("POST", "/api/git/cherry-pick/abort"),
  rebase: (onto) => call("POST", "/api/git/rebase", { onto }),
  rebaseAbort: () => call("POST", "/api/git/rebase/abort"),
  merge: (branch) => call("POST", "/api/git/merge", { branch }),
  mergeAbort: () => call("POST", "/api/git/merge/abort"),
  resolve: (path, strategy) => call("POST", "/api/git/resolve", { path, strategy }),
};
