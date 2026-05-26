#!/usr/bin/env python3
"""
Google Sheets Integration Module
Handles authentication and data export to Google Sheets
"""

import os
import pickle
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import tkinter as tk
from tkinter import messagebox

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

class GoogleSheetsExporter:
    def __init__(self):
        self.service = None
        self.authenticated = False
    
    def authenticate(self):
        """Authenticate with Google Sheets API"""
        creds = None
        # The file token.pickle stores the user's access and refresh tokens.
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists('credentials.json'):
                    messagebox.showerror("Error", 
                        "credentials.json file not found!\n\n"
                        "Please follow these steps:\n"
                        "1. Go to https://console.cloud.google.com/\n"
                        "2. Create a new project or select existing one\n"
                        "3. Enable Google Sheets API\n"
                        "4. Create credentials (OAuth 2.0 Client ID)\n"
                        "5. Download the JSON file and rename it to 'credentials.json'\n"
                        "6. Place it in the same folder as this application")
                    return False
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save the credentials for the next run
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        
        try:
            self.service = build('sheets', 'v4', credentials=creds)
            self.authenticated = True
            return True
        except Exception as e:
            messagebox.showerror("Authentication Error", f"Failed to authenticate: {str(e)}")
            return False
    
    def _tab_name(self, section):
        """Return the spreadsheet tab name for a section key."""
        return 'Other Students' if section == 'Other' else f"{section} Section"

    def create_sheet_with_tabs(self, title, sections):
        """Create a new Google Sheet with one tab per section."""
        if not self.authenticated:
            if not self.authenticate():
                return None

        try:
            sheets_list = [
                {'properties': {'title': self._tab_name(s), 'sheetId': i}}
                for i, s in enumerate(sections)
            ]
            spreadsheet = self.service.spreadsheets().create(
                body={'properties': {'title': title}, 'sheets': sheets_list},
                fields='spreadsheetId'
            ).execute()
            return spreadsheet.get('spreadsheetId')
        except HttpError as error:
            messagebox.showerror("Error", f"Failed to create sheet: {error}")
            return None
    
    def format_sheet_data(self, assignment_name, f2_grades, f5_grades, f6_grades, other_grades):
        """Format data for Google Sheets export"""
        data = []
        
        # Add header
        data.append([f"Assignment: {assignment_name}"])
        data.append([])  # Empty row
        
        # F2 Section
        if f2_grades:
            data.append(["F2 SECTION"])
            data.append(["Last Name", "First Name", "Grade"])
            for student_name, grade in f2_grades:
                if ',' in student_name:
                    parts = student_name.split(', ')
                    if len(parts) >= 2:
                        last_name = parts[0].strip()
                        first_name = parts[1].strip()
                        data.append([last_name, first_name, grade])
            data.append([])  # Empty row
        
        # F5 Section
        if f5_grades:
            data.append(["F5 SECTION"])
            data.append(["Last Name", "First Name", "Grade"])
            for student_name, grade in f5_grades:
                if ',' in student_name:
                    parts = student_name.split(', ')
                    if len(parts) >= 2:
                        last_name = parts[0].strip()
                        first_name = parts[1].strip()
                        data.append([last_name, first_name, grade])
            data.append([])  # Empty row
        
        # F6 Section
        if f6_grades:
            data.append(["F6 SECTION"])
            data.append(["Last Name", "First Name", "Grade"])
            for student_name, grade in f6_grades:
                if ',' in student_name:
                    parts = student_name.split(', ')
                    if len(parts) >= 2:
                        last_name = parts[0].strip()
                        first_name = parts[1].strip()
                        data.append([last_name, first_name, grade])
            data.append([])  # Empty row
        
        # Other students
        if other_grades:
            data.append(["OTHER STUDENTS"])
            data.append(["Last Name", "First Name", "Grade"])
            for student_name, grade in other_grades:
                if ',' in student_name:
                    parts = student_name.split(', ')
                    if len(parts) >= 2:
                        last_name = parts[0].strip()
                        first_name = parts[1].strip()
                        data.append([last_name, first_name, grade])
        
        return data
    
    def export_to_sheets(self, assignment_name, section_grades_dict):
        """Export assignment grades to Google Sheets with one tab per section.
        section_grades_dict: {section_name: [(student_name, grade), ...]}
        Use 'Other' as the key for unmatched students."""
        if not self.authenticated:
            if not self.authenticate():
                return None

        sections = list(section_grades_dict.keys())
        spreadsheet_id = self.create_sheet_with_tabs(f"Assignment Grades - {assignment_name}", sections)
        if not spreadsheet_id:
            return None

        try:
            DATA_OFFSET = 4  # title + section + empty + header
            for i, (section, grades) in enumerate(section_grades_dict.items()):
                self.write_section_data(spreadsheet_id, self._tab_name(section), grades, assignment_name)
                numeric = [g for (_, g) in grades if isinstance(g, (int, float))]
                section_max = max(numeric) if numeric else None
                if section_max is not None:
                    rows_to_highlight = [
                        DATA_OFFSET + j
                        for j, (_, grade) in enumerate(grades)
                        if not isinstance(grade, (int, float)) or grade < section_max
                    ]
                    self._highlight_rows(spreadsheet_id, i, rows_to_highlight, 3)
            self.format_all_sheets(spreadsheet_id, sections)
            return f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
        except HttpError as error:
            messagebox.showerror("Error", f"Failed to write data: {error}")
            return None
    
    def format_sheet(self, spreadsheet_id):
        """Apply formatting to the Google Sheet"""
        try:
            requests = []
            
            # Format headers (bold)
            requests.append({
                'repeatCell': {
                    'range': {
                        'sheetId': 0,
                        'startRowIndex': 0,
                        'endRowIndex': 1
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'textFormat': {
                                'bold': True,
                                'fontSize': 14
                            }
                        }
                    },
                    'fields': 'userEnteredFormat.textFormat'
                }
            })
            
            # Format section headers (bold, background color)
            for i in range(0, 100):  # Check first 100 rows for section headers
                requests.append({
                    'repeatCell': {
                        'range': {
                            'sheetId': 0,
                            'startRowIndex': i,
                            'endRowIndex': i + 1
                        },
                        'cell': {
                            'userEnteredFormat': {
                                'textFormat': {
                                    'bold': True
                                },
                                'backgroundColor': {
                                    'red': 0.9,
                                    'green': 0.9,
                                    'blue': 0.9
                                }
                            }
                        },
                        'fields': 'userEnteredFormat.textFormat,userEnteredFormat.backgroundColor'
                    }
                })
            
            # Auto-resize columns
            requests.append({
                'autoResizeDimensions': {
                    'dimensions': {
                        'sheetId': 0,
                        'dimension': 'COLUMNS',
                        'startIndex': 0,
                        'endIndex': 3
                    }
                }
            })
            
            # Apply formatting
            body = {
                'requests': requests
            }
            
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body=body
            ).execute()
            
        except HttpError as error:
            print(f"Formatting error (non-critical): {error}")
    
    def _highlight_rows(self, spreadsheet_id, sheet_id, row_indices, num_cols):
        """Apply yellow background to the given row indices in a sheet."""
        if not row_indices:
            return
        requests = []
        for row_idx in row_indices:
            requests.append({
                'repeatCell': {
                    'range': {
                        'sheetId': sheet_id,
                        'startRowIndex': row_idx,
                        'endRowIndex': row_idx + 1,
                        'startColumnIndex': 0,
                        'endColumnIndex': num_cols
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'backgroundColor': {'red': 1.0, 'green': 1.0, 'blue': 0.6}
                        }
                    },
                    'fields': 'userEnteredFormat.backgroundColor'
                }
            })
        try:
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id, body={'requests': requests}
            ).execute()
        except HttpError as error:
            print(f"Highlighting error (non-critical): {error}")

    def write_section_data(self, spreadsheet_id, sheet_name, grades_data, assignment_name):
        """Write data to a specific sheet tab"""
        if not grades_data:
            return

        data = []
        data.append([f"Assignment: {assignment_name}"])
        data.append([f"Section: {sheet_name}"])
        data.append([])
        data.append(["Last Name", "First Name", "Grade"])

        for student_name, grade in grades_data:
            if ',' in student_name:
                parts = student_name.split(', ')
                last_name = parts[0].strip()
                first_name = parts[1].strip() if len(parts) > 1 else ''
            else:
                parts = student_name.split()
                last_name = parts[-1].strip() if len(parts) > 1 else student_name
                first_name = parts[0].strip() if parts else ''
            data.append([last_name, first_name, grade])
        
        # Write data to the specific sheet
        body = {
            'values': data
        }
        
        self.service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=f"'{sheet_name}'!A1",
            valueInputOption='RAW',
            body=body
        ).execute()

    def write_section_multi_columns(self, spreadsheet_id, sheet_name, header_assignments, rows):
        """Write data to a specific sheet tab where rows already contain [Last, First, grade1, grade2, ...]
        header_assignments is a list of assignment column headers (strings)"""
        if not rows:
            return

        data = []
        data.append([f"Sub-chapter export"])  # Title row
        data.append([f"Section: {sheet_name}"])
        data.append([])

        # Column headers: Last Name, First Name, then each assignment, then Total
        header = ["Last Name", "First Name"] + header_assignments + ["Total"]
        data.append(header)

        # Append all rows (assumed already in Last, First, grade1... order)
        for r in rows:
            # compute total for the grade columns (elements after first two)
            try:
                grades = r[2:]
            except Exception:
                grades = []
            total = 0.0
            for g in grades:
                try:
                    # allow numeric values or numeric strings
                    total += float(g)
                except Exception:
                    # ignore blanks or non-numeric
                    continue
            new_row = list(r) + [total]
            data.append(new_row)

        body = {'values': data}

        self.service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=f"'{sheet_name}'!A1",
            valueInputOption='RAW',
            body=body
        ).execute()

    def _hide_columns(self, spreadsheet_id, sheet_id, col_indices):
        """Hide specified column indices in a sheet."""
        if not col_indices:
            return
        requests = [
            {
                'updateDimensionProperties': {
                    'range': {
                        'sheetId': sheet_id,
                        'dimension': 'COLUMNS',
                        'startIndex': col_idx,
                        'endIndex': col_idx + 1
                    },
                    'properties': {'hiddenByUser': True},
                    'fields': 'hiddenByUser'
                }
            }
            for col_idx in col_indices
        ]
        try:
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id, body={'requests': requests}
            ).execute()
        except HttpError as error:
            print(f"Column hide error (non-critical): {error}")

    def export_subchapter_to_sheets(self, subchapter, assignments, sections_dict):
        """Export multiple assignments organized by section.
        sections_dict: {section: [[last, first, grade1, grade2, ...], ...]}"""
        if not self.authenticated:
            if not self.authenticate():
                return None

        sections = list(sections_dict.keys())
        spreadsheet_id = self.create_sheet_with_tabs(f"Subchapter {subchapter} Grades", sections)
        if not spreadsheet_id:
            return None

        # Columns 0=Last, 1=First, 2..N=assignments, N+1=Total
        # Hide assignment columns whose title contains 'lesson practice' or 'code practice'
        cols_to_hide = [
            2 + idx
            for idx, a in enumerate(assignments)
            if 'lesson practice' in a.lower() or 'code practice' in a.lower()
        ]

        try:
            DATA_OFFSET = 4  # title + section + empty + header
            num_cols = 2 + len(assignments) + 1  # Last, First, grades..., Total
            for i, (section, rows) in enumerate(sections_dict.items()):
                self.write_section_multi_columns(spreadsheet_id, self._tab_name(section), assignments, rows)
                self._hide_columns(spreadsheet_id, i, cols_to_hide)

                # Compute each student's total, then find the section max
                totals = []
                for row in rows:
                    t = 0.0
                    for g in row[2:]:
                        try:
                            t += float(g)
                        except (TypeError, ValueError):
                            pass
                    totals.append(t)

                section_max = max(totals) if totals else None
                if section_max is not None and section_max > 0:
                    rows_to_highlight = [
                        DATA_OFFSET + j
                        for j, t in enumerate(totals)
                        if t < section_max
                    ]
                    self._highlight_rows(spreadsheet_id, i, rows_to_highlight, num_cols)

            self.format_all_sheets(spreadsheet_id, sections)
            return f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"
        except HttpError as error:
            messagebox.showerror("Error", f"Failed to write subchapter data: {error}")
            return None

    def write_section_split(self, spreadsheet_id, sheet_name, header_assignments, section_data):
        """Write a sheet with a legend and two blocks: Submitted and Not submitted.
        section_data is a dict {'submitted': [rows], 'not_submitted': [rows]}"""
        submitted = section_data.get('submitted', [])
        not_sub = section_data.get('not_submitted', [])

        data = []
        data.append([f"Sub-chapter: {header_assignments[0].split()[0] if header_assignments else ''}"])
        data.append([f"Section: {sheet_name}"])
        data.append(["Legend:", "Blank cell = no submission"])
        data.append([])

        # Submitted block
        data.append(["Submitted"])
        header = ["Last Name", "First Name"] + header_assignments + ["Total"]
        data.append(header)
        for r in submitted:
            # compute total for the grade columns (elements after first two)
            grades = r[2:]
            total = 0.0
            for g in grades:
                try:
                    total += float(g)
                except Exception:
                    continue
            data.append(list(r) + [total])

        data.append([])

        # Not submitted block
        data.append(["Not submitted"])
        data.append(header)
        for r in not_sub:
            grades = r[2:]
            total = 0.0
            for g in grades:
                try:
                    total += float(g)
                except Exception:
                    continue
            data.append(list(r) + [total])

        body = {'values': data}

        self.service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=f"'{sheet_name}'!A1",
            valueInputOption='RAW',
            body=body
        ).execute()
    
    def format_all_sheets(self, spreadsheet_id, sections):
        """Apply formatting to all sheets in the spreadsheet."""
        try:
            requests = []
            for i, section in enumerate(sections):
                requests.append({
                    'repeatCell': {
                        'range': {'sheetId': i, 'startRowIndex': 0, 'endRowIndex': 4},
                        'cell': {'userEnteredFormat': {'textFormat': {'bold': True, 'fontSize': 12}}},
                        'fields': 'userEnteredFormat.textFormat'
                    }
                })
                requests.append({
                    'repeatCell': {
                        'range': {'sheetId': i, 'startRowIndex': 3, 'endRowIndex': 4},
                        'cell': {
                            'userEnteredFormat': {
                                'textFormat': {'bold': True},
                                'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}
                            }
                        },
                        'fields': 'userEnteredFormat.textFormat,userEnteredFormat.backgroundColor'
                    }
                })
                requests.append({
                    'autoResizeDimensions': {
                        'dimensions': {'sheetId': i, 'dimension': 'COLUMNS', 'startIndex': 0, 'endIndex': 3}
                    }
                })
            if requests:
                self.service.spreadsheets().batchUpdate(
                    spreadsheetId=spreadsheet_id, body={'requests': requests}
                ).execute()
        except HttpError as error:
            print(f"Formatting error (non-critical): {error}")
