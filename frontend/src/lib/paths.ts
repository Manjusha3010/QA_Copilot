import { api } from "./api";
import { markWizardDone } from "./wizardStorage";

export type DataPaths = {
  pdfs: string;
  markdown: string;
  selenium: string;
  playwright: string;
  vwo_tests: string;
};

export const PATH_FIELDS: { key: keyof DataPaths; label: string; placeholder: string }[] = [
  { key: "pdfs", label: "PDFs folder (optional)", placeholder: "./data/PDF" },
  { key: "markdown", label: "Markdown notes (e.g. data/MD)", placeholder: "./data/MD" },
  { key: "selenium", label: "Selenium repo", placeholder: "./data/repos/ATB14xSeleniumAdvanceFrameworks" },
  { key: "playwright", label: "Playwright repo", placeholder: "./data/repos/Advance-Playwright-Framework" },
  {
    key: "vwo_tests",
    label: "VWO testcases CSV file (not a folder)",
    placeholder: "./data/CSV/testcases_vwo_100.csv",
  },
];

export function pathsFromMeta(meta: { paths: DataPaths }): DataPaths {
  return {
    pdfs: meta.paths.pdfs ?? "",
    markdown: meta.paths.markdown ?? "",
    selenium: meta.paths.selenium ?? "",
    playwright: meta.paths.playwright ?? "",
    vwo_tests: meta.paths.vwo_tests ?? "",
  };
}

export async function saveDataPaths(paths: DataPaths): Promise<void> {
  await api("/api/settings/paths", {
    method: "POST",
    body: JSON.stringify({
      pdfs: paths.pdfs || null,
      markdown: paths.markdown || null,
      selenium: paths.selenium || null,
      playwright: paths.playwright || null,
      vwo_tests: paths.vwo_tests || null,
    }),
  });
  markWizardDone();
}
