"""Quick debug script to compute and print subchapter rows including Total without calling Google APIs."""
import csv, os
from student_grades_app import StudentGradesApp
import tkinter as tk

root = tk.Tk()
root.withdraw()
app = StudentGradesApp(root)

# pick first subchapter prefix
if not app.assignments:
    print('No assignments')
    raise SystemExit(1)

first = app.assignments[0]
prefix = first.split()[0]
print('Using prefix:', prefix)
matching = [a for a in app.assignments if a.strip().startswith(prefix)]
print('Matching assignments count:', len(matching))

sections = {k: {'submitted': [], 'not_submitted': []} for k in ['F2','F5','F6','Other']}
for student in app.grades_data:
    section = app.get_student_section(student['name']) or 'Other'
    if ',' in student['name']:
        parts = student['name'].split(', ')
        last = parts[0].strip() if parts else ''
        firstn = parts[1].strip() if len(parts) > 1 else ''
    else:
        parts = student['name'].split()
        firstn = parts[0].strip() if parts else ''
        last = parts[-1].strip() if len(parts) > 1 else ''
    base = [last, firstn]
    any_sub = False
    row_grades = []
    for a in matching:
        g = student['grades'].get(a)
        if g is not None:
            any_sub = True
            row_grades.append(g)
        else:
            row_grades.append('')
    full = base + row_grades
    # compute total
    total = 0.0
    for v in full[2:]:
        try:
            total += float(v)
        except Exception:
            pass
    full_with_total = full + [total]
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
