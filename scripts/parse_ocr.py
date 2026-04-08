#!/usr/bin/env python3
"""
Parse the OCR text of Hegel's Grundlinien der Philosophie des Rechts
from the Internet Archive (Lasson 1911 edition) and split it into
individual paragraph files.

Usage:
    python3 scripts/parse_ocr.py /tmp/hegel_rph_raw.txt texts/1821-grundlinien-der-philosophie-des-rechts/
"""

import re
import sys
import os


# --- OCR fixes: paragraph numbers that were misread by OCR ---
OCR_PAR_FIXES = {
    r'^§\s*IT\.\s*$': 17,
    r'^§\s*8L\s*[.\s]*$': 81,
    r'^§\s*lOL\s*[.\s]*$': 101,
    r'^§\s*29L\s*[.\s]*$': 291,
    r'^§\s*33L\s*[.\s]*$': 331,
    r'^§\s*857\s*[.\s]*$': 357,
}

# Known § split points: lines where a new § starts without a § marker
# because the OCR lost it or the § number only appeared in a page header.
# Key: the § number that currently absorbs this text.
# Value: (new_par_num, split_marker) — text starting with split_marker
# belongs to new_par_num.
MANUAL_SPLITS = {
    3: (4, "Der Boden des Rechts ist"),
    5: (6, "ß) Ebenso ist Ich"),
    7: (8, "Das weiter Bestimmte der Besonderung"),
    87: (88, "Im Vertrage erwerbe ich"),
}


def read_file(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.readlines()


def clean_line(line):
    """Remove common OCR artifacts from a single line."""
    # Remove page margin noise (|li, |O, |8, |^, etc.)
    line = re.sub(r'\|[a-zA-Z0-9^]+', '', line)
    # Remove stray semicolons with single letter at end of line
    line = re.sub(r'\s+;[a-zA-Z]$', '', line)
    # Remove "13*" style page count markers
    line = re.sub(r'^\d+\*\s*$', '', line)
    # Normalize multiple spaces to single
    line = re.sub(r'  +', ' ', line)
    return line.strip()


# Common OCR character-level errors and their corrections
OCR_TEXT_FIXES = [
    # Misread letters
    (r'Yerstandesbestimmung', 'Verstandesbestimmung'),
    (r'JErscheinungen', 'Erscheinungen'),
    (r'Tats-ache', 'Tatsache'),
    (r'ßollen', 'sollen'),
    (r'Eeichtum', 'Reichtum'),
    (r'Eeichtums', 'Reichtums'),
    (r'UQvermischt', 'unvermischt'),
    (r'Kan tischen', 'Kantischen'),
    (r'Verstandesj', 'Verstandes)'),
    (r"Vv'ille", 'Wille'),
    (r'unmittelbai=', 'unmittelbar'),
    (r'vTiöxQioig', 'ὑπόκρισις'),  # Greek word mangled by OCR
    (r'iictio', 'fictio'),  # Latin word mangled by OCR
    (r'Um-echt', 'Unrecht'),
    (r'AbBchnitt', 'Abschnitt'),
    (r'Da3', 'Das'),
    (r'AVillens', 'Willens'),
    (r'Absclmitt', 'Abschnitt'),
    (r'Eechtsphilosophie', 'Rechtsphilosophie'),
    (r'Eecht', 'Recht'),
    # Stray single characters from OCR margin noise
    (r' l man ', ' man '),
    (r' M\.$', '.'),
]


def clean_ocr_text(text):
    """Apply known OCR corrections to a line of text."""
    for pattern, replacement in OCR_TEXT_FIXES:
        text = re.sub(pattern, replacement, text)
    return text


def is_page_header(line):
    """Detect page headers (running heads/feet from printed book)."""
    stripped = line.strip()
    if not stripped:
        return False

    # "Hegel, Rechtsphilosophie. N" or "Hegel, Eechtsphilosophie. N"
    if re.match(r'^Hegel,\s*(R|E)echtsphilosophie', stripped):
        return True

    # Page number at start + section title: "28  Einleitung.    §  5."
    if re.match(r'^\d+[a-zA-Z]*\s+(Einleitung|Erster|Zweiter|Dritter|Vorrede)', stripped):
        return True

    # Section title + page number at end: "Einleitung.  §  6.  29"
    if re.match(r'^(Einleitung|Erster|Zweiter|Dritter)', stripped) and re.search(r'\d+\s*$', stripped):
        return True

    # "Das abstrakte Recht. ... §  41—43.  52" etc.
    if re.match(r'^(Das abstrakt|Die Moralit|Die Sittlich|Die Familie|Die bürgerlich|Der Staat|Das Unrecht|Das Eigen)', stripped) and re.search(r'\d+\s*$', stripped):
        return True

    # Lines that are just page numbers with section info on same line
    # e.g. "84     Erster  Teil.    Das  abstrakte  Recht.    Dritter  Abschnitt."
    if re.match(r'^\d+\s+(Erster|Zweiter|Dritter)', stripped):
        return True

    # "Dritter Teil. Die Sittlichkeit. Dritter Abschnitt." with or without number
    if re.match(r'^(Erster|Zweiter|Dritter)\s+Teil', stripped) and 'Abschnitt' in stripped:
        return True

    return False


def extract_par_from_header(line):
    """If a page header contains a single § number reference, return it."""
    stripped = line.strip()
    # Match "§  N." or "§  N," followed by a page number at end
    # e.g., "Einleitung.    §  4.  27" → 4
    m = re.search(r'§\s*(\d+)[.,]?\s+(\d+)\s*$', stripped)
    if m:
        par_num = int(m.group(1))
        page_num = int(m.group(2))
        # Heuristic: page numbers are roughly 20-280, § numbers 1-360
        # If second number looks like a page, first is a §
        if page_num < 300 and par_num <= 360:
            return par_num
    return None


def is_paragraph_start(line):
    """Detect a standalone § heading line like '§ 1.' or '§  142.'"""
    stripped = line.strip()

    # Check OCR misreadings first (before standard regex catches them wrong)
    for pattern, num in OCR_PAR_FIXES.items():
        if re.match(pattern, stripped):
            return num

    # Standard: "§ N." or "§ N" at start and end of line
    m = re.match(r'^§\s*(\d+)\s*[.\-,]?\s*[.\s]*$', stripped)
    if m:
        num = int(m.group(1))
        # Only accept valid paragraph numbers (1-360)
        if 1 <= num <= 360:
            return num

    return None


def is_footnote_start(line):
    """Detect start of a footnote."""
    stripped = line.strip()
    # "*) text..."  or "^) text..."  or "1) Author name..."
    if re.match(r'^[\*\^\>»]?\)\s', stripped):
        return True
    if re.match(r'^\d\)\s', stripped):
        return True
    # Footnote markers at start: "i)" or similar OCR artifacts
    if re.match(r'^[i!]\)\s', stripped):
        return True
    return False


def is_section_header(line):
    """Detect structural section headers (not page headers) like 'B. Betrug.' or 'C. Zwang und Verbrechen.'"""
    stripped = line.strip()
    if re.match(r'^[A-C]\.\s+[A-ZÄÖÜ]', stripped) and len(stripped) < 80:
        return True
    return False


def extract_paragraphs(lines, start_line):
    """Extract all paragraphs from the text starting at start_line."""
    paragraphs = {}
    current_par = None
    current_text = []
    in_footnote = False

    i = start_line
    while i < len(lines):
        line = lines[i].rstrip()
        i += 1

        # Check for standalone paragraph start (§ N.)
        par_num = is_paragraph_start(line)
        if par_num is not None:
            if current_par is not None:
                paragraphs[current_par] = current_text
            current_par = par_num
            current_text = []
            in_footnote = False
            continue

        # Skip page headers (running heads/feet from the printed book)
        if is_page_header(line):
            continue

        # Skip footnotes (they span until next blank line)
        if is_footnote_start(line):
            in_footnote = True
            continue
        if in_footnote:
            if line.strip() == '':
                in_footnote = False
            continue

        # Skip section sub-headers (A. Das Eigentum, B. Betrug, etc.)
        # These are structural markers, not paragraph content
        if is_section_header(line):
            continue

        # Blank lines: preserve as paragraph separators within a §
        if line.strip() == '':
            if current_par is not None and current_text and current_text[-1] != '':
                current_text.append('')
            continue

        # Regular content line
        if current_par is not None:
            cleaned = clean_line(line)
            if cleaned:
                current_text.append(cleaned)

    # Save last paragraph
    if current_par is not None:
        paragraphs[current_par] = current_text

    return paragraphs


def apply_manual_splits(paragraphs):
    """Split paragraphs where OCR lost the § marker entirely."""
    for absorbing_par, (new_par, split_marker) in MANUAL_SPLITS.items():
        if absorbing_par not in paragraphs:
            continue
        text = paragraphs[absorbing_par]
        split_idx = None
        for idx, line in enumerate(text):
            if line.startswith(split_marker):
                split_idx = idx
                break
        if split_idx is not None:
            # Everything before the split stays with the absorbing paragraph
            paragraphs[absorbing_par] = text[:split_idx]
            # Remove leading blank lines
            new_text = text[split_idx:]
            while new_text and new_text[0] == '':
                new_text.pop(0)
            paragraphs[new_par] = new_text
            print(f"  Split § {new_par} from § {absorbing_par}")


def join_broken_lines(text_lines):
    """Join lines that were broken by OCR page width."""
    result = []
    buffer = ''

    for line in text_lines:
        if line == '':
            if buffer:
                result.append(buffer)
                buffer = ''
            result.append('')
            continue

        if buffer:
            # If previous line ended with a hyphen, join without space
            if buffer.endswith('-'):
                # But keep hyphens that are part of compound words
                # If the next word starts lowercase, it's a broken word
                if line and line[0].islower():
                    buffer = buffer[:-1] + line
                else:
                    buffer = buffer + ' ' + line
            else:
                buffer = buffer + ' ' + line
        else:
            buffer = line

    if buffer:
        result.append(buffer)

    # Remove trailing empty lines
    while result and result[-1] == '':
        result.pop()
    # Remove leading empty lines
    while result and result[0] == '':
        result.pop(0)

    return result


def detect_anmerkung(text_lines):
    """Split paragraph text into main § text and Anmerkung.

    In Hegel's Rechtsphilosophie, each § consists of:
    1. The paragraph text (often a single dense sentence)
    2. An Anmerkung (remark) — Hegel's own elaboration

    The first text block (before the first blank line) is the § text.
    Everything after is the Anmerkung.
    """
    par_text = []
    anm_text = []
    first_block_done = False

    for line in text_lines:
        if line == '' and not first_block_done:
            first_block_done = True
            continue
        if first_block_done:
            anm_text.append(line)
        else:
            par_text.append(line)

    # Clean up Anmerkung
    while anm_text and anm_text[0] == '':
        anm_text.pop(0)
    while anm_text and anm_text[-1] == '':
        anm_text.pop()

    return par_text, anm_text


def get_section_name(par_num):
    """Return the section name for a given paragraph number."""
    if par_num <= 33:
        return "Einleitung"
    elif par_num <= 40:
        return "Erster Theil. Das abstracte Recht"
    elif par_num <= 71:
        return "Erster Theil. Das abstracte Recht — Erster Abschnitt. Das Eigentum"
    elif par_num <= 81:
        return "Erster Theil. Das abstracte Recht — Zweiter Abschnitt. Der Vertrag"
    elif par_num <= 104:
        return "Erster Theil. Das abstracte Recht — Dritter Abschnitt. Das Unrecht"
    elif par_num <= 114:
        return "Zweiter Theil. Die Moralität"
    elif par_num <= 118:
        return "Zweiter Theil. Die Moralität — Erster Abschnitt. Der Vorsatz und die Schuld"
    elif par_num <= 128:
        return "Zweiter Theil. Die Moralität — Zweiter Abschnitt. Die Absicht und das Wohl"
    elif par_num <= 141:
        return "Zweiter Theil. Die Moralität — Dritter Abschnitt. Das Gute und das Gewissen"
    elif par_num <= 157:
        return "Dritter Theil. Die Sittlichkeit"
    elif par_num <= 181:
        return "Dritter Theil. Die Sittlichkeit — Erster Abschnitt. Die Familie"
    elif par_num <= 256:
        return "Dritter Theil. Die Sittlichkeit — Zweiter Abschnitt. Die bürgerliche Gesellschaft"
    else:
        return "Dritter Theil. Die Sittlichkeit — Dritter Abschnitt. Der Staat"


def format_paragraph_file(par_num, par_text, anm_text, section_name):
    """Format a paragraph file with YAML metadata header."""
    header = f"""---
Werk: Grundlinien der Philosophie des Rechts
Paragraph: § {par_num}
Abschnitt: {section_name}
TWA: Bd. 7
GW: Bd. 14,1
Erstausgabe: 1821
---"""

    body = f"\n§ {par_num}\n\n"
    body += '\n'.join(par_text)

    if anm_text:
        body += '\n\nAnmerkung\n\n'
        body += '\n'.join(anm_text)

    return header + '\n' + body + '\n'


def main():
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <input_file> <output_dir>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_dir = sys.argv[2]

    os.makedirs(output_dir, exist_ok=True)

    lines = read_file(input_file)
    print(f"Read {len(lines)} lines from {input_file}")

    # Find the start of the actual text (§ 1)
    start_line = None
    for i, line in enumerate(lines):
        if re.match(r'^§\s*1[\.\-]?\s*$', line.strip()):
            if i > 5000:  # Past the Lasson introduction
                start_line = i
                break

    if start_line is None:
        print("ERROR: Could not find § 1 in the text!")
        sys.exit(1)

    print(f"Found § 1 at line {start_line + 1}")

    # Extract all paragraphs
    paragraphs = extract_paragraphs(lines, start_line)
    print(f"Extracted {len(paragraphs)} raw paragraphs")

    # Apply manual splits for paragraphs with missing § markers
    apply_manual_splits(paragraphs)
    print(f"After splits: {len(paragraphs)} paragraphs")

    # Report status
    found = sorted(paragraphs.keys())
    expected = list(range(1, 361))
    missing = [n for n in expected if n not in found]
    extra = [n for n in found if n not in expected]
    if missing:
        print(f"Missing paragraphs ({len(missing)}): {missing}")
    if extra:
        print(f"Extra paragraphs: {extra}")
    print(f"Coverage: {len(found)}/{len(expected)} paragraphs")

    # Write individual files
    written = 0
    for par_num in sorted(paragraphs.keys()):
        if par_num < 1 or par_num > 360:
            continue

        text_lines = paragraphs[par_num]
        joined = join_broken_lines(text_lines)
        # Apply OCR text corrections
        joined = [clean_ocr_text(line) for line in joined]
        par_text, anm_text = detect_anmerkung(joined)
        section = get_section_name(par_num)

        content = format_paragraph_file(par_num, par_text, anm_text, section)
        filename = f"{par_num:03d}-par-{par_num:03d}.txt"
        filepath = os.path.join(output_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        written += 1

    print(f"Wrote {written} paragraph files to {output_dir}")


if __name__ == '__main__':
    main()
