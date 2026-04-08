#!/usr/bin/env python3
"""Extract the Vorrede from the OCR text."""

import re
import sys

# Reuse OCR fixes from parse_ocr
OCR_TEXT_FIXES = [
    (r'Yerstandesbestimmung', 'Verstandesbestimmung'),
    (r'JErscheinungen', 'Erscheinungen'),
    (r'Tats-ache', 'Tatsache'),
    (r'ßollen', 'sollen'),
    (r'Eeichtum', 'Reichtum'),
    (r'Eeichtums', 'Reichtums'),
    (r'UQvermischt', 'unvermischt'),
    (r'Kan tischen', 'Kantischen'),
    (r"Vv'ille", 'Wille'),
    (r'unmittelbai=', 'unmittelbar'),
    (r'Um-echt', 'Unrecht'),
    (r'Eechtsphilosophie', 'Rechtsphilosophie'),
    (r'Eecht', 'Recht'),
    (r'b\'esondere', 'besondere'),
]


def is_page_header(line):
    stripped = line.strip()
    if not stripped:
        return False
    if re.match(r'^Hegel,\s*(R|E)echtsphilosophie', stripped):
        return True
    if re.match(r'^\d+\s+Vorrede', stripped):
        return True
    if re.match(r'^Vorrede\.\s+\d+\s*$', stripped):
        return True
    return False


def is_footnote_start(line):
    stripped = line.strip()
    if re.match(r'^[\*\^\>»]?\)\s', stripped):
        return True
    if re.match(r'^\d\)\s', stripped):
        return True
    return False


def main():
    input_file = sys.argv[1]
    output_file = sys.argv[2]

    with open(input_file, 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()

    # Find "Vorrede." heading
    start = None
    for i, line in enumerate(lines):
        if line.strip() == 'Vorrede.':
            if i > 4500:  # Past the table of contents
                start = i + 1
                break

    # Find § 1 (end of Vorrede)
    end = None
    for i, line in enumerate(lines):
        if re.match(r'^§\s*1[\.\-]?\s*$', line.strip()):
            if i > 5000:
                end = i
                break

    if start is None or end is None:
        print("Could not find Vorrede boundaries!")
        sys.exit(1)

    print(f"Vorrede: lines {start+1} to {end}")

    # Extract and clean
    text_lines = []
    in_footnote = False
    for i in range(start, end):
        line = lines[i].rstrip()

        if is_page_header(line):
            continue
        if is_footnote_start(line):
            in_footnote = True
            continue
        if in_footnote:
            if line.strip() == '':
                in_footnote = False
            continue

        # Clean OCR artifacts
        cleaned = re.sub(r'\|[a-zA-Z0-9^]+', '', line)
        cleaned = re.sub(r'  +', ' ', cleaned).strip()

        if cleaned:
            text_lines.append(cleaned)
        elif text_lines and text_lines[-1] != '':
            text_lines.append('')

    # Join broken lines
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
            if buffer.endswith('-') and line and line[0].islower():
                buffer = buffer[:-1] + line
            else:
                buffer = buffer + ' ' + line
        else:
            buffer = line
    if buffer:
        result.append(buffer)

    # Remove trailing blank lines
    while result and result[-1] == '':
        result.pop()

    # Apply OCR text fixes
    cleaned_result = []
    for line in result:
        for pattern, replacement in OCR_TEXT_FIXES:
            line = re.sub(pattern, replacement, line)
        cleaned_result.append(line)

    # Write output
    header = """---
Werk: Grundlinien der Philosophie des Rechts
Abschnitt: Vorrede
TWA: Bd. 7, S. 11-28
GW: Bd. 14,1, S. 3-17
Erstausgabe: 1821
---
"""
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(header)
        f.write('\n'.join(cleaned_result))
        f.write('\n')

    print(f"Wrote Vorrede to {output_file}")


if __name__ == '__main__':
    main()
