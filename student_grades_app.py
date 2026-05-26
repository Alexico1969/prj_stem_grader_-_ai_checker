#!/usr/bin/env python3
"""
Student Grades Management App
A tkinter application to manage and view student grades from Project Stem and class lists.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import csv
import glob
import json
import os
import re
from collections import defaultdict
from google_sheets_integration import GoogleSheetsExporter

class StudentGradesApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Grade Manager — Project STEM")
        w, h = 1140, 740
        x = max(0, (self.root.winfo_screenwidth()  - w) // 2)
        y = max(0, (self.root.winfo_screenheight() - h) // 2)
        self.root.geometry(f"{w}x{h}+{x}+{y}")
        self.root.minsize(900, 600)
        
        # Data storage
        self.grades_data = []
        self.student_names = {}
        self.assignments = []
        self.students = []
        self.all_sections = []
        self.active_sections = []
        self.points_possible = {}
        
        # Google Sheets integration
        self.sheets_exporter = GoogleSheetsExporter()
        
        # Create main interface
        self.create_widgets()
        
        # Load data
        self.load_data()
    
    def create_widgets(self):
        C = {
            'sidebar':      '#1e293b',
            'sidebar_head': '#0f172a',
            'btn_nav':      '#334155',
            'btn_nav_hov':  '#475569',
            'btn_cfg':      '#3b82f6',
            'btn_cfg_hov':  '#2563eb',
            'btn_exp':      '#059669',
            'btn_exp_hov':  '#047857',
            'main_bg':      '#f8fafc',
            'card_bg':      '#ffffff',
            'card_border':  '#e2e8f0',
            'text_main':    '#1e293b',
            'text_muted':   '#64748b',
            'text_sidebar': '#f1f5f9',
            'text_dim':     '#94a3b8',
            'status_bg':    '#1e293b',
            'status_fg':    '#94a3b8',
            'divider':      '#334155',
            'select_bg':    '#3b82f6',
        }

        self.root.configure(bg=C['main_bg'])

        # Status bar — pack first so it anchors at the very bottom
        self.status_var = tk.StringVar(value="Loading...")
        tk.Label(
            self.root, textvariable=self.status_var,
            bg=C['status_bg'], fg=C['status_fg'],
            font=('Segoe UI', 9), anchor=tk.W, padx=16, pady=6
        ).pack(side=tk.BOTTOM, fill=tk.X)

        # ── Sidebar ──────────────────────────────────────────────────
        sidebar = tk.Frame(self.root, bg=C['sidebar'], width=270)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)

        # App title block
        hdr = tk.Frame(sidebar, bg=C['sidebar_head'])
        hdr.pack(fill=tk.X)
        tk.Label(
            hdr, text="Grade Manager",
            bg=C['sidebar_head'], fg=C['text_sidebar'],
            font=('Segoe UI', 15, 'bold'), anchor=tk.W
        ).pack(fill=tk.X, padx=18, pady=(18, 2))
        tk.Label(
            hdr, text="Project STEM",
            bg=C['sidebar_head'], fg=C['text_dim'],
            font=('Segoe UI', 9), anchor=tk.W
        ).pack(fill=tk.X, padx=18, pady=(0, 16))

        tk.Frame(sidebar, bg=C['divider'], height=1).pack(fill=tk.X)

        def sidebar_btn(text, cmd, bg, hov):
            btn = tk.Button(
                sidebar, text=text, command=cmd,
                bg=bg, fg='#ffffff',
                activebackground=hov, activeforeground='#ffffff',
                font=('Segoe UI', 10), relief=tk.FLAT, bd=0,
                padx=18, pady=11, anchor=tk.W,
                cursor='hand2', wraplength=225, justify=tk.LEFT
            )
            btn.pack(fill=tk.X, padx=8, pady=2)
            btn.bind('<Enter>', lambda e, b=btn, c=hov: b.config(bg=c))
            btn.bind('<Leave>', lambda e, b=btn, c=bg:  b.config(bg=c))
            return btn

        def section_label(text):
            tk.Label(
                sidebar, text=text,
                bg=C['sidebar'], fg=C['text_dim'],
                font=('Segoe UI', 8, 'bold'), anchor=tk.W
            ).pack(fill=tk.X, padx=20, pady=(12, 2))

        section_label("SETTINGS")
        sidebar_btn("Select Active Classes",
                    self.select_active_classes, C['btn_cfg'], C['btn_cfg_hov'])

        tk.Frame(sidebar, bg=C['divider'], height=1).pack(fill=tk.X, padx=12, pady=(12, 0))

        section_label("QUERY")
        sidebar_btn("Find Grade — Student & Assignment",
                    self.find_specific_grade,    C['btn_nav'], C['btn_nav_hov'])
        sidebar_btn("All Grades for a Student",
                    self.find_student_grades,    C['btn_nav'], C['btn_nav_hov'])
        sidebar_btn("All Grades for an Assignment",
                    self.find_assignment_grades, C['btn_nav'], C['btn_nav_hov'])

        tk.Frame(sidebar, bg=C['divider'], height=1).pack(fill=tk.X, padx=12, pady=(12, 0))

        section_label("EXPORT")
        sidebar_btn("Export Assignment → Google Sheets",
                    self.export_to_google_sheets,      C['btn_exp'], C['btn_exp_hov'])
        sidebar_btn("Export Sub-chapter → Google Sheets",
                    self.export_subchapter_to_sheets,  C['btn_exp'], C['btn_exp_hov'])

        # ── Main content area ─────────────────────────────────────────
        main = tk.Frame(self.root, bg=C['main_bg'])
        main.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        tk.Label(
            main, text="Output",
            bg=C['main_bg'], fg=C['text_muted'],
            font=('Segoe UI', 11, 'bold'), anchor=tk.W
        ).pack(fill=tk.X, padx=22, pady=(18, 6))

        # 1-pixel card border via outer frame
        card_outer = tk.Frame(main, bg=C['card_border'])
        card_outer.pack(fill=tk.BOTH, expand=True, padx=18, pady=(0, 18))

        self.results_text = scrolledtext.ScrolledText(
            card_outer,
            bg=C['card_bg'], fg=C['text_main'],
            font=('Consolas', 10), relief=tk.FLAT, bd=0,
            padx=16, pady=14, wrap=tk.WORD,
            selectbackground=C['select_bg'], selectforeground='#ffffff',
            insertbackground=C['text_main']
        )
        self.results_text.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
    
    def load_data(self):
        """Load data from CSV files"""
        try:
            # Load grades data
            self.load_grades_data()
            
            # Load student names from F2, F5, F6
            self.load_student_names()
            
            # Extract assignments and students
            self.extract_assignments_and_students()
            
            sections_str = ', '.join(self.all_sections) if self.all_sections else 'none'
            self.status_var.set(f"Data loaded: {len(self.students)} students, {len(self.assignments)} assignments | Classes: {sections_str}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load data: {str(e)}")
            self.status_var.set("Error loading data")
    
    def load_grades_data(self):
        """Load grades data from the main CSV file"""
        try:
            with open('grades.csv', 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                
                header = next(reader)
                points_row = next(reader)

                # Store assignments (skip first 5 columns which are student info)
                self.assignments = header[5:]

                # Store max possible score per assignment
                self.points_possible = {}
                for i, assignment in enumerate(self.assignments):
                    if i + 5 < len(points_row):
                        val = points_row[i + 5].strip()
                        try:
                            self.points_possible[assignment] = float(val)
                        except ValueError:
                            self.points_possible[assignment] = None
                
                # Load student data
                for row_num, row in enumerate(reader, start=3):  # Start from row 3 (after header and points)
                    if row and row[0].strip():
                        # The CSV reader already handles quotes, so we don't need regex matching
                        student_name = row[0].strip()
                        student_id = row[1] if len(row) > 1 else ""
                        
                        # Store grades data
                        grades = {}
                        for i, assignment in enumerate(self.assignments):
                            if i + 5 < len(row):
                                grade_value = row[i + 5].strip()
                                if grade_value:
                                    try:
                                        grades[assignment] = float(grade_value)
                                    except ValueError:
                                        grades[assignment] = grade_value
                                else:
                                    grades[assignment] = None
                        
                        self.grades_data.append({
                            'name': student_name,
                            'id': student_id,
                            'grades': grades
                        })
                            
        except FileNotFoundError:
            raise Exception("Grades CSV file not found")
        except Exception as e:
            raise Exception(f"Error reading grades file: {str(e)}")
    
    def discover_class_files(self):
        """Find all '* - names.csv' and '* - names.txt' files in the current directory."""
        sections = {}
        for filepath in glob.glob('* - names.csv') + glob.glob('* - names.txt'):
            match = re.match(r'^(.+?)\s+-\s+names\.(csv|txt)$', os.path.basename(filepath), re.IGNORECASE)
            if match:
                section = match.group(1).strip()
                if section not in sections:
                    sections[section] = filepath
        return sections

    def load_student_names(self):
        """Load student names from all discovered class files."""
        class_files = self.discover_class_files()
        self.all_sections = sorted(class_files.keys())

        # Restore previously saved selection, falling back to all sections
        self.active_sections = list(self.all_sections)
        try:
            with open('active_classes.json', 'r') as f:
                saved = json.load(f)
            restored = [s for s in saved if s in self.all_sections]
            if restored:
                self.active_sections = restored
        except (FileNotFoundError, json.JSONDecodeError):
            pass

        self.student_names = {s: [] for s in self.all_sections}

        for section, filepath in class_files.items():
            try:
                with open(filepath, 'r', encoding='utf-8') as file:
                    reader = csv.reader(file)
                    for row in reader:
                        if row and row[0].strip() and row[0].lower() != 'name':
                            self.student_names[section].append(row[0].strip())
            except FileNotFoundError:
                print(f"Warning: {filepath} not found")
            except Exception as e:
                print(f"Warning: Error reading {filepath}: {str(e)}")

    def select_active_classes(self):
        """Open dialog to select which class sections are active."""
        if not self.all_sections:
            messagebox.showinfo("No Classes", "No class name files found.\nAdd files named like 'F2 - names.csv' to the app folder.")
            return
        dialog = ClassSelectionDialog(self.root, self.all_sections, self.active_sections)
        self.root.wait_window(dialog.dialog)
        if dialog.result is not None:
            self.active_sections = dialog.result
            try:
                with open('active_classes.json', 'w') as f:
                    json.dump(self.active_sections, f)
            except Exception:
                pass
            self.status_var.set(f"Active classes: {', '.join(self.active_sections)}")
    
    def extract_assignments_and_students(self):
        """Extract unique assignments and students"""
        self.students = []
        for student in self.grades_data:
            # Convert "Last, First" format to "First Last" for display
            if ',' in student['name']:
                parts = student['name'].split(', ')
                if len(parts) == 2:
                    display_name = f"{parts[1]} {parts[0]}"
                else:
                    display_name = student['name']
            else:
                display_name = student['name']
            
            self.students.append(display_name)
        
        self.students.sort()
    
    def normalize_name(self, name):
        """Normalize names for comparison"""
        return re.sub(r'\s+', ' ', name.strip().lower())
    
    def find_student_in_grades(self, search_name):
        """Find a student in grades data using flexible matching"""
        search_normalized = self.normalize_name(search_name)
        
        for student in self.grades_data:
            # Convert "Last, First" format to "First Last" for comparison
            if ',' in student['name']:
                parts = student['name'].split(', ')
                if len(parts) == 2:
                    student_display_name = f"{parts[1]} {parts[0]}"
                else:
                    student_display_name = student['name']
            else:
                student_display_name = student['name']
            
            student_normalized = self.normalize_name(student_display_name)
            
            # Check exact match
            if search_normalized == student_normalized:
                return student
            
            # Check flexible matching (first and last name)
            search_parts = search_normalized.split()
            student_parts = self.normalize_name(student['name']).split(', ')
            
            if len(search_parts) >= 2 and len(student_parts) >= 2:
                search_first_last = {search_parts[0], search_parts[-1]}
                student_first_last = {student_parts[1].split()[0], student_parts[0].split()[0]}
                
                if search_first_last == student_first_last:
                    return student
        
        return None
    
    def find_specific_grade(self):
        """Menu option 1: Find grade for specific student and assignment"""
        dialog = SpecificGradeDialog(self.root, self.students, self.assignments)
        self.root.wait_window(dialog.dialog)
        
        if dialog.result:
            student_name, assignment = dialog.result
            student = self.find_student_in_grades(student_name)
            
            if student:
                grade = student['grades'].get(assignment)
                if grade is not None:
                    result = f"Student: {student_name}\n"
                    result += f"Assignment: {assignment}\n"
                    result += f"Grade: {grade}\n"
                    result += f"Student ID: {student['id']}\n"
                else:
                    result = f"Student: {student_name}\n"
                    result += f"Assignment: {assignment}\n"
                    result += "Grade: Not submitted/No grade\n"
            else:
                result = f"Student '{student_name}' not found in grades data.\n"
                result += "Available students:\n"
                for s in self.students[:10]:  # Show first 10 as examples
                    result += f"  - {s}\n"
                if len(self.students) > 10:
                    result += f"  ... and {len(self.students) - 10} more\n"
            
            self.display_result(result)
    
    def find_student_grades(self):
        """Menu option 2: Find all grades for a specific student"""
        dialog = StudentSelectionDialog(self.root, self.students)
        self.root.wait_window(dialog.dialog)
        
        if dialog.result:
            student_name = dialog.result
            student = self.find_student_in_grades(student_name)
            
            if student:
                result = f"All Grades for: {student_name}\n"
                result += f"Student ID: {student['id']}\n"
                result += "=" * 50 + "\n\n"
                
                # Group assignments by type
                lesson_practice = []
                code_practice = []
                assignments = []
                quizzes = []
                tests = []
                other = []
                
                for assignment, grade in student['grades'].items():
                    if grade is not None:
                        if "Lesson Practice" in assignment:
                            lesson_practice.append((assignment, grade))
                        elif "Code Practice" in assignment:
                            code_practice.append((assignment, grade))
                        elif "Assignment" in assignment:
                            assignments.append((assignment, grade))
                        elif "Quiz" in assignment:
                            quizzes.append((assignment, grade))
                        elif "Test" in assignment:
                            tests.append((assignment, grade))
                        else:
                            other.append((assignment, grade))
                
                # Display by category
                if lesson_practice:
                    result += "LESSON PRACTICE:\n"
                    for assignment, grade in lesson_practice:
                        result += f"  {assignment}: {grade}\n"
                    result += "\n"
                
                if code_practice:
                    result += "CODE PRACTICE:\n"
                    for assignment, grade in code_practice:
                        result += f"  {assignment}: {grade}\n"
                    result += "\n"
                
                if assignments:
                    result += "ASSIGNMENTS:\n"
                    for assignment, grade in assignments:
                        result += f"  {assignment}: {grade}\n"
                    result += "\n"
                
                if quizzes:
                    result += "QUIZZES:\n"
                    for assignment, grade in quizzes:
                        result += f"  {assignment}: {grade}\n"
                    result += "\n"
                
                if tests:
                    result += "TESTS:\n"
                    for assignment, grade in tests:
                        result += f"  {assignment}: {grade}\n"
                    result += "\n"
                
                if other:
                    result += "OTHER:\n"
                    for assignment, grade in other:
                        result += f"  {assignment}: {grade}\n"
                    result += "\n"
                
                # Summary
                total_grades = len([g for g in student['grades'].values() if g is not None])
                result += f"Total completed assignments: {total_grades}\n"
                
            else:
                result = f"Student '{student_name}' not found in grades data.\n"
            
            self.display_result(result)
    
    def find_assignment_grades(self):
        """Menu option 3: Find all grades for a specific assignment"""
        dialog = AssignmentSelectionDialog(self.root, self.assignments)
        self.root.wait_window(dialog.dialog)
        
        if dialog.result:
            assignment = dialog.result
            result = f"All Grades for Assignment: {assignment}\n"
            result += "=" * 50 + "\n\n"
            
            # Group students by active class sections
            section_grades = {s: [] for s in self.active_sections}
            other_grades = []

            for student in self.grades_data:
                grade = student['grades'].get(assignment)
                student_section = self.get_student_section(student['name'])
                display_grade = grade if grade is not None else ""

                if student_section in section_grades:
                    section_grades[student_section].append((student['name'], display_grade))
                else:
                    other_grades.append((student['name'], display_grade))

            total_students_with_grades = sum(len(v) for v in section_grades.values()) + len(other_grades)
            result += f"Total students with grades: {total_students_with_grades}\n\n"

            for section, grades in section_grades.items():
                if grades:
                    grades.sort(key=lambda x: self.get_last_name(x[0]))
                    result += f"{section} SECTION:\n"
                    result += "-" * 20 + "\n"
                    for student_name, grade in grades:
                        result += f"{self.format_csv_name(student_name, grade)}\n"
                    result += f"\n{section} Total: {len(grades)} students\n\n"

            if other_grades:
                other_grades.sort(key=lambda x: self.get_last_name(x[0]))
                result += "OTHER STUDENTS:\n"
                result += "-" * 20 + "\n"
                for student_name, grade in other_grades:
                    result += f"{self.format_csv_name(student_name, grade)}\n"
                result += f"\nOther Total: {len(other_grades)} students\n\n"

            # Overall Statistics
            all_grades = [entry for grades in section_grades.values() for entry in grades] + other_grades
            numeric_grades = [g for _, g in all_grades if isinstance(g, (int, float))]
            if numeric_grades:
                result += "OVERALL STATISTICS:\n"
                result += "-" * 20 + "\n"
                result += f"Average: {sum(numeric_grades) / len(numeric_grades):.2f}\n"
                result += f"Highest: {max(numeric_grades)}\n"
                result += f"Lowest: {min(numeric_grades)}\n"
            
            if total_students_with_grades == 0:
                result += "No students have submitted this assignment.\n"
            
            self.display_result(result)
    
    def export_to_google_sheets(self):
        """Menu option 4: Export assignment grades to Google Sheets"""
        dialog = AssignmentSelectionDialog(self.root, self.assignments)
        self.root.wait_window(dialog.dialog)
        
        if dialog.result:
            assignment = dialog.result
            
            # Group students by active class sections
            section_grades = {s: [] for s in self.active_sections}
            other_grades = []

            for student in self.grades_data:
                grade = student['grades'].get(assignment)
                student_section = self.get_student_section(student['name'])
                display_grade = grade if grade is not None else ""

                if student_section in section_grades:
                    section_grades[student_section].append((student['name'], display_grade))
                else:
                    other_grades.append((student['name'], display_grade))

            for grades in section_grades.values():
                grades.sort(key=lambda x: self.get_last_name(x[0]))
            other_grades.sort(key=lambda x: self.get_last_name(x[0]))

            all_section_grades = dict(section_grades)
            if other_grades:
                all_section_grades['Other'] = other_grades

            # Export to Google Sheets
            try:
                self.status_var.set("Exporting to Google Sheets...")
                self.show_progress(
                    f"Exporting assignment grades to Google Sheets...\n\n"
                    f"Assignment: {assignment}\n"
                    f"Sections: {', '.join(all_section_grades.keys())}\n\n"
                    f"Authenticating and creating spreadsheet, please wait..."
                )

                sheet_url = self.sheets_exporter.export_to_sheets(assignment, all_section_grades)

                if sheet_url:
                    result = f"Successfully exported to Google Sheets!\n\n"
                    result += f"Assignment: {assignment}\n"
                    for section, grades in all_section_grades.items():
                        label = "Other students" if section == 'Other' else f"{section} students"
                        result += f"{label}: {len(grades)}\n"
                    result += f"\nGoogle Sheet URL:\n{sheet_url}\n\n"
                    result += "Click the URL above to open your Google Sheet!"
                    
                    self.status_var.set("Export completed successfully")
                else:
                    result = "Failed to export to Google Sheets. Please check your credentials."
                    self.status_var.set("Export failed")
                
                self.display_result(result)
                
            except Exception as e:
                error_msg = f"Error exporting to Google Sheets: {str(e)}"
                messagebox.showerror("Export Error", error_msg)
                self.status_var.set("Export failed")

    def export_subchapter_to_sheets(self):
        """Menu option 5: Export all assignments for a sub-chapter (e.g., 1.4) to Google Sheets
        Each section (F2, F5, F6, Other) gets its own worksheet. The worksheet columns are:
        Last Name | First Name | <subchapter Lesson Practice> | <subchapter Code Practice Q1> | Q2 | Q3 ...
        """
        # Build a list of unique sub-chapter prefixes from assignments (token before first space)
        prefixes = []
        for a in self.assignments:
            tok = a.strip().split()[0] if a.strip() else ''
            if tok and tok not in prefixes:
                prefixes.append(tok)

        dialog = SubChapterDialog(self.root, prefixes)
        self.root.wait_window(dialog.dialog)

        if not dialog.result:
            return

        subchapter = dialog.result.strip()

        # Find matching assignments for the chosen prefix
        matching = [a for a in self.assignments if a.strip().startswith(subchapter + ' ') or a.strip() == subchapter]

        if not matching:
            messagebox.showinfo("No assignments", f"No assignments found for sub-chapter {subchapter}")
            return

        # Build per-section data: {section: [rows], ...}
        sections = {k: [] for k in self.active_sections + ['Other']}

        for student in self.grades_data:
            section = self.get_student_section(student['name']) or 'Other'

            # Parse names
            if ',' in student['name']:
                parts = student['name'].split(', ')
                last = parts[0].strip() if parts else ''
                first = parts[1].strip() if len(parts) > 1 else ''
            else:
                parts = student['name'].split()
                first = parts[0].strip() if parts else ''
                last = parts[-1].strip() if len(parts) > 1 else ''

            # Build row of grades for matching assignments (blank for not submitted)
            grade_row = [student['grades'].get(a) if student['grades'].get(a) is not None else "" for a in matching]

            key = section if section in self.active_sections else 'Other'
            sections[key].append([last, first] + grade_row)

        # Sort each section by last name
        for rows in sections.values():
            rows.sort(key=lambda r: r[0].lower())

        # Call exporter
        try:
            self.status_var.set("Exporting subchapter to Google Sheets...")
            self.show_progress(
                f"Exporting sub-chapter {subchapter} to Google Sheets...\n\n"
                f"Assignments: {len(matching)}\n"
                f"Sections: {', '.join(s for s in sections if s != 'Other')}\n\n"
                f"Authenticating and creating spreadsheet, please wait..."
            )

            sheet_url = self.sheets_exporter.export_subchapter_to_sheets(subchapter, matching, sections)

            if sheet_url:
                result = f"Successfully exported sub-chapter {subchapter} to Google Sheets:\n{sheet_url}\n"
                result += "\nLegend: blank cell = no submission"
                self.status_var.set("Export completed successfully")
            else:
                result = "Failed to export sub-chapter to Google Sheets."
                self.status_var.set("Export failed")

            self.display_result(result)

        except Exception as e:
            messagebox.showerror("Export Error", f"Error exporting sub-chapter: {str(e)}")
            self.status_var.set("Export failed")
    
    def get_student_section(self, student_name):
        """Determine which class section (F2, F5, F6) a student belongs to"""
        # Convert "Last, First" format to "First Last" for comparison
        if ',' in student_name:
            parts = student_name.split(', ')
            if len(parts) == 2:
                display_name = f"{parts[1]} {parts[0]}"
            else:
                display_name = student_name
        else:
            display_name = student_name
        
        # Check each section with flexible matching
        for section, names in self.student_names.items():
            for name in names:
                # Try exact match first
                if self.normalize_name(display_name) == self.normalize_name(name):
                    return section
                
                # Try flexible matching for names like "Riley Sky Mantaring" vs "Mantaring, Riley"
                display_parts = self.normalize_name(display_name).split()
                name_parts = self.normalize_name(name).split()
                
                if len(display_parts) >= 2 and len(name_parts) >= 2:
                    # Check if first and last names match, ignoring middle names
                    display_first_last = {display_parts[0], display_parts[-1]}
                    name_first_last = {name_parts[0], name_parts[-1]}
                    
                    if display_first_last == name_first_last:
                        return section
        
        return None  # Not found in any section
    
    def format_display_name(self, student_name):
        """Convert 'Last, First' format to 'First Last' for display"""
        if ',' in student_name:
            parts = student_name.split(', ')
            if len(parts) == 2:
                return f"{parts[1]} {parts[0]}"
        return student_name
    
    def get_last_name(self, student_name):
        """Extract last name for sorting purposes"""
        if ',' in student_name:
            # Format: "Last, First" - last name is the first part
            parts = student_name.split(', ')
            if len(parts) >= 1:
                return parts[0].strip().lower()
        else:
            # Format: "First Last" - last name is the last part
            parts = student_name.split()
            if len(parts) >= 2:
                return parts[-1].strip().lower()
        return student_name.strip().lower()
    
    def format_csv_name(self, student_name, grade):
        """Format student name and grade as CSV: Last name, First name, Grade"""
        if ',' in student_name:
            # Format: "Last, First" - already in correct order
            parts = student_name.split(', ')
            if len(parts) >= 2:
                last_name = parts[0].strip()
                first_name = parts[1].strip()
                return f"{last_name},{first_name},{grade}"
            else:
                return f"{student_name},{grade}"
        else:
            # Format: "First Last" - need to split and reorder
            parts = student_name.split()
            if len(parts) >= 2:
                first_name = parts[0].strip()
                last_name = parts[-1].strip()
                return f"{last_name},{first_name},{grade}"
            else:
                return f"{student_name},{grade}"
    
    def show_progress(self, text):
        """Clear the results area and show a progress message immediately."""
        self.results_text.config(state=tk.NORMAL)
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, text)
        self.results_text.config(state=tk.DISABLED)
        self.root.update()

    def display_result(self, result):
        """Display result in the results text area and make URLs clickable."""
        import webbrowser

        # Clear existing content
        self.results_text.config(state=tk.NORMAL)
        self.results_text.delete(1.0, tk.END)

        # Pattern to find URLs
        url_re = re.compile(r"(https?://[\w\-._~:/?#[\]@!$&'()*+,;=%]+)")

        pos = 0
        for match in url_re.finditer(result):
            start, end = match.span()
            # Insert text before URL
            if start > pos:
                self.results_text.insert(tk.END, result[pos:start])

            url = match.group(0)
            tag_name = f"url_{start}_{end}"
            # Insert URL text with tag
            self.results_text.insert(tk.END, url, (tag_name,))

            # Configure tag appearance (blue underline) and bindings
            self.results_text.tag_config(tag_name, foreground="#3b82f6", underline=1)
            # On click, open in default browser
            self.results_text.tag_bind(tag_name, "<Button-1>", lambda e, u=url: webbrowser.open(u))
            # Change cursor on hover
            self.results_text.tag_bind(tag_name, "<Enter>", lambda e: self.results_text.config(cursor="hand2"))
            self.results_text.tag_bind(tag_name, "<Leave>", lambda e: self.results_text.config(cursor=""))

            pos = end

        # Insert remaining text after last URL
        if pos < len(result):
            self.results_text.insert(tk.END, result[pos:])

        # Ensure the widget is editable only programmatically
        self.results_text.config(state=tk.DISABLED)


# ── Shared dialog palette & button helper ────────────────────────────────────
_DC = {
    'bg':      '#f8fafc',
    'hdr':     '#1e293b',
    'hdr_fg':  '#f1f5f9',
    'hdr_sub': '#94a3b8',
    'text':    '#1e293b',
    'sub':     '#64748b',
    'btn_ok':  '#3b82f6',
    'btn_okh': '#2563eb',
    'btn_cx':  '#64748b',
    'btn_cxh': '#475569',
}

def _dlg_btn(parent, text, cmd, bg, hov):
    btn = tk.Button(
        parent, text=text, command=cmd,
        bg=bg, fg='#ffffff',
        activebackground=hov, activeforeground='#ffffff',
        font=('Segoe UI', 10), relief=tk.FLAT, bd=0,
        padx=22, pady=8, cursor='hand2'
    )
    btn.bind('<Enter>', lambda e, b=btn, c=hov: b.config(bg=c))
    btn.bind('<Leave>', lambda e, b=btn, c=bg:  b.config(bg=c))
    return btn

def _dlg_header(dialog, title, subtitle=None):
    hdr = tk.Frame(dialog, bg=_DC['hdr'])
    hdr.pack(fill=tk.X)
    tk.Label(hdr, text=title, bg=_DC['hdr'], fg=_DC['hdr_fg'],
             font=('Segoe UI', 13, 'bold'), anchor=tk.W
             ).pack(fill=tk.X, padx=20, pady=(14, 2 if subtitle else 12))
    if subtitle:
        tk.Label(hdr, text=subtitle, bg=_DC['hdr'], fg=_DC['hdr_sub'],
                 font=('Segoe UI', 9), anchor=tk.W
                 ).pack(fill=tk.X, padx=20, pady=(0, 12))

def _dlg_field(body, label):
    tk.Label(body, text=label, bg=_DC['bg'], fg=_DC['sub'],
             font=('Segoe UI', 9, 'bold'), anchor=tk.W).pack(fill=tk.X)

def _dlg_combo(body, var, values, width=48):
    combo = ttk.Combobox(body, textvariable=var, values=values,
                         width=width, font=('Segoe UI', 10))
    combo.pack(fill=tk.X, pady=(2, 12))
    return combo


class SpecificGradeDialog:
    def __init__(self, parent, students, assignments):
        self.result = None
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Find Specific Grade")
        self.dialog.configure(bg=_DC['bg'])
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.resizable(False, False)

        _dlg_header(self.dialog, "Find Specific Grade")

        body = tk.Frame(self.dialog, bg=_DC['bg'])
        body.pack(fill=tk.BOTH, padx=24, pady=16)

        _dlg_field(body, "STUDENT")
        self.student_var = tk.StringVar()
        _dlg_combo(body, self.student_var, students)

        _dlg_field(body, "ASSIGNMENT")
        self.assignment_var = tk.StringVar()
        _dlg_combo(body, self.assignment_var, assignments)

        footer = tk.Frame(self.dialog, bg=_DC['bg'])
        footer.pack(fill=tk.X, padx=24, pady=(0, 20))
        _dlg_btn(footer, "Find Grade", self.ok_clicked,  _DC['btn_ok'], _DC['btn_okh']).pack(side=tk.LEFT, padx=(0, 8))
        _dlg_btn(footer, "Cancel",     self.cancel_clicked, _DC['btn_cx'], _DC['btn_cxh']).pack(side=tk.LEFT)

        self.dialog.geometry("500x290")

    def ok_clicked(self):
        if self.student_var.get() and self.assignment_var.get():
            self.result = (self.student_var.get(), self.assignment_var.get())
            self.dialog.destroy()
        else:
            messagebox.showwarning("Warning", "Please select both student and assignment")

    def cancel_clicked(self):
        self.dialog.destroy()


class StudentSelectionDialog:
    def __init__(self, parent, students):
        self.result = None
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Select Student")
        self.dialog.configure(bg=_DC['bg'])
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.resizable(False, False)

        _dlg_header(self.dialog, "Select Student")

        body = tk.Frame(self.dialog, bg=_DC['bg'])
        body.pack(fill=tk.BOTH, padx=24, pady=16)

        _dlg_field(body, "STUDENT")
        self.student_var = tk.StringVar()
        _dlg_combo(body, self.student_var, students)

        footer = tk.Frame(self.dialog, bg=_DC['bg'])
        footer.pack(fill=tk.X, padx=24, pady=(0, 20))
        _dlg_btn(footer, "View Grades", self.ok_clicked,     _DC['btn_ok'], _DC['btn_okh']).pack(side=tk.LEFT, padx=(0, 8))
        _dlg_btn(footer, "Cancel",      self.cancel_clicked, _DC['btn_cx'], _DC['btn_cxh']).pack(side=tk.LEFT)

        self.dialog.geometry("480x195")

    def ok_clicked(self):
        if self.student_var.get():
            self.result = self.student_var.get()
            self.dialog.destroy()
        else:
            messagebox.showwarning("Warning", "Please select a student")

    def cancel_clicked(self):
        self.dialog.destroy()


class AssignmentSelectionDialog:
    def __init__(self, parent, assignments):
        self.result = None
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Select Assignment")
        self.dialog.configure(bg=_DC['bg'])
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.resizable(False, False)

        _dlg_header(self.dialog, "Select Assignment")

        body = tk.Frame(self.dialog, bg=_DC['bg'])
        body.pack(fill=tk.BOTH, padx=24, pady=16)

        _dlg_field(body, "ASSIGNMENT")
        self.assignment_var = tk.StringVar()
        _dlg_combo(body, self.assignment_var, assignments, width=56)

        footer = tk.Frame(self.dialog, bg=_DC['bg'])
        footer.pack(fill=tk.X, padx=24, pady=(0, 20))
        _dlg_btn(footer, "View Grades", self.ok_clicked,     _DC['btn_ok'], _DC['btn_okh']).pack(side=tk.LEFT, padx=(0, 8))
        _dlg_btn(footer, "Cancel",      self.cancel_clicked, _DC['btn_cx'], _DC['btn_cxh']).pack(side=tk.LEFT)

        self.dialog.geometry("520x195")

    def ok_clicked(self):
        if self.assignment_var.get():
            self.result = self.assignment_var.get()
            self.dialog.destroy()
        else:
            messagebox.showwarning("Warning", "Please select an assignment")

    def cancel_clicked(self):
        self.dialog.destroy()


class SubChapterDialog:
    def __init__(self, parent, subchapter_choices):
        self.result = None
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Select Sub-chapter")
        self.dialog.configure(bg=_DC['bg'])
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.resizable(False, False)

        _dlg_header(self.dialog, "Export Sub-chapter")

        body = tk.Frame(self.dialog, bg=_DC['bg'])
        body.pack(fill=tk.BOTH, padx=24, pady=16)

        _dlg_field(body, "SUB-CHAPTER")
        self.subchapter_var = tk.StringVar()
        combo = ttk.Combobox(body, textvariable=self.subchapter_var,
                             values=subchapter_choices, width=22, font=('Segoe UI', 10))
        combo.pack(anchor=tk.W, pady=(2, 4))
        if subchapter_choices:
            combo.current(0)

        footer = tk.Frame(self.dialog, bg=_DC['bg'])
        footer.pack(fill=tk.X, padx=24, pady=(8, 20))
        _dlg_btn(footer, "Export", self.ok_clicked,     _DC['btn_ok'], _DC['btn_okh']).pack(side=tk.LEFT, padx=(0, 8))
        _dlg_btn(footer, "Cancel", self.cancel_clicked, _DC['btn_cx'], _DC['btn_cxh']).pack(side=tk.LEFT)

        self.dialog.geometry("340x195")

    def ok_clicked(self):
        val = self.subchapter_var.get().strip()
        if val:
            self.result = val
            self.dialog.destroy()
        else:
            messagebox.showwarning("Warning", "Please select a sub-chapter")

    def cancel_clicked(self):
        self.dialog.destroy()


class ClassSelectionDialog:
    def __init__(self, parent, all_sections, active_sections):
        self.result = None
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Select Active Classes")
        self.dialog.configure(bg=_DC['bg'])
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.resizable(False, False)

        _dlg_header(self.dialog, "Select Active Classes",
                    "Only selected classes appear in results and exports.")

        body = tk.Frame(self.dialog, bg=_DC['bg'])
        body.pack(fill=tk.BOTH, padx=24, pady=(10, 4))

        self.vars = {}
        for section in all_sections:
            var = tk.BooleanVar(value=section in active_sections)
            self.vars[section] = var
            tk.Checkbutton(
                body, text=section, variable=var,
                bg=_DC['bg'], fg=_DC['text'],
                selectcolor=_DC['bg'],
                activebackground=_DC['bg'], activeforeground=_DC['text'],
                font=('Segoe UI', 11), anchor=tk.W
            ).pack(fill=tk.X, pady=3)

        footer = tk.Frame(self.dialog, bg=_DC['bg'])
        footer.pack(fill=tk.X, padx=24, pady=(8, 20))
        _dlg_btn(footer, "Save",   self.ok_clicked,     _DC['btn_ok'], _DC['btn_okh']).pack(side=tk.LEFT, padx=(0, 8))
        _dlg_btn(footer, "Cancel", self.cancel_clicked, _DC['btn_cx'], _DC['btn_cxh']).pack(side=tk.LEFT)

        self.dialog.update_idletasks()
        self.dialog.geometry(f"320x{180 + 36 * len(all_sections)}")

    def ok_clicked(self):
        selected = [s for s, v in self.vars.items() if v.get()]
        if not selected:
            messagebox.showwarning("Warning", "Please select at least one class")
            return
        self.result = selected
        self.dialog.destroy()

    def cancel_clicked(self):
        self.dialog.destroy()


def main():
    root = tk.Tk()
    app = StudentGradesApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
