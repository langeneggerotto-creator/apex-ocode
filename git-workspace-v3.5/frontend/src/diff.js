// Lightweight hand-rolled unified-diff renderer. A unified diff is already
// text-shaped and its rendering is just per-line coloring by leading
// character — deliberately not a re-vendor of Bite 4's Monaco, which would
// be a full editing engine for a job that needs none of its editing
// capability.

export function renderDiff(container, diffText) {
  container.textContent = "";
  if (!diffText) {
    const empty = document.createElement("div");
    empty.className = "diff-empty";
    empty.textContent = "No differences.";
    container.appendChild(empty);
    return;
  }
  const lines = diffText.split("\n");
  const frag = document.createDocumentFragment();
  for (const line of lines) {
    const row = document.createElement("div");
    row.className = "diff-line " + classify(line);
    row.textContent = line.length ? line : " ";
    frag.appendChild(row);
  }
  container.appendChild(frag);
}

function classify(line) {
  if (line.startsWith("+++") || line.startsWith("---")) return "diff-file-header";
  if (line.startsWith("@@")) return "diff-hunk-header";
  if (line.startsWith("+")) return "diff-add";
  if (line.startsWith("-")) return "diff-del";
  if (line.startsWith("diff ") || line.startsWith("index ")) return "diff-meta";
  return "diff-context";
}
