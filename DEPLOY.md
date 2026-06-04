# Deploy QA Copilot

## GitHub

Repository: https://github.com/Manjusha3010/QA_Copilot.git

```powershell
cd QACopilot
git init
git add .
git commit -m "Initial commit: QA Copilot v1.0.0"
git branch -M main
git remote add origin https://github.com/Manjusha3010/QA_Copilot.git
git push -u origin main
```

## Vercel (React UI)

Vercel hosts the **frontend only**. The Python API (Qdrant, BGE-M3, Groq) must run elsewhere (your PC, Railway, Render, etc.).

### 1. Import project

1. Go to [vercel.com](https://vercel.com) → **Add New Project**
2. Import **Manjusha3010/QA_Copilot** from GitHub
3. **Root Directory:** leave as repo root (where `vercel.json` lives)
4. Vercel reads `vercel.json` automatically (`outputDirectory`: `frontend/dist`)

### 2. Environment variables (Vercel)

| Variable | Example | Purpose |
|----------|---------|---------|
| `VITE_API_PROXY` | `https://your-api-host.com` | Build-time API URL for production fetches |

Without `VITE_API_PROXY`, the built UI calls `/api` on the same Vercel domain — those routes are **not** implemented on Vercel. Point this at your running FastAPI server.

### 3. Deploy

Click **Deploy**. KT docs are copied into the build at `/kt/` (see `frontend/scripts/copy-kt.mjs`).

### 4. API hosting (required for Chat / RAG)

Run locally or deploy `app.py` to a Python host with:

- Python 3.11–3.13
- `GROQ_API_KEY`, Qdrant storage, model weights
- Port 8843 (or set `QACOPILOT_API_PORT`)

Then set `VITE_API_PROXY` in Vercel to that public API URL and **redeploy** the frontend.

## Local production preview

```powershell
cd frontend
npm run build
npm run preview
```
