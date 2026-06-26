#!/usr/bin/env python3
"""Check corpus metadata, structure, and obvious OCR/search-noise problems."""

from __future__ import annotations

import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEXTS = ROOT / "texts"
MAX_SAMPLES = 20

CONFIG = {
    "kant.nvim": {
        "required": ["Werk", "Abschnitt", "Akademie-Ausgabe", "Erstausgabe"],
        "search_terms": ["Vernunft", "Kritik"],
        "ocr_patterns": [
            ("margin-noise", r"\|[A-Za-z0-9^]+"),
            ("known-ocr-noise", r"\b(?:Yerstandes|JErscheinungen|UQ|Vv|Eecht|Eechts|Tats-ache|unmittelbai=)\b"),
            ("dotless-i", r"ı"),
        ],
    },
    "hegel.nvim": {
        "required": ["Werk", "Abschnitt", "TWA", "GW", "Erstausgabe"],
        "search_terms": ["Grundlinien", "Philosophie", "Recht"],
        "ocr_patterns": [
            ("page-header", r"^\s*(?:Hegel|He\s*grel|Hegrel)[,. ]+Rechtsphilosophie\b"),
            ("margin-noise", r"\|[A-Za-z0-9^]+"),
            ("long-s-leftover", r"ſ"),
            ("long-s-as-f", r"\b(?:fich|fie|ift|fo|felb\w*|feyn\w*|diefs|Dafs|dafs)\b"),
            ("known-ocr-noise", r"\b(?:Kritit|Philofophie|Philofoph\w*|Befireben|gegenmwärt\w*|Bewufst\w*|Aeuflerungen|Sy/te\w*|E/chen\w*)\b"),
            ("odd-glyph", r"[ı⸗]"),
        ],
    },
}


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def split_header(path: Path) -> tuple[dict[str, str], list[str], int, str | None]:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, lines, 1, "missing opening ---"

    for idx in range(1, min(len(lines), 100)):
        if lines[idx].strip() == "---":
            header: dict[str, str] = {}
            for line in lines[1:idx]:
                if ":" in line:
                    key, value = line.split(":", 1)
                    header[key.strip()] = value.strip()
            return header, lines[idx + 1 :], idx + 2, None

    return {}, lines, 1, "missing closing ---"


def check_metadata(files: list[Path], required: list[str]) -> list[str]:
    errors: list[str] = []
    for path in files:
        header, _, _, header_error = split_header(path)
        if header_error:
            errors.append(f"{rel(path)}: {header_error}")
            continue
        missing = [key for key in required if not header.get(key)]
        if missing:
            errors.append(f"{rel(path)}: missing metadata: {', '.join(missing)}")
    return errors


def count_header_noise(files: list[Path], terms: list[str]) -> dict[str, tuple[int, int]]:
    counts = {term: [0, 0] for term in terms}
    for path in files:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        in_header = bool(lines and lines[0].strip() == "---")
        for idx, line in enumerate(lines):
            if idx > 0 and in_header and line.strip() == "---":
                in_header = False
                continue
            for term in terms:
                if term in line:
                    counts[term][0 if in_header else 1] += 1
    return {term: (header, body) for term, (header, body) in counts.items()}


def find_ocr_warnings(files: list[Path], patterns: list[tuple[str, str]]) -> tuple[Counter[str], list[str]]:
    compiled = [(name, re.compile(pattern)) for name, pattern in patterns]
    counts: Counter[str] = Counter()
    samples: list[str] = []

    for path in files:
        _, body, body_start, _ = split_header(path)
        for offset, line in enumerate(body):
            for name, pattern in compiled:
                if pattern.search(line):
                    counts[name] += 1
                    if len(samples) < MAX_SAMPLES:
                        samples.append(f"{rel(path)}:{body_start + offset}: [{name}] {line[:160]}")
                    break
    return counts, samples


def check_kant_pages() -> list[str]:
    warnings: list[str] = []
    for work_dir in sorted(p for p in TEXTS.iterdir() if p.is_dir()):
        numbers = []
        for path in work_dir.glob("seite-*.txt"):
            match = re.fullmatch(r"seite-(\d+)\.txt", path.name)
            if match:
                numbers.append(int(match.group(1)))
        if not numbers:
            continue
        gaps = [n for n in range(min(numbers), max(numbers) + 1) if n not in numbers]
        if gaps:
            shown = ", ".join(str(n) for n in gaps[:12])
            if len(gaps) > 12:
                shown += ", ..."
            warnings.append(f"{rel(work_dir)}: page gaps in {min(numbers)}-{max(numbers)}: {shown}")
    return warnings


def check_hegel_paragraphs() -> list[str]:
    errors: list[str] = []
    gpr = TEXTS / "1821-grundlinien-der-philosophie-des-rechts"
    if not gpr.is_dir():
        return [f"{rel(gpr)}: missing directory"]

    if not (gpr / "000-vorrede.txt").is_file():
        errors.append(f"{rel(gpr / '000-vorrede.txt')}: missing Vorrede")

    seen: defaultdict[int, list[Path]] = defaultdict(list)
    for path in sorted(gpr.glob("*-par-*.txt")):
        match = re.fullmatch(r"(\d{3})-par-(\d{3})\.txt", path.name)
        if not match:
            errors.append(f"{rel(path)}: unexpected paragraph filename")
            continue

        left, right = (int(match.group(1)), int(match.group(2)))
        if left != right:
            errors.append(f"{rel(path)}: filename numbers differ")
        seen[left].append(path)

        header, _, _, header_error = split_header(path)
        if header_error:
            continue
        expected = f"§ {left}"
        if header.get("Paragraph") != expected:
            errors.append(f"{rel(path)}: Paragraph metadata is {header.get('Paragraph')!r}, expected {expected!r}")

    missing = [n for n in range(1, 361) if n not in seen]
    if missing:
        errors.append(f"{rel(gpr)}: missing paragraphs: {missing}")

    duplicates = {n: paths for n, paths in seen.items() if len(paths) > 1}
    for number, paths in sorted(duplicates.items()):
        errors.append(f"{rel(gpr)}: duplicate § {number}: {', '.join(rel(p) for p in paths)}")

    return errors


def main() -> int:
    config = CONFIG.get(ROOT.name)
    if config is None:
        print(f"Unknown repo name: {ROOT.name}", file=sys.stderr)
        return 2
    if not TEXTS.is_dir():
        print(f"Missing text directory: {TEXTS}", file=sys.stderr)
        return 2

    files = sorted(TEXTS.rglob("*.txt"))
    errors = check_metadata(files, config["required"])
    warnings = check_kant_pages() if ROOT.name == "kant.nvim" else []
    errors.extend(check_hegel_paragraphs() if ROOT.name == "hegel.nvim" else [])
    header_noise = count_header_noise(files, config["search_terms"])
    ocr_counts, ocr_samples = find_ocr_warnings(files, config["ocr_patterns"])

    print(f"Corpus: {ROOT.name}")
    print(f"Text files: {len(files)}")

    if header_noise:
        print("\nHeader search noise:")
        for term, (header, body) in header_noise.items():
            print(f"  {term}: {header} header hits, {body} body hits")

    if warnings:
        print("\nWarnings:")
        for warning in warnings:
            print(f"  - {warning}")

    if ocr_counts:
        print("\nSuspicious OCR patterns:")
        for name, count in sorted(ocr_counts.items()):
            print(f"  {name}: {count}")
        print("\nSamples:")
        for sample in ocr_samples:
            print(f"  - {sample}")

    if errors:
        print("\nErrors:")
        for error in errors:
            print(f"  - {error}")
        return 1

    print("\nOK: no structural errors.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
