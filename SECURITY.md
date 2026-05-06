# Security Policy

CardBoxGen is a static web app and Python package. The public app runs fully in the browser through GitHub Pages and Pyodide; it does not require a backend service.

## Supported Version

Security fixes target the current `main` branch and the latest published release.

## Reporting a Vulnerability

If you find a vulnerability, avoid posting sensitive details in a public issue. Open a private security advisory on GitHub if available, or contact the repository owner through GitHub.

Include:

- affected URL or file path;
- steps to reproduce;
- browser or Python version;
- expected and actual behavior;
- any proof of impact.

## Privacy Notes

- Project generation runs locally in the browser or local Python process.
- QR scanning uses browser camera APIs locally.
- Camera frames are not uploaded by CardBoxGen.
- Share links and `CBG1:` project codes encode project parameters; do not share them publicly if dimensions or notes are sensitive.

## Fabrication Safety

Mechanical correctness issues are usually bugs, not security vulnerabilities. Report unsafe geometry, misleading validation, or exportable impossible designs through normal GitHub Issues unless there is a privacy or code-execution impact.
