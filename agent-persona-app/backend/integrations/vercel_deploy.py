"""
Pushes a set of files to a real, permanent Vercel deployment via Vercel's
REST API -- used to promote a generated site out of Open Lovable's
ephemeral sandbox (which expires) into something with a durable URL.

Docs reference: https://vercel.com/docs/rest-api/reference/endpoints/deployments/create-a-new-deployment
"""
import os
import re
import base64
import requests

VERCEL_API_BASE = "https://api.vercel.com"


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9-]", "-", name.lower())
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug[:50] or "agency-site"


def _scaffold_files() -> dict:
    """Minimal Vite + React + Tailwind scaffold -- the same shape Open
    Lovable's own sandbox sets up, but these never get handed back to us
    (get-sandbox-files is broken in this build), so we recreate them here
    to give Vercel something buildable alongside the generated components."""
    return {
        "package.json": """{
  "name": "agency-site",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "lucide-react": "^0.383.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.0.0",
    "vite": "^4.3.9",
    "tailwindcss": "^3.3.0",
    "postcss": "^8.4.31",
    "autoprefixer": "^10.4.16"
  }
}""",
        "vite.config.js": """import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
})""",
        "tailwind.config.js": """/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: { extend: {} },
  plugins: [],
}""",
        "postcss.config.js": """export default {
  plugins: { tailwindcss: {}, autoprefixer: {} },
}""",
        "index.html": """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Agency Site</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>""",
        "src/main.jsx": """import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)""",
    }


def deploy_files(files: dict, project_name_hint: str) -> dict:
    """files: {path: content} as parsed from the generated <file> blocks.
    Merges in a minimal Vite/React/Tailwind scaffold (package.json,
    vite.config.js, index.html, etc.) since the generated files alone are
    just components with nothing to actually build them.

    NOTE: Vercel's file size limits apply per-file for inline `data` uploads --
    fine for typical generated component files, but if this errors on large
    files, the two-step /v2/files upload-by-sha flow would be the fallback.
    """
    token = os.environ["VERCEL_TOKEN"]
    team_id = os.environ.get("VERCEL_TEAM_ID")

    project_name = _slugify(project_name_hint)

    # generated files win on any path collision (e.g. if the AI also wrote main.jsx)
    all_files = {**_scaffold_files(), **files}

    deployment_files = []
    for path, content in all_files.items():
        normalized_path = path.replace("/home/user/app/", "").lstrip("/")
        if not normalized_path:
            continue
        data_b64 = base64.b64encode(content.encode("utf-8")).decode("ascii")
        deployment_files.append({"file": normalized_path, "data": data_b64, "encoding": "base64"})

    payload = {
        "name": project_name,
        "files": deployment_files,
        "target": "production",
        "projectSettings": {
            "framework": "vite",
        },
    }

    params = {"teamId": team_id} if team_id else {}
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    resp = requests.post(
        f"{VERCEL_API_BASE}/v13/deployments",
        params=params,
        headers=headers,
        json=payload,
        timeout=120,
    )
    resp.raise_for_status()
    data = resp.json()

    url = data.get("url")
    return {
        "deployment_id": data.get("id"),
        "url": f"https://{url}" if url else None,
        "raw": data,
    }