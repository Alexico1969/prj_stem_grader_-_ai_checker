import tkinter as tk
from student_grades_app import StudentGradesApp

root = tk.Tk()
root.withdraw()
app = StudentGradesApp(root)

sample = "Export complete. Google Sheet URL:\nhttps://docs.google.com/spreadsheets/d/FAKE_ID\n\nLegend: blank cell = no submission"
app.display_result(sample)
print('Displayed sample result with URL tag. Please check the GUI window if visible.')
# keep the root for a short while to allow manual click test if someone runs this script interactively
root.after(2000, root.destroy)
root.mainloop()
