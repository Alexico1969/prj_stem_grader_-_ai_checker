import tkinter as tk
from student_grades_app import StudentGradesApp

root = tk.Tk()
root.withdraw()
app = StudentGradesApp(root)
print('Assignments count:', len(app.assignments))
print('First 10 assignments:')
for a in app.assignments[:10]:
    print(' -', a)

# print prefixes
prefixes = []
for a in app.assignments:
    tok = a.strip().split()[0] if a.strip() else ''
    if tok and tok not in prefixes:
        prefixes.append(tok)
print('Prefixes count:', len(prefixes))
print(prefixes[:20])
