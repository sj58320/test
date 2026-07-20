export const RECENT_VIEW_LIMIT = 5;

export function normalizeRecentViews(value, limit = RECENT_VIEW_LIMIT) {
  if (!Array.isArray(value)) return [];
  const seen = new Set();
  return value.filter(item => {
    if (!item || typeof item !== "object") return false;
    if (typeof item.targetId !== "string" || !item.targetId.trim()) return false;
    if (typeof item.type !== "string" || !item.type.trim()) return false;
    if (typeof item.title !== "string" || !item.title.trim()) return false;
    if (seen.has(item.targetId)) return false;
    seen.add(item.targetId);
    return true;
  }).slice(0, limit).map(item => ({
    targetId: item.targetId,
    type: item.type,
    title: item.title,
    visitedAt: Number(item.visitedAt) || Date.now()
  }));
}

export function addRecentView(value, entry, limit = RECENT_VIEW_LIMIT) {
  const current = normalizeRecentViews(value, limit);
  const next = {
    targetId: String(entry?.targetId || "").trim(),
    type: String(entry?.type || "").trim(),
    title: String(entry?.title || "").trim(),
    visitedAt: Number(entry?.visitedAt) || Date.now()
  };
  if (!next.targetId || !next.type || !next.title) return current;
  return [next, ...current.filter(item => item.targetId !== next.targetId)].slice(0, limit);
}

export function removeRecentView(value, targetId, limit = RECENT_VIEW_LIMIT) {
  return normalizeRecentViews(value, limit).filter(item => item.targetId !== targetId);
}
