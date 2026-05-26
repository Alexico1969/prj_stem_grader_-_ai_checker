import csv
import re

workspace = r"e:\Dropbox\RePoS\_Molloy\Get_PRJSTEM_grades"

def normalize_name(name):
    return re.sub(r"\s+", " ", name.strip().lower())

# Load student names
student_names = {'F2': [], 'F5': [], 'F6': []}
for prefix in ['F2','F5','F6']:
    fn = workspace + f"\\{prefix} - names.csv"
    try:
        with open(fn, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if row and row[0].strip() and row[0].lower() != 'name':
                    student_names[prefix].append(row[0].strip())
    except FileNotFoundError:
        pass

# read grades
grades = []
assignments = []
with open(workspace + "\\grades.csv", 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    header = next(reader)
    next(reader)
    assignments = header[5:]
    for row in reader:
        if row and row[0].strip():
            student_name = row[0].strip()
            grades_map = {}
            for i, a in enumerate(assignments):
                if i+5 < len(row):
                    v = row[i+5].strip()
                    if v:
                        try:
                            grades_map[a] = float(v)
                        except:
                            grades_map[a] = v
                    else:
                        grades_map[a] = None
            grades.append({'name': student_name, 'grades': grades_map})

# replicate get_student_section

def get_student_section(student_name):
    # convert Last, First to First Last
    if ',' in student_name:
        parts = student_name.split(', ')
        if len(parts) == 2:
            display_name = f"{parts[1]} {parts[0]}"
        else:
            display_name = student_name
    else:
        display_name = student_name

    for section, names in student_names.items():
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

# find students with grades but no section mapping for at least one assignment
unmatched = set()
for s in grades:
    for a, g in s['grades'].items():
        if g is not None:
            sec = get_student_section(s['name'])
            if sec is None:
                unmatched.add(s['name'])
                break

print('Students with grades but no matched section (sample):')
for name in sorted(unmatched)[:200]:
    print(name)

# specifically check the three names
for target in ["Allocco, Sophia", "Deng, Victoria", "Wilson, Ravi"]:
    sec = None
    for s in grades:
        if s['name'] == target:
            sec = get_student_section(s['name'])
            break
    print(f"{target} -> section: {sec}")

# Also show if those three ever had a non-None grade in any assignment
for target in ["Allocco, Sophia", "Deng, Victoria", "Wilson, Ravi"]:
    found = False
    for s in grades:
        if s['name'] == target:
            for a,g in s['grades'].items():
                if g is not None:
                    print(f"{target} has grade for assignment: {a} -> {g}")
                    found = True
                    break
            if not found:
                print(f"{target} has NO grades in any assignment (all None)")
            break

# list where these three might have been categorized for one assignment sample (first assignment)
sample_a = assignments[0] if assignments else None
print('\nSample assignment:', sample_a)
for s in grades:
    if s['name'] in ["Allocco, Sophia", "Deng, Victoria", "Wilson, Ravi"]:
        g = s['grades'].get(sample_a)
        print(s['name'], 'grade->', g, 'section->', get_student_section(s['name']))
