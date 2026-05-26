# Google Sheets API Setup Guide

This guide will help you set up Google Sheets API integration for the Student Grades Management App.

## Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" at the top
3. Click "New Project"
4. Enter a project name (e.g., "Student Grades App")
5. Click "Create"

## Step 2: Enable Google Sheets API

1. In the Google Cloud Console, make sure your new project is selected
2. Go to "APIs & Services" > "Library"
3. Search for "Google Sheets API"
4. Click on "Google Sheets API"
5. Click "Enable"

## Step 3: Create Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. If prompted, configure the OAuth consent screen:
   - Choose "External" user type
   - Fill in the required fields (App name, User support email, Developer contact)
   - Add your email to test users
   - Save and continue through all steps
4. For Application type, choose "Desktop application"
5. Give it a name (e.g., "Student Grades App")
6. Click "Create"

## Step 4: Download Credentials

1. After creating the OAuth client ID, click the download button (⬇️)
2. Save the downloaded JSON file
3. Rename it to `credentials.json`
4. Place it in the same folder as your `student_grades_app.py` file

## Step 5: First Time Setup

1. Run the Student Grades App
2. Click "4. Export Assignment Grades to Google Sheets"
3. Select an assignment
4. The first time, your browser will open for authentication:
   - Sign in with your Google account
   - Click "Allow" to grant permissions
   - The app will create a `token.pickle` file for future use

## Step 6: Using the Export Feature

After setup, you can:
1. Click "4. Export Assignment Grades to Google Sheets"
2. Select any assignment
3. The app will automatically:
   - Create a new Google Sheet
   - Organize data by sections (F2, F5, F6)
   - Sort students alphabetically by last name
   - Format the sheet with headers and styling
   - Provide you with the Google Sheet URL

## File Structure

Your folder should contain:
```
student_grades_app.py
google_sheets_integration.py
credentials.json          # Downloaded from Google Cloud Console
token.pickle             # Created after first authentication
2025-09-13T1722_Grades-(7fac90)_CS_Python_Fundamentals.csv
F2 - names.csv
F5 - names.csv
F6 - names.csv
```

## Troubleshooting

### "credentials.json file not found"
- Make sure you downloaded the JSON file from Google Cloud Console
- Rename it to exactly `credentials.json`
- Place it in the same folder as the app

### "Authentication failed"
- Delete the `token.pickle` file and try again
- Make sure you're signed in to the correct Google account
- Check that the Google Sheets API is enabled in your project

### "Permission denied"
- Make sure you added your email as a test user in the OAuth consent screen
- Check that the Google Sheets API is enabled

## Security Notes

- Keep your `credentials.json` file secure and don't share it
- The `token.pickle` file contains your access tokens - keep it secure
- Only share Google Sheets with people who need access

## Features of the Exported Sheet

The exported Google Sheet will include:
- **Separate tabs** for each class section (F2 Section, F5 Section, F6 Section, Other Students)
- **Assignment name** as the main spreadsheet title
- **Section-specific data** on each tab:
  - Assignment name and section name at the top
  - Columns: Last Name, First Name, Grade
  - Students sorted alphabetically by last name within each section
- **Professional formatting** with headers and styling on each tab
- **Auto-sized columns** for easy reading
- **Easy navigation** between class sections using tabs
