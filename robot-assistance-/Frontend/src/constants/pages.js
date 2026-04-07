export const APP_PAGES = [
  { id: "dashboard", label: "Dashboard" },
  { id: "meetings", label: "Meetings" },
  { id: "reminders", label: "Reminders" },
  { id: "notifications", label: "Notifications" },
  { id: "summary", label: "Executive Summary" },
];

const PAGE_IDS = new Set(APP_PAGES.map((page) => page.id));

export function getPageFromHash(hash) {
  const cleanHash = String(hash || "").replace(/^#/, "");
  return PAGE_IDS.has(cleanHash) ? cleanHash : "dashboard";
}
