## Web app (GitHub Pages)

This folder contains a static web app that runs the generator in the browser via Pyodide.

### Local preview

From the repo root:

- `python3 -m http.server 8000`
- Open `http://localhost:8000/docs/`

### GitHub Pages

In GitHub repo settings:

- Settings → Pages
- Source: `Deploy from a branch`
- Branch: `main` (or `master`) and folder: `/docs`

Then your tool will be available at:

- `https://<your-username>.github.io/<repo-name>/`

(Exact URL depends on repository name.)
