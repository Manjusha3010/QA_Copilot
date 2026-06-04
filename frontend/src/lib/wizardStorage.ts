export const WIZARD_DONE_KEY = "qacopilot_wizard_done";

export function isWizardDone(): boolean {
  return localStorage.getItem(WIZARD_DONE_KEY) === "1";
}

export function markWizardDone(): void {
  localStorage.setItem(WIZARD_DONE_KEY, "1");
}
