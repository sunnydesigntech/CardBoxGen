import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from cardboxgen.api import generate_svg
from cardboxgen.version import __version__


def test_api_result_is_json_safe_and_contains_bundle_files():
    result = generate_svg("tray_open_front", {"inner_w": 135, "inner_d": 90, "inner_h": 80, "thickness": 3})
    json.dumps(result)
    assert result["svg"].startswith("<?xml")
    assert {"project_summary.md", "assembly_guide.md", "bom.md", "metadata.json", "params.json"} <= set(result["bundle_files"])
    assert result["meta"]["template_id"] == "tray_open_front"


def test_legacy_alias_returns_deprecation_warning():
    result = generate_svg("card_shoe_front_draw", {"card_w": 63, "card_h": 88, "card_t": 0.35, "capacity": 20})
    assert result["meta"]["template_id"] == "card_shoe"
    assert any(w["code"] == "TEMPLATE_ALIAS" for w in result["warnings"])


def test_cli_smoke_module_and_wrapper(tmp_path):
    root = Path(__file__).resolve().parents[1]
    presets = [
        "tray_open_front",
        "dispenser_slot_front",
        "window_front",
        "box_with_lid",
        "divider_rack",
        "card_shoe",
        "candy_machine_rotary_layered",
    ]
    for preset in presets:
        out = tmp_path / f"{preset}.svg"
        cmd = [
            sys.executable,
            "-m",
            "cardboxgen",
            "--preset",
            preset,
            "--inner-width",
            "135",
            "--inner-depth",
            "90",
            "--inner-height",
            "80",
            "--thickness",
            "3",
            "--kerf",
            "0.2",
            "--clearance",
            "0.15",
            "--out",
            str(out),
        ]
        subprocess.run(cmd, check=True, cwd=root)
        ET.parse(out)

    out2 = tmp_path / "calibration.svg"
    subprocess.run([sys.executable, "cardboxgen_v0_1.py", "--calibration", "--thickness", "3", "--kerf", "0.2", "--out", str(out2)], check=True, cwd=root)
    ET.parse(out2)


def test_examples_script_generates_all_supported_examples(tmp_path):
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root / "examples"))
    from generate_examples import generate

    generate(str(tmp_path))
    expected = [
        "tray_open_front.svg",
        "dispenser_slot_front.svg",
        "window_front.svg",
        "box_with_lid.svg",
        "divider_rack.svg",
        "card_shoe.svg",
        "candy_machine_rotary_layered.svg",
        "calibration_mating_strips.svg",
        "invalid_dimension_report.json",
    ]
    for filename in expected[:-1]:
        ET.parse(tmp_path / filename)
    data = json.loads((tmp_path / "invalid_dimension_report.json").read_text())
    assert data["blocking"] is True


def test_docs_bundle_is_fresh():
    root = Path(__file__).resolve().parents[1]
    subprocess.run([sys.executable, "tools/sync_docs.py", "--check"], check=True, cwd=root)


def test_i18n_keys_and_versions_match():
    root = Path(__file__).resolve().parents[1]
    files = sorted((root / "docs" / "i18n").glob("*.json"))

    def flat(obj, prefix=""):
        if isinstance(obj, dict):
            out = set()
            for key, value in obj.items():
                out |= flat(value, f"{prefix}.{key}" if prefix else key)
            return out
        return {prefix}

    payloads = [json.loads(path.read_text(encoding="utf-8")) for path in files]
    key_sets = [flat(payload) for payload in payloads]
    assert all(keys == key_sets[0] for keys in key_sets)
    assert all(payload["app"]["version"] == f"v{__version__}" for payload in payloads)


def test_web_app_i18n_references_exist():
    root = Path(__file__).resolve().parents[1]
    payload = json.loads((root / "docs" / "i18n" / "en.json").read_text(encoding="utf-8"))

    def flat(obj, prefix=""):
        if isinstance(obj, dict):
            out = set()
            for key, value in obj.items():
                out |= flat(value, f"{prefix}.{key}" if prefix else key)
            return out
        return {prefix}

    keys = flat(payload)
    app_js = (root / "docs" / "app.js").read_text(encoding="utf-8")
    index_html = (root / "docs" / "index.html").read_text(encoding="utf-8")
    js_refs = {m.group(1) for m in re.finditer(r"(?<![\w.])t\(\s*[\"']([^\"']+)[\"']", app_js)}
    html_refs = set(re.findall(r'data-i18n(?:-placeholder)?="([^"]+)"', index_html))
    missing = sorted((js_refs | html_refs) - keys)
    assert missing == []


def test_web_app_version_matches_package():
    root = Path(__file__).resolve().parents[1]
    app_js = (root / "docs" / "app.js").read_text(encoding="utf-8")
    index_html = (root / "docs" / "index.html").read_text(encoding="utf-8")
    assert f'APP_VERSION = "{__version__}"' in app_js
    assert f"v{__version__}" in index_html


def test_web_app_loads_checked_pyodide_bundle():
    root = Path(__file__).resolve().parents[1]
    app_js = (root / "docs" / "app.js").read_text(encoding="utf-8")
    index_html = (root / "docs" / "index.html").read_text(encoding="utf-8")
    assert "cardboxgen_bundle.py" in app_js
    old_module = "cardboxgen_" + "v0_7_templates.py"
    assert old_module not in app_js
    for preset in [
        "tray_open_front",
        "dispenser_slot_front",
        "window_front",
        "box_with_lid",
        "divider_rack",
        "card_shoe",
        "candy_machine_rotary_layered",
        "calibration",
    ]:
        assert f'value="{preset}"' in index_html


def test_web_app_has_qr_camera_fallback_and_exec_entrypoint():
    root = Path(__file__).resolve().parents[1]
    app_js = (root / "docs" / "app.js").read_text(encoding="utf-8")
    index_html = (root / "docs" / "index.html").read_text(encoding="utf-8")
    docs_readme = (root / "docs" / "README.md").read_text(encoding="utf-8")
    assert 'id="copyShareLink"' in index_html
    assert 'id="projectCodeInput"' in index_html
    assert 'id="scanQr"' in index_html
    assert "navigator.mediaDevices.getUserMedia" in app_js
    assert "BarcodeDetector" in app_js
    assert "status.cameraBlocked" in app_js
    assert "CBG1:" in app_js
    assert (root / "docs" / "exec" / "index.html").exists()
    assert "camera_qr_sharing.md" in docs_readme
    assert (root / "docs" / "wiki" / "Home.md").exists()
    assert (root / "docs" / "wiki" / "Camera-QR-and-Project-Codes.md").exists()
