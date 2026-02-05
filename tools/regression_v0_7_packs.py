#!/usr/bin/env python3

import argparse
import json
import sys
import zipfile
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from cardboxgen_v0_7_templates import generate_svg


ALLOWED_TEMPLATES = {
    "tray_open_front",
    "divider_rack",
    "window_front",
    "card_shoe",
    "candy_machine_rotary_layered",
}

EXPECTED_ZIP_FILES = {
    "cut.svg",
    "project_summary.md",
    "assembly_guide.md",
    "bom.md",
    "teacher_notes.md",
}


@dataclass
class Case:
    template_id: str
    params: Dict[str, Any]
    source_file: Path


def _read_case(path: Path) -> Case:
    data = json.loads(path.read_text(encoding="utf-8"))
    template_id = str(data.get("template_id", "")).strip()
    params = data.get("params")
    if template_id not in ALLOWED_TEMPLATES:
        raise ValueError(f"{path}: unknown or disallowed template_id: {template_id!r}")
    if not isinstance(params, dict):
        raise TypeError(f"{path}: params must be an object/dict")
    return Case(template_id=template_id, params=params, source_file=path)


def _iter_cases(params_dir: Path) -> List[Case]:
    if not params_dir.exists():
        raise FileNotFoundError(f"Params dir not found: {params_dir}")

    cases: List[Case] = []
    for p in sorted(params_dir.glob("*.json")):
        cases.append(_read_case(p))

    if not cases:
        raise FileNotFoundError(f"No *.json found in: {params_dir}")

    return cases


def _find_error_warnings(warnings: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for w in warnings or []:
        sev = str((w or {}).get("severity", "")).lower()
        if sev == "error":
            out.append(w)
    return out


def _build_project_summary_md(template_id: str, params: Dict[str, Any], warnings: List[Dict[str, Any]]) -> str:
    errors = _find_error_warnings(warnings)
    return (
        "# CardBoxGen Project Summary\n\n"
        f"Template: **{template_id}**\n\n"
        "## Generator params\n"
        "```json\n"
        + json.dumps(params, indent=2, sort_keys=True)
        + "\n```\n\n"
        + ("## Errors\n" + "\n".join([f"- {e.get('code')}: {e.get('message')}" for e in errors]) + "\n\n" if errors else "")
    )


def _build_stub_md(title: str, template_id: str) -> str:
    return f"# {title}\n\nTemplate: **{template_id}**\n"


def _validate_svg(svg: str, *, template_id: str) -> None:
    if not isinstance(svg, str) or not svg.strip():
        raise ValueError(f"{template_id}: empty svg")
    s = svg.lstrip()
    if "<svg" not in s[:5000]:
        raise ValueError(f"{template_id}: svg does not look like SVG")


def _write_zip(out_path: Path, *, svg: str, template_id: str, params: Dict[str, Any], warnings: List[Dict[str, Any]]) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("cut.svg", svg)
        z.writestr("project_summary.md", _build_project_summary_md(template_id, params, warnings))
        z.writestr("assembly_guide.md", _build_stub_md("Assembly Guide", template_id))
        z.writestr("bom.md", _build_stub_md("Bill of Materials", template_id))
        z.writestr("teacher_notes.md", _build_stub_md("Teacher Notes", template_id))

    with zipfile.ZipFile(out_path, "r") as z:
        names = set(z.namelist())
        if names != EXPECTED_ZIP_FILES:
            missing = sorted(EXPECTED_ZIP_FILES - names)
            extra = sorted(names - EXPECTED_ZIP_FILES)
            raise ValueError(
                f"{template_id}: zip contents mismatch. Missing={missing} Extra={extra} ({out_path})"
            )


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(description="Generate and validate v0.7 regression project packs (ZIP) per template.")
    ap.add_argument(
        "--params-dir",
        default="examples/regression_v0_7_params",
        help="Directory containing *.json files with {template_id, params} (default: %(default)s)",
    )
    ap.add_argument(
        "--out-dir",
        default="artifacts/regression_v0_7",
        help="Output directory for generated ZIPs (default: %(default)s)",
    )
    ap.add_argument(
        "--date",
        default=None,
        help="Override date (YYYYMMDD) for deterministic filenames; default is today.",
    )
    args = ap.parse_args(argv)

    params_dir = Path(args.params_dir)
    out_dir = Path(args.out_dir)

    if args.date:
        ymd = str(args.date).strip()
        if not (len(ymd) == 8 and ymd.isdigit()):
            raise ValueError("--date must be YYYYMMDD")
    else:
        ymd = date.today().strftime("%Y%m%d")

    cases = _iter_cases(params_dir)

    failures: List[Tuple[str, str]] = []
    for c in cases:
        try:
            res = generate_svg(c.template_id, c.params)
            if not isinstance(res, dict):
                raise TypeError("generate_svg returned non-dict")
            svg = res.get("svg")
            warnings = res.get("warnings") or []

            _validate_svg(svg, template_id=c.template_id)

            errors = _find_error_warnings(warnings)
            if errors:
                raise ValueError(f"Blocking errors returned: {errors}")

            zip_name = f"CardBoxGen_{c.template_id}_{ymd}.zip"
            out_path = out_dir / zip_name
            _write_zip(out_path, svg=svg, template_id=c.template_id, params=c.params, warnings=warnings)

            print(f"OK  {c.template_id} -> {out_path}")
        except Exception as e:
            failures.append((c.template_id, str(e)))
            print(f"FAIL {c.template_id}: {e}", file=sys.stderr)

    if failures:
        print("\nFailures:", file=sys.stderr)
        for tid, msg in failures:
            print(f"- {tid}: {msg}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
