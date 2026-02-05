## Web app (GitHub Pages)

This folder contains a static web app that runs the generator in the browser via Pyodide.

### Local preview

From the repo root:

- `python3 -m http.server 8000`
- Open `http://localhost:8000/docs/`

### GitHub Pages

This repo includes an Actions workflow that deploys the `docs/` folder to GitHub Pages.

In GitHub repo settings:

- Settings → Pages
- Source: **GitHub Actions**

Then your tool will be available at:

- `https://<your-username>.github.io/<repo-name>/`

(Exact URL depends on repository name.)

For this repo, the live URL is:

- https://sunnydesigntech.github.io/CardBoxGen/
