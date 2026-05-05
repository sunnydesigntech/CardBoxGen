import json
import subprocess
import sys

from cardboxgen.api import generate_svg
from cardboxgen.validation import validate_template_params


def test_invalid_dimensions_are_blocking_and_non_exportable():
    result = generate_svg("tray_open_front", {"inner_w": 12, "inner_d": 12, "inner_h": 8, "thickness": 3, "kerf": 0.2, "fit_clearance": 0.15})
    assert result["meta"]["exportable"] is False
    assert any(w["severity"] == "error" for w in result["warnings"])
    assert 'id="DIAGNOSTIC"' in result["svg"]
    assert 'id="CUT"' not in result["svg"]


def test_validate_template_params_returns_computed_limits():
    validation = validate_template_params("box_with_lid", {"inner_w": 135, "inner_d": 90, "inner_h": 80, "thickness": 3, "kerf": 0.2, "fit_clearance": 0.4})
    assert not validation.blocking
    assert validation.computed_limits["burn_radius_mm"] == 0.1
    assert validation.computed_limits["lid_inner_w"] == 135 + 6 + 2 * 0.4


def test_unbalanced_kerf_clearance_combo_is_blocking():
    validation = validate_template_params("tray_open_front", {"inner_w": 80, "inner_d": 60, "inner_h": 50, "thickness": 1, "kerf": 0.45, "fit_clearance": 0.0})
    assert validation.blocking
    assert any(message.code == "FIT_COMPENSATION_UNBALANCED" for message in validation.messages)


def test_cli_blocks_invalid_export_without_allow_flag(tmp_path):
    out = tmp_path / "bad.svg"
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "cardboxgen",
            "--preset",
            "tray_open_front",
            "--inner-width",
            "5",
            "--inner-depth",
            "5",
            "--inner-height",
            "5",
            "--out",
            str(out),
        ],
        text=True,
        capture_output=True,
    )
    assert proc.returncode != 0
    assert not out.exists()


def test_cli_validate_command_json_report(tmp_path):
    report = tmp_path / "report.json"
    proc = subprocess.run(
        [sys.executable, "-m", "cardboxgen", "validate", "--preset", "tray_open_front", "--inner-width", "5", "--json-report", str(report)],
        text=True,
        capture_output=True,
    )
    assert proc.returncode != 0
    data = json.loads(report.read_text())
    assert data["blocking"] is True
