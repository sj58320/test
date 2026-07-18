const FILTER_LINKS = new Map([
  ["skins-human", { tab: "skins", skinCategory: "human" }],
  ["skins-zombie", { tab: "skins", skinCategory: "zombie" }],
  ["skins-weapon", { tab: "skins", skinCategory: "weapon" }],
  ["commands", { tab: "cmds", commandPage: "all" }],
  ["commands-donator", { tab: "cmds", commandPage: "donator" }]
]);

export function resolveFilterDeepLink(value) {
  const hash = decodeURIComponent(String(value || "").replace(/^#/, ""));
  const state = FILTER_LINKS.get(hash);
  return state ? { ...state } : null;
}

export function skinCategoryDeepLink(category) {
  return ["human", "zombie", "weapon"].includes(category)
    ? `skins-${category}`
    : null;
}

export function commandPageDeepLink(pageId) {
  if (pageId === "all") return "commands";
  if (pageId === "donator") return "commands-donator";
  return "cmds";
}
