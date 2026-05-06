# Camera, QR, and Project Codes

CardBoxGen can request camera access for QR scanning, but it cannot force camera permission. Camera permission is controlled by the browser, operating system, and any embedded app hosting the page.

## Reliable Fallbacks

Use the Project handoff panel:

- Copy share link: copies a URL containing the current project in `cfg=...`.
- Copy project code: copies a pasteable `CBG1:` project/location code.
- Import code: accepts either a full share link or a `CBG1:` code.
- Scan QR: optional, only when the browser grants camera permission and supports QR decoding.

The project code path is the most reliable method. It does not require camera access, login, cookies, or a backend.

## If Camera Is Blocked

Use this sequence:

1. Open the app directly in Safari or Chrome: https://sunnydesigntech.github.io/CardBoxGen/
2. If a launcher or embedded browser is involved, open: https://sunnydesigntech.github.io/CardBoxGen/exec/
3. If QR still does not work, press Copy project code on the sending device.
4. Paste the code into Project / location code on the receiving device.
5. Press Import code.

## Common Causes

- The page is opened inside an embedded browser without camera support.
- Site camera permission is set to Block.
- Operating system camera permission is disabled for the browser.
- The page is not running on HTTPS or localhost.
- The browser supports camera video but not QR decoding through `BarcodeDetector`.

## Privacy

QR scanning runs locally in the browser. CardBoxGen does not upload camera frames. Only decoded QR text is used to import a project.
