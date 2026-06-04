export const COLLECTION_PILLS: { id: string; label: string }[] = [
  { id: "selenium_code", label: "Selenium" },
  { id: "playwright_code", label: "Playwright" },
  { id: "vwo_testcases", label: "Test Cases" },
  { id: "vwo_docs", label: "PRDs / Docs" },
  { id: "vwo_bugs", label: "JIRA Bugs" },
];

export function routerCaption(collections: string[]): string {
  if (collections.length === 0) return "No collections selected.";
  if (collections.length > 2) return "Searching all knowledge bases.";
  const c = collections[0];
  if (c === "vwo_testcases") return "Filtering test cases by priority and module";
  if (c === "vwo_docs") return "Searching product requirements and PDF documentation";
  if (c === "vwo_bugs") return "Searching JIRA bug exports and markdown notes";
  if (c === "selenium_code") return "Searching Selenium Java / TestNG automation code";
  if (c === "playwright_code") return "Searching Playwright TypeScript test framework";
  return `Searching ${collections.join(" and ")}`;
}

export function chunkDisplayId(pointId: unknown, index: number): string {
  if (pointId != null && String(pointId) !== "") return `r${pointId}-c0`;
  return `r${index}-c0`;
}
