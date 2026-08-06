// Thin fetch wrapper for the backend file-service API. Nothing else in the
// frontend talks to the backend directly — every read/write goes through here,
// so there is exactly one place that knows the API shape.

export async function fetchTree() {
  const res = await fetch("/api/tree");
  if (!res.ok) throw new Error(`GET /api/tree failed: ${res.status}`);
  return res.json();
}

export async function fetchFile(path) {
  const res = await fetch(`/api/file?path=${encodeURIComponent(path)}`);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new ApiError(res.status, body.error || `GET /api/file failed: ${res.status}`);
  }
  return res.json(); // { content, hash }
}

export async function saveFile(path, content, expectedHash) {
  const res = await fetch(`/api/file?path=${encodeURIComponent(path)}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content, expected_hash: expectedHash }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new ApiError(res.status, body.error || `PUT /api/file failed: ${res.status}`);
  }
  return res.json(); // { hash }
}

export class ApiError extends Error {
  constructor(status, message) {
    super(message);
    this.status = status;
  }
}
