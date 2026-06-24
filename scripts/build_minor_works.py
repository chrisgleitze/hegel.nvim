#!/usr/bin/env python3
"""Build a few single-file Hegel texts from local source snapshots.

Expected local sources:
  /tmp/gw-glauben-3.html .. /tmp/gw-glauben-6.html
  /tmp/differenz-1801.txt
  /tmp/kritisches-journal-1802.txt
  /tmp/verfassung-1893.txt
"""

from __future__ import annotations

import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEXTS = ROOT / "texts"


def clean_ocr_noise(text: str) -> str:
    text = text.replace("\r", "")
    text = text.replace("\ufeff", "")
    text = re.sub(r"\n?Digitized by Google\s*\n?", "\n", text)
    text = re.sub(r"\n?Digilized by Google\s*\n?", "\n", text)
    text = re.sub(r"\n?Bayerische Staatsbibliothek.*\n?", "\n", text)
    text = re.sub(r"\n?StaatsBibliothek Digitale Bibliothek.*\n?", "\n", text)
    text = re.sub(r"\n?urn:nbn:[^\n]+\n?", "\n", text)
    text = re.sub(r"\n?Bamberg, Staatsbibliothek[^\n]*\n?", "\n", text)
    text = re.sub(r"\n[ \t]*[ivxlcdmIVXLCDM]+[ \t]+Vorrede[^\n]*\n", "\n", text)
    text = re.sub(r"\n[ \t]*\d+[ \t]+(?:Einleitung|Allgemeiner Theil|Vorrede)[^\n]*\n", "\n", text)
    text = re.sub(r"\n[ \t]*(?:Einleitung|Allgemeiner Theil|Vorwort|Vorrede)\.[ \t]+\d+[^\n]*\n", "\n", text)
    text = re.sub(r"\n[ \t]*\d+[ \t]+(?:©lauten|Glauben|Differenz|Die Reichs|Das Reich)[^\n]*\n", "\n", text)
    text = re.sub(r"\n[ \t]*(?:©lauten|Glauben|Differenz|Die Reichs|Das Reich)[^\n]*\d+[ \t]*\n", "\n", text)
    text = re.sub(r"\n[ \t]*\d+[ \t]*\n", "\n", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() + "\n"


def join_wrapped_lines(text: str) -> str:
    parts: list[str] = []
    for block in re.split(r"\n\s*\n", text):
        lines = [ln.strip() for ln in block.splitlines() if ln.strip()]
        if not lines:
            continue
        buf = lines[0]
        for line in lines[1:]:
            if buf.endswith("-"):
                buf = buf[:-1] + line
            elif re.match(r"^[a-zäöüß]", line):
                buf += " " + line
            elif re.match(r"^[,.;:!?)]", line):
                buf += line
            else:
                buf += " " + line
        parts.append(buf)
    return "\n\n".join(parts).strip() + "\n"


def extract_between(path: str, start: str, end: str) -> str:
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    s = text.find(start)
    if s < 0:
        raise RuntimeError(f"start marker not found in {path!r}: {start!r}")
    e = text.find(end, s)
    if e < 0:
        raise RuntimeError(f"end marker not found in {path!r}: {end!r}")
    return text[s:e]


def strip_tags(fragment: str) -> str:
    fragment = re.sub(r"<a [^>]*></a>", "", fragment)
    fragment = fragment.replace("<br />", "\n").replace("<br/>", "\n").replace("<br>", "\n")
    fragment = re.sub(r"</p>", "\n\n", fragment)
    fragment = re.sub(r"</h[1-6]>", "\n\n", fragment)
    fragment = re.sub(r"<p[^>]*>", "", fragment)
    fragment = re.sub(r"<h[1-6][^>]*>", "", fragment)
    fragment = re.sub(r"<span[^>]*>", "", fragment)
    fragment = fragment.replace("</span>", "")
    fragment = re.sub(r"<a name=\"page[^\"]*\"[^>]*></a>", "", fragment)
    fragment = re.sub(r"<[^>]+>", "", fragment)
    fragment = html.unescape(fragment)
    fragment = fragment.replace("\xa0", " ")
    fragment = re.sub(r"\n{3,}", "\n\n", fragment)
    return fragment.strip()


def extract_pg_chapter(path: str) -> str:
    raw = Path(path).read_text(encoding="utf-8", errors="replace")
    m = re.search(r'<div class="book-reader__chapter-content-wrapper">(.*?)</div>\s*</div>\s*</div>', raw, re.S)
    if not m:
        raise RuntimeError(f"chapter wrapper not found in {path}")
    text = strip_tags(m.group(1))
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def build_glauben() -> str:
    chapters = [
        extract_pg_chapter("/tmp/gw-glauben-3.html"),
        extract_pg_chapter("/tmp/gw-glauben-4.html"),
        extract_pg_chapter("/tmp/gw-glauben-5.html"),
        extract_pg_chapter("/tmp/gw-glauben-6.html"),
    ]
    text = "\n\n".join(chapters)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    text = text.split("Glauben und Wissen · Georg Wilhelm Friedrich Hegel", 1)[0].rstrip()
    return text + "\n"


def build_differenz() -> str:
    text = extract_between("/tmp/differenz-1801.txt", "Au den wenigen öffentlichen", "Verbefferungen in der Vorrede.")
    text = clean_ocr_noise(text)
    text = join_wrapped_lines(text)
    text = text.replace("Sy/tems", "Systems")
    text = text.replace("Sy/tem", "System")
    text = text.replace("Syftems", "Systems")
    text = text.replace("Syftem", "System")
    text = re.sub(r"\n[ivxıIVX ]+\s+Vorrede[^\n]*\n", "\n", text)
    text = re.sub(r"\n[ivxıIVX ]+\s+\d+\s*\n", "\n", text)
    return text


def build_wesen() -> str:
    text = extract_between(
        "/tmp/kritisches-journal-1802.txt",
        "Ueber das Wefen der philoſophiſchen Kritif über-",
        "Ein Geſpraͤch zwiſchen dem Verfaſſer und einem Freund.",
    )
    text = clean_ocr_noise(text)
    text = join_wrapped_lines(text)
    text = text.replace("Wefen", "Wesen")
    text = text.replace("Kritif", "Kritik")
    text = text.replace("Philofophie", "Philosophie")
    text = text.replace("philoſophiſchen", "philosophischen")
    return text


def build_verfassung() -> str:
    text = extract_between("/tmp/verfassung-1893.txt", "Einleitung.", "Anhang.")
    text = clean_ocr_noise(text)
    text = join_wrapped_lines(text)
    return text


def write_text(rel_dir: str, filename: str, metadata: dict[str, str], title: str, body: str) -> None:
    out_dir = TEXTS / rel_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / filename
    header = (
        "---\n"
        f"Werk: {metadata['Werk']}\n"
        f"Abschnitt: {metadata['Abschnitt']}\n"
        f"TWA: {metadata['TWA']}\n"
        f"GW: {metadata['GW']}\n"
        f"Erstausgabe: {metadata['Erstausgabe']}\n"
        "---\n\n"
    )
    out.write_text(header + title + "\n\n" + body.strip() + "\n", encoding="utf-8")


def main() -> None:
    write_text(
        "1802-glauben-und-wissen",
        "000-glauben-und-wissen.txt",
        {"Werk": "Glauben und Wissen", "Abschnitt": "Gesamttext", "TWA": "Bd. 2", "GW": "Bd. 4", "Erstausgabe": "1802"},
        "Glauben und Wissen",
        build_glauben(),
    )
    write_text(
        "1801-differenz-des-fichteschen-und-schellingschen-systems-der-philosophie",
        "000-differenz-des-fichteschen-und-schellingschen-systems-der-philosophie.txt",
        {"Werk": "Differenz des Fichteschen und Schellingschen Systems der Philosophie", "Abschnitt": "Gesamttext", "TWA": "Bd. 2", "GW": "Bd. 4", "Erstausgabe": "1801"},
        "Differenz des Fichteschen und Schellingschen Systems der Philosophie",
        build_differenz(),
    )
    write_text(
        "1802-ueber-das-wesen-der-philosophischen-kritik",
        "000-ueber-das-wesen-der-philosophischen-kritik.txt",
        {"Werk": "Über das Wesen der philosophischen Kritik überhaupt", "Abschnitt": "Gesamttext", "TWA": "Bd. 2", "GW": "Bd. 4", "Erstausgabe": "1802"},
        "Über das Wesen der philosophischen Kritik überhaupt",
        build_wesen(),
    )
    write_text(
        "1798-1802-die-verfassung-deutschlands",
        "000-die-verfassung-deutschlands.txt",
        {"Werk": "Die Verfassung Deutschlands", "Abschnitt": "Gesamttext", "TWA": "Bd. 1", "GW": "Bd. 5", "Erstausgabe": "1893 (verfasst 1798-1802)"},
        "Die Verfassung Deutschlands",
        build_verfassung(),
    )


if __name__ == "__main__":
    main()
