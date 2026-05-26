# AI Cheating Checker — Setup & Usage

## What this script does

`ai_check.py` logs into ProjectStem (Canvas LMS), fetches every student's code
submission for each assignment listed in `assignments_to_check.txt`, scans the
code for patterns that suggest AI-generated or advanced code the class has not
yet learned, and writes the results to a timestamped PDF report.

---

## Files in this folder

| File | Description |
|---|---|
| `ai_check.py` | Main script |
| `checklist_S1_S5.csv` | Student roster — columns: First name, Last name, ID, Group |
| `assignments_to_check.txt` | One Canvas assignment/quiz URL per line |
| `PrjStem_login.txt` | Login credentials (keep this file private) |

---

## Requirements

### Python
Python 3.10 or higher.  
Download from https://www.python.org/downloads/

### Python packages
Run once in a terminal:

```
pip install selenium reportlab
```

### Google Chrome
The script drives Chrome via Selenium.  
Download from https://www.google.com/chrome/

### ChromeDriver
ChromeDriver must match your installed Chrome version.  
Download from https://googlechromelabs.github.io/chrome-for-testing/  
Place `chromedriver.exe` somewhere on your system PATH, or in the same folder as the script.

---

## Credentials

`PrjStem_login.txt` must contain exactly these two lines:

```
username: your@email.com
password: yourpassword
```

Keep this file private — do not commit it to version control.

---

## Running the script

Open a terminal, navigate to the folder containing the files, then run:

```
python ai_check.py
```

A Chrome window will open automatically. The script logs in, checks every
student, then closes the browser and writes a PDF named:

```
ai_check_YYYYMMDD_HHMMSS.pdf
```

---

## Cheating indicators scanned

| Flag | Pattern |
|---|---|
| `comment` | Any line containing `#` |
| `f-string` | `f"` or `f'` (formatted string literals) |
| `for loop` | Line starting with `for` |
| `while loop` | Line starting with `while` |

---

## Updating the student list

Replace `checklist_S1_S5.csv` with a new file using the same column headers:

```
First name,Last name,ID,Group
```

## Updating the assignments to check

Edit `assignments_to_check.txt` — one Canvas URL per line, blank lines are ignored.
Both assignment URLs and quiz URLs are supported.
