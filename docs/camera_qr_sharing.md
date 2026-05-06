# Camera, QR, and Project Codes

CardBoxGen is a static GitHub Pages app. It can request browser camera access for QR scanning, but it cannot force camera permission. The browser, operating system, and embedding app decide whether the camera is available.

## What Works Reliably

Use one of these handoff methods:

- Copy share link: copies a URL with the current project in the `cfg` query parameter.
- Copy project code: copies a `CBG1:` code containing the same project data.
- Import code: accepts either a full share link or the `CBG1:` project code.
- Scan QR: optional convenience path when the browser allows camera access and supports QR decoding.

The project code path does not need camera, cookies, account login, or a backend.

## Why Camera Can Be Blocked

Camera access can fail when:

- the page is opened inside an embedded browser that does not expose camera permissions;
- the browser setting for this site is set to Block;
- the operating system camera permission is disabled for the browser;
- the page is not running on HTTPS or localhost;
- the browser supports camera video but does not support QR decoding through `BarcodeDetector`.

CardBoxGen now detects those cases and shows a fallback message instead of leaving the user stuck.

## Recommended Student Workflow

1. Open the live app directly in Safari or Chrome:
   <https://sunnydesigntech.github.io/CardBoxGen/>
2. If using an execution or classroom launcher, open:
   <https://sunnydesigntech.github.io/CardBoxGen/exec/>
3. If camera scanning is blocked, use Copy project code on the sending device.
4. Paste the code into Project / location code on the receiving device.
5. Press Import code.

## Permission Reset

If QR scanning should work but the browser says camera is blocked:

- Safari: open site settings for the page and set Camera to Allow or Ask.
- Chrome: click the site settings icon in the address bar, set Camera to Allow, then reload.
- iOS/iPadOS: check Settings -> Safari or Settings -> Chrome and allow camera access.
- macOS: check System Settings -> Privacy & Security -> Camera.

After changing permission, reload the page and press Scan QR again.

## Privacy

QR scanning runs locally in the browser. CardBoxGen does not upload camera frames. The app only reads the QR text after the browser decodes it.
