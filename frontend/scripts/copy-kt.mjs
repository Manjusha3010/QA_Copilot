/** Copy ../KT into public/kt so Vite + Vercel serve KT docs at /kt/ */
import { cpSync, existsSync, mkdirSync, rmSync } from "fs";
import { dirname, join } from "path";
import { fileURLToPath } from "url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const src = join(root, "..", "KT");
const dest = join(root, "public", "kt");

if (!existsSync(src)) {
  console.warn("copy-kt: KT folder not found, skipping");
  process.exit(0);
}

mkdirSync(join(root, "public"), { recursive: true });
if (existsSync(dest)) rmSync(dest, { recursive: true });
cpSync(src, dest, { recursive: true });
console.log("copy-kt: copied KT -> frontend/public/kt");
