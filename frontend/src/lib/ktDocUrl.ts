/** KT HTML served by the API from `<project>/KT/` (e.g. index.html). */
const DEFAULT_API = "http://127.0.0.1:8843";

export function ktDocUrl(): string {
  if (import.meta.env.DEV) {
    const base = (import.meta.env.VITE_API_PROXY || DEFAULT_API).replace(/\/+$/, "");
    return `${base}/kt/index.html`;
  }
  return "/kt/index.html";
}
