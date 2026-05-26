# Student Grades Management App

A tkinter application to manage and view student grades from Project Stem and class lists.

## Features

The app provides three main menu options:

### 1. Find Grade for Specific Student and Assignment
- Select a student from a dropdown list
- Select an assignment from a dropdown list
- View the specific grade for that student and assignment
- Shows student ID and grade information

### 2. Find All Grades for a Specific Student
- Select a student from a dropdown list
- View all grades organized by category:
  - Lesson Practice
  - Code Practice
  - Assignments
  - Quizzes
  - Tests
  - Other
- Shows total completed assignments
- Displays grades in an organized, easy-to-read format

### 3. Find All Grades for a Specific Assignment
- Select an assignment from a dropdown list
- View all students who have submitted that assignment
- Grades are sorted from highest to lowest
- Shows statistics including:
  - Average grade
  - Highest grade
  - Lowest grade
  - Total number of submissions

## How to Use

1. **Run the application:**
   ```bash
   python student_grades_app.py
   ```

2. **Make sure these files are in the same directory:**
   - `2025-09-13T1722_Grades-(7fac90)_CS_Python_Fundamentals.csv`
   - `F2 - names.csv`
   - `F5 - names.csv`
   - `F6 - names.csv`

3. **Use the menu buttons:**
   - Click any of the three menu options
   - Use the dropdown menus to select students/assignments
   - View results in the results area

## Features

- **Flexible Name Matching:** Handles name variations between your class lists and Project Stem data
- **Organized Display:** Grades are categorized and sorted for easy viewing
- **Statistics:** Provides useful statistics for assignments
- **Error Handling:** Gracefully handles missing files and data issues
- **User-Friendly Interface:** Clean, intuitive interface with dropdown selections

## Data Sources

- **Grades Data:** Loaded from the Project Stem CSV file
- **Student Names:** Loaded from F2, F5, F6 name files
- **Automatic Matching:** Uses the same flexible matching logic from the analysis script

## Requirements

- Python 3.x
- tkinter (usually included with Python)
- CSV files in the same directory as the script

## Notes

- The app automatically excludes test users (like Harry Champagnat)
- Names are matched flexibly to handle variations between files
- All data is loaded when the app starts
- Results are displayed in a scrollable text area
