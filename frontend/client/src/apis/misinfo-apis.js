import axiosClient from "./axios-client.js";

function unwrapList(payload, keys = []) {
  if (Array.isArray(payload)) return payload;
  if (!payload || typeof payload !== "object") return [];
  for (const k of keys) {
    if (Array.isArray(payload[k])) return payload[k];
  }
  for (const v of Object.values(payload)) {
    if (Array.isArray(v)) return v;
  }
  return [];
}

async function getJsonList(paths, unwrapKeys) {
  let lastError = null;
  for (const path of paths) {
    const p = path.startsWith("/") ? path : `/${path}`;
    try {
      const { data, status } = await apiClient.get(p, { validateStatus: () => true });
      if (status >= 200 && status < 300) {
        return {
          ok: true,
          data: unwrapList(data, unwrapKeys),
          pathUsed: p,
        };
      }
      lastError = new Error(`GET ${p} → HTTP ${status}`);
      if (status === 404 || status === 405) {
        continue;
      }
      break;
    } catch (e) {
      lastError = e;
    }
  }
  return { ok: false, data: [], error: lastError, pathUsed: null };
}

/**
 * GET narratives (tries common backend paths).
 */
export async function getNarratives() {
  return getJsonList(
    ["/narratives", "/misinformation/narratives", "/misinfo/narratives"],
    ["narratives", "items", "results", "data", "content"]
  );
}

/**
 * GET posts.
 */
export async function getPosts() {
  return getJsonList(
    ["/posts", "/misinformation/posts", "/misinfo/posts"],
    ["posts", "items", "results", "data", "content"]
  );
}

/**
 * GET incidents.
 */
export async function getIncidents() {
  return getJsonList(
    ["/incidents", "/misinformation/incidents", "/misinfo/incidents"],
    ["incidents", "items", "results", "data", "content"]
  );
}
