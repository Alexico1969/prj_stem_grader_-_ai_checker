"""Compute subchapter rows and Totals without importing Tkinter or GUI code."""
import csv
import os
import re

WORKDIR = os.path.dirname(os.path.abspath(__file__))
GRADES_CSV = os.path.join(WORKDIR, 'grades.csv')


def normalize_name(name):
    return re.sub(r'\s+', ' ', name.strip().lower())


def load_rosters():
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


def get_student_section(name, rosters):
    if ',' in name:
        parts = name.split(', ')
        if len(parts) == 2:
            display = f"{parts[1]} {parts[0]}"
        else:
            display = name
    else:
        display = name
    for section, names in rosters.items():
        for n in names:
            if normalize_name(display) == normalize_name(n):
                return section
            display_parts = normalize_name(display).split()
            name_parts = normalize_name(n).split()
            if len(display_parts) >= 2 and len(name_parts) >= 2:
                if {display_parts[0], display_parts[-1]} == {name_parts[0], name_parts[-1]}:
                    return section
    return None


def main():
    if not os.path.exists(GRADES_CSV):
        print('grades.csv not found')
        return

    with open(GRADES_CSV, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
        try:
            next(reader)
        except StopIteration:
            pass
        assignments = header[5:]
        rows = list(reader)

    rosters = load_rosters()

    if not assignments:
        print('No assignments found')
        return

    prefixes = []
    for a in assignments:
        tok = a.strip().split()[0] if a.strip() else ''
        if tok and tok not in prefixes:
            prefixes.append(tok)

    prefix = prefixes[0]
    print('Using prefix:', prefix)
    matching = [a for a in assignments if a.strip().startswith(prefix)]
    print('Matching assignments count:', len(matching))

    sections = {k: {'submitted': [], 'not_submitted': []} for k in ['F2','F5','F6','Other']}

    for r in rows:
        if not r or not r[0].strip():
            continue
        student_name = r[0].strip()
        # build base name fields
        if ',' in student_name:
            parts = student_name.split(', ')
            last = parts[0].strip() if parts else ''
            first = parts[1].strip() if len(parts) > 1 else ''
        else:
            parts = student_name.split()
            first = parts[0].strip() if parts else ''
            last = parts[-1].strip() if len(parts) > 1 else ''
        base = [last, first]
        # collect grades
        grade_row = []
        any_sub = False
        # build index mapping: assignments start at column index 5
        for i, a in enumerate(assignments):
            col = i + 5
            val = ''
            if col < len(r):
                val = r[col].strip()
            if a in matching:
                if val:
                    try:
                        grade_val = float(val)
                        grade_row.append(grade_val)
                        any_sub = True
                    except Exception:
                        grade_row.append(val)
                        if val:
                            any_sub = True
                else:
                    grade_row.append('')
        full = base + grade_row
        # compute total
        total = 0.0
        for v in full[2:]:
            try:
                total += float(v)
            except Exception:
                pass
        full_with_total = full + [total]
        section = get_student_section(student_name, rosters) or 'Other'
        key = section if section in ['F2','F5','F6'] else 'Other'
        if any_sub:
            sections[key]['submitted'].append(full_with_total)
        else:
            sections[key]['not_submitted'].append(full_with_total)

    for k,v in sections.items():
        print('Section:', k)
        print(' Submitted:', len(v['submitted']))
        if v['submitted']:
            print('  Sample submitted row:', v['submitted'][0])
        print(' Not submitted:', len(v['not_submitted']))
        if v['not_submitted']:
            print('  Sample not-submitted row:', v['not_submitted'][0])
        print()

if __name__ == '__main__':
    main()
