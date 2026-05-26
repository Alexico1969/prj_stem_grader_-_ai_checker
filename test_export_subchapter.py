from student_grades_app import StudentGradesApp
import tkinter as tk

# Create app but replace the real exporter with a fake one to avoid Google API calls
class FakeExporter:
    def export_subchapter_to_sheets(self, subchapter, assignments, sections_dict):
        print('Fake export called')
        print('Subchapter:', subchapter)
        print('Assignments:', assignments)
        for k,v in sections_dict.items():
            submitted = v.get('submitted', [])
            not_sub = v.get('not_submitted', [])
            print(f"{k} - Submitted: {len(submitted)}, Not submitted: {len(not_sub)}")
            if submitted:
                print(' Sample submitted row:', submitted[0])
            if not_sub:
                print(' Sample not-submitted row:', not_sub[0])
        return 'https://fake.sheet/url'

root = tk.Tk()
root.withdraw()
app = StudentGradesApp(root)
app.sheets_exporter = FakeExporter()

# Choose a subchapter that exists in the assignments e.g., take the prefix of the first matching assignment
if app.assignments:
    # find a subchapter like '1.1' from first assignment
    first = app.assignments[0]
    prefix = first.split()[0]
    print('Using subchapter prefix:', prefix)
    app.export_subchapter_to_sheets.__func__(app)  # but this opens the dialog, so instead call internal logic similar to that

    # We'll directly simulate what the method does by calling the same code here
    subchapter = prefix
    matching = [a for a in app.assignments if a.strip().startswith(subchapter)]
    sections = {k: {'submitted': [], 'not_submitted': []} for k in ['F2','F5','F6','Other']}
    for student in app.grades_data:
        section = app.get_student_section(student['name']) or 'Other'
        if ',' in student['name']:
            parts = student['name'].split(', ')
            last = parts[0].strip() if parts else ''
            first = parts[1].strip() if len(parts) > 1 else ''
        else:
            parts = student['name'].split()
            first = parts[0].strip() if parts else ''
            last = parts[-1].strip() if len(parts) > 1 else ''

        base = [last, first]
        any_submitted = False
        grade_row = []
        for a in matching:
            g = student['grades'].get(a)
            if g is not None:
                any_submitted = True
                grade_row.append(g)
            else:
                grade_row.append('')

        full_row = base + grade_row
        key = section if section in ['F2','F5','F6'] else 'Other'
        if any_submitted:
            sections[key]['submitted'].append(full_row)
        else:
            sections[key]['not_submitted'].append(full_row)

    fake_url = app.sheets_exporter.export_subchapter_to_sheets(subchapter, matching, sections)
    print('Returned URL:', fake_url)
else:
    print('No assignments found')
