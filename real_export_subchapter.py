#!/usr/bin/env python3
"""
Run a real export of a sub-chapter to Google Sheets without launching the GUI.
Usage:
  python real_export_subchapter.py --subchapter 1.4
If --subchapter omitted, the script will print available prefixes and prompt you to type one.

It requires `credentials.json` in the repository (OAuth client) and will open a browser for the OAuth flow.
"""
import csv
import os
import argparse
import re
from google_sheets_integration import GoogleSheetsExporter

WORKDIR = os.path.dirname(os.path.abspath(__file__))
GRADES_CSV = os.path.join(WORKDIR, 'grades.csv')


def normalize_name(name):
    return re.sub(r'\s+', ' ', name.strip().lower())


def load_assignments():
    with open(GRADES_CSV, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
        next(reader)
        return header[5:]


def load_grades_data():
    grades_data = []
    with open(GRADES_CSV, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
        next(reader)
        assignments = header[5:]
        for row in reader:
            if row and row[0].strip():
                student_name = row[0].strip()
                student_id = row[1] if len(row) > 1 else ''
                grades = {}
                for i, a in enumerate(assignments):
                    if i + 5 < len(row):
                        v = row[i + 5].strip()
                        if v:
                            try:
                                grades[a] = float(v)
                            except ValueError:
                                grades[a] = v
                        else:
                            grades[a] = None
                grades_data.append({'name': student_name, 'id': student_id, 'grades': grades})
    return assignments, grades_data


def load_class_rosters():
    rosters = {'F2': [], 'F5': [], 'F6': []}
    for prefix in ['F2', 'F5', 'F6']:
        fn = os.path.join(WORKDIR, f'{prefix} - names.csv')
        if os.path.exists(fn):
            with open(fn, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    if row and row[0].strip() and row[0].lower() != 'name':
                        rosters[prefix].append(row[0].strip())
    return rosters


def get_student_section(student_name, rosters):
    # Convert Last, First to First Last
    if ',' in student_name:
        parts = student_name.split(', ')
        if len(parts) == 2:
            display_name = f"{parts[1]} {parts[0]}"
        else:
            display_name = student_name
    else:
        display_name = student_name

    for section, names in rosters.items():
        for name in names:
            if normalize_name(display_name) == normalize_name(name):
                return section
            display_parts = normalize_name(display_name).split()
            name_parts = normalize_name(name).split()
            if len(display_parts) >= 2 and len(name_parts) >= 2:
                display_first_last = {display_parts[0], display_parts[-1]}
                name_first_last = {name_parts[0], name_parts[-1]}
                if display_first_last == name_first_last:
                    return section
    return None


def main():
    parser = argparse.ArgumentParser(description='Export sub-chapter grades to Google Sheets')
    parser.add_argument('--subchapter', '-s', help='Sub-chapter prefix, e.g. 1.4')
    args = parser.parse_args()

    assignments, grades_data = load_grades_data()
    rosters = load_class_rosters()

    prefixes = []
    for a in assignments:
        tok = a.strip().split()[0] if a.strip() else ''
        if tok and tok not in prefixes:
            prefixes.append(tok)

    if not args.subchapter:
        print('Available sub-chapter prefixes:')
        print(', '.join(prefixes))
        selected = input('Enter sub-chapter (e.g. 1.4): ').strip()
    else:
        selected = args.subchapter.strip()

    if selected not in prefixes:
        print(f"Warning: {selected} not found in prefixes. Available: {', '.join(prefixes[:20])}")

    matching = [a for a in assignments if a.strip().startswith(selected)]
    if not matching:
        print('No matching assignments found for', selected)
        return

    # Build sections structure
    sections = {k: {'submitted': [], 'not_submitted': []} for k in ['F2', 'F5', 'F6', 'Other']}
    for student in grades_data:
        section = get_student_section(student['name'], rosters) or 'Other'
        if ',' in student['name']:
            parts = student['name'].split(', ')
            last = parts[0].strip() if parts else ''
            first = parts[1].strip() if len(parts) > 1 else ''
        else:
            parts = student['name'].split()
            first = parts[0].strip() if parts else ''
            last = parts[-1].strip() if len(parts) > 1 else ''
        base = [last, first]
        any_sub = False
        row_grades = []
        for a in matching:
            g = student['grades'].get(a)
            if g is not None:
                any_sub = True
                row_grades.append(g)
            else:
                row_grades.append('')
        full_row = base + row_grades
        key = section if section in ['F2', 'F5', 'F6'] else 'Other'
        if any_sub:
            sections[key]['submitted'].append(full_row)
        else:
            sections[key]['not_submitted'].append(full_row)

    # Export
    exporter = GoogleSheetsExporter()
    print('Authenticating and exporting. A browser window will open for OAuth; please complete the flow.')
    url = exporter.export_subchapter_to_sheets(selected, matching, sections)
    if url:
        print('Export complete. Google Sheet URL:')
        print(url)
    else:
        print('Export failed')


if __name__ == '__main__':
    main()
