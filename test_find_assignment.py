from student_grades_app import StudentGradesApp
import tkinter as tk

root = tk.Tk()
root.withdraw()
app = StudentGradesApp(root)

# Pick an assignment that earlier showed missing students - use the second assignment in list
assignment = app.assignments[0] if app.assignments else None
print('Testing assignment:', assignment)

# Call the method that generates the result (adapted - we can call find_assignment_grades's internal code by copying)
result = ''
# We'll simulate the relevant part by reusing app.find_assignment_grades logic in a minimal way
f2_grades = []
f5_grades = []
f6_grades = []
other_grades = []
for student in app.grades_data:
    grade = student['grades'].get(assignment)
    section = app.get_student_section(student['name'])
    display_grade = grade if grade is not None else ''
    if section == 'F2':
        f2_grades.append((student['name'], display_grade))
    elif section == 'F5':
        f5_grades.append((student['name'], display_grade))
    elif section == 'F6':
        f6_grades.append((student['name'], display_grade))
    else:
        other_grades.append((student['name'], display_grade))

print('F6 students count:', len(f6_grades))
for n,g in sorted(f6_grades, key=lambda x: app.get_last_name(x[0])):
    print(app.format_csv_name(n,g))
