import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

/** Must match backend default in `backend/run_config.py` unless you set QACOPILOT_API_PORT / VITE_API_PROXY. */
const DEFAULT_API = "http://127.0.0.1:8843";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const target = (env.VITE_API_PROXY || DEFAULT_API).replace(/\/+$/, "");
  return {
    plugins: [react()],
    server: {
      port: 5173,
      proxy: {
        "/api": target,
        "/kt": target,
      },
    },
  };
});
