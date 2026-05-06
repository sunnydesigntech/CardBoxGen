# Support

Use GitHub Issues for bugs, invalid geometry reports, documentation gaps, and feature requests.

Repository:

```text
https://github.com/sunnydesigntech/CardBoxGen
```

Live app:

```text
https://sunnydesigntech.github.io/CardBoxGen/
```

Direct launcher:

```text
https://sunnydesigntech.github.io/CardBoxGen/exec/
```

## Geometry Bug Reports

For generated parts that do not assemble, include:

- template id;
- all dimensions and units;
- material thickness measured with calipers;
- kerf value and how it was measured;
- clearance value;
- browser or CLI command used;
- generated SVG or project pack;
- photo or screenshot of the failed part, if available.

Important: not every dimension is physically valid. If CardBoxGen blocks export with a validation error, include that error code and the repair suggestion.

## Web App Reports

For web or camera/QR issues, include:

- browser name and version;
- operating system;
- whether the page is opened directly or inside an embedded app;
- whether the fallback Project Code import works;
- console error text if available.

Camera permission is controlled by the browser and operating system. CardBoxGen cannot force camera access; use Project Code import when QR scanning is blocked.

## Security or Privacy Reports

Use `SECURITY.md` for security-sensitive reports. Do not post private tokens, unreleased project files, or personal data in public issues.
