#!/usr/bin/env python3
"""
ai_check.py
For every student in checklist_S1_S5.csv, fetch their code submission for
every URL in assignments_to_check.txt, scan for AI-cheating indicators,
and write the findings to a timestamped PDF report.

Requires:  pip install selenium reportlab
"""

import csv
import os
import getpass
import time
import re
from datetime import datetime
from urllib.parse import urlparse
from xml.sax.saxutils import escape   # safe HTML for reportlab Paragraphs

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle
)

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

LOGIN_URL        = "https://projectstem.org/users/sign_in"
BASE_URL         = "https://courses.projectstem.org"
CSV_FILE         = "checklist_S1_S5.csv"
ASSIGNMENTS_FILE = "assignments_to_check.txt"
CREDS_FILE       = "PrjStem_login.txt"

# ---------------------------------------------------------------------------
# AI-cheating patterns
# ---------------------------------------------------------------------------

CHECKS = [
    ("comment",    re.compile(r'#')),
    ("f-string",   re.compile(r'\bf["\']')),
    ("for loop",   re.compile(r'^\s*for\s+')),
    ("while loop", re.compile(r'^\s*while\s+')),
]

def ai_check(code_text):
    """Return list of (line_number, line, [reasons]) for suspicious lines."""
    flagged = []
    for i, line in enumerate(code_text.splitlines(), start=1):
        reasons = [label for label, pat in CHECKS if pat.search(line)]
        if reasons:
            flagged.append((i, line, reasons))
    return flagged

# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------

def get_all_students():
    with open(CSV_FILE, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_urls():
    urls = []
    with open(ASSIGNMENTS_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("http"):
                urls.append(line)
    return urls


def parse_canvas_url(url):
    """Return (course_id, resource_type, resource_id) from a Canvas URL."""
    parts = urlparse(url).path.strip("/").split("/")
    if len(parts) >= 4 and parts[0] == "courses":
        return parts[1], parts[2], parts[3]
    return None, None, None


def url_label(url):
    """Short human-readable label for a Canvas URL."""
    _, rtype, rid = parse_canvas_url(url)
    if rtype and rid:
        return f"{rtype.rstrip('s').capitalize()} {rid}"
    return url


def get_credentials():
    if os.path.exists(CREDS_FILE):
        creds = {}
        with open(CREDS_FILE, encoding="utf-8") as f:
            for line in f:
                if ":" in line:
                    key, _, val = line.partition(":")
                    creds[key.strip().lower()] = val.strip()
        username = creds.get("username")
        password = creds.get("password")
        if username and password:
            return username, password
    username = os.environ.get("PROJECTSTEM_USERNAME") or input("ProjectStem email: ")
    password = os.environ.get("PROJECTSTEM_PASSWORD") or getpass.getpass("Password: ")
    return username, password

# ---------------------------------------------------------------------------
# Selenium helpers
# ---------------------------------------------------------------------------

def login(driver, wait, username, password):
    driver.get(LOGIN_URL)
    wait.until(EC.presence_of_element_located((By.ID, "user_login")))
    driver.find_element(By.ID, "user_login").send_keys(username)
    driver.find_element(By.ID, "user_password").send_keys(password)
    driver.find_element(By.ID, "new_user").submit()
    wait.until(lambda d: "sign_in" not in d.current_url)
    print(f"[+] Logged in — {driver.current_url}")


def find_quiz_submission_url(driver, wait, course_id, quiz_id, student_name, student_id):
    mod_url = f"{BASE_URL}/courses/{course_id}/quizzes/{quiz_id}/moderate"
    driver.get(mod_url)
    try:
        wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "table, .student_list, #moderate_quiz_form")
        ))
    except TimeoutException:
        return None

    for attr in (f"[data-student-id='{student_id}']", f"#user_{student_id}"):
        try:
            row  = driver.find_element(By.CSS_SELECTOR, attr)
            link = row.find_element(By.CSS_SELECTOR, "a[href*='submission'], a[href*='history']")
            return link.get_attribute("href")
        except NoSuchElementException:
            pass

    first_last = student_name.lower().split()
    for row in driver.find_elements(By.CSS_SELECTOR, "tr, li.student"):
        if all(p in row.text.lower() for p in first_last):
            try:
                link = row.find_element(
                    By.CSS_SELECTOR,
                    "a[href*='submission'], a[href*='history'], a[href*='quiz']"
                )
                return link.get_attribute("href")
            except NoSuchElementException:
                pass
    return None


def get_speedgrader_url(course_id, assignment_id, student_id):
    return (
        f"{BASE_URL}/courses/{course_id}/gradebook/speed_grader"
        f"?assignment_id={assignment_id}&student_id={student_id}"
    )


def extract_code(driver, wait):
    """Return list of (label, text) from the current page."""
    # SpeedGrader: submission lives in a dynamically injected iframe
    if driver.find_elements(By.ID, "iframe_holder"):
        try:
            wait.until(EC.visibility_of_element_located((By.ID, "iframe_holder")))
            wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "#iframe_holder iframe")
            ))
        except TimeoutException:
            return []
        time.sleep(1)
        try:
            iframe = driver.find_element(By.CSS_SELECTOR, "#iframe_holder iframe")
            driver.switch_to.frame(iframe)
            text = driver.find_element(By.TAG_NAME, "body").text.strip()
            return [("submission", text)] if text else []
        except Exception:
            return []
        finally:
            driver.switch_to.default_content()

    # Quiz / other page: scan common selectors + iframes
    time.sleep(2)

    def scrape(d):
        found = []
        for label, sel in [
            ("pre", "pre"), ("code", "code"),
            (".quiz_response_text", ".quiz_response_text"),
            (".quiz-answer", ".quiz-answer"),
            (".answer_text", ".answer_text"),
            ("textarea", "textarea"),
            (".CodeMirror-code", ".CodeMirror-code"),
            (".cm-content", ".cm-content"),
        ]:
            for el in d.find_elements(By.CSS_SELECTOR, sel):
                t = el.text.strip()
                if len(t) > 5:
                    found.append((label, t))
        return found

    results = scrape(driver)
    for iframe in driver.find_elements(By.TAG_NAME, "iframe"):
        try:
            driver.switch_to.frame(iframe)
            results += scrape(driver)
        except Exception:
            pass
        finally:
            driver.switch_to.default_content()
    return results


def check_student_url(driver, wait, url, student_name, student_id):
    """
    Navigate to a student's submission and run ai_check.
    Returns:
        None             – no submission found / navigation error
        []               – submission found, nothing suspicious
        [(n, line, ...)] – suspicious lines
    """
    try:
        course_id, resource_type, resource_id = parse_canvas_url(url)
        if not course_id:
            return None

        if resource_type == "quizzes":
            sub_url = find_quiz_submission_url(
                driver, wait, course_id, resource_id, student_name, student_id
            )
            if sub_url is None:
                return None
            driver.get(sub_url)

        elif resource_type == "assignments":
            driver.get(get_speedgrader_url(course_id, resource_id, student_id))

        else:
            return None

        results = extract_code(driver, wait)
        if not results:
            return None

        full_code = "\n".join(text for _, text in results)
        return ai_check(full_code)

    except Exception as e:
        print(f"    [!] Error ({url_label(url)}): {e}")
        driver.switch_to.default_content()   # reset iframe state
        return None

# ---------------------------------------------------------------------------
# PDF generation
# ---------------------------------------------------------------------------

def build_pdf(all_results, urls, filename):
    """
    all_results : list of
        { 'name': str, 'id': str,
          'assignments': [ {'label': str, 'flagged': list|None}, ... ] }
    """
    doc    = SimpleDocTemplate(filename, pagesize=letter,
                               leftMargin=0.75*inch, rightMargin=0.75*inch,
                               topMargin=0.75*inch,  bottomMargin=0.75*inch)
    styles = getSampleStyleSheet()

    mono = ParagraphStyle(
        "mono", parent=styles["Normal"],
        fontName="Courier", fontSize=8, leading=10,
        leftIndent=12, spaceAfter=2,
    )
    flag_style = ParagraphStyle(
        "flag", parent=mono,
        textColor=colors.darkred,
    )
    heading_student = ParagraphStyle(
        "student", parent=styles["Heading2"],
        spaceAfter=4, spaceBefore=10,
    )
    heading_asgn = ParagraphStyle(
        "asgn", parent=styles["Heading3"],
        fontSize=10, spaceAfter=2, spaceBefore=6,
    )

    story = []

    # ---- Title ----
    ts = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
    story.append(Paragraph("AI Cheating Check Report", styles["Title"]))
    story.append(Paragraph(f"Generated: {ts}", styles["Normal"]))
    story.append(Paragraph(
        f"Students checked: {len(all_results)}  |  "
        f"Assignments checked: {len(urls)}",
        styles["Normal"]
    ))
    story.append(Spacer(1, 0.15*inch))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
    story.append(Spacer(1, 0.1*inch))

    # ---- Per-student sections ----
    for sr in all_results:
        story.append(Paragraph(
            f"{sr['name']}  <font size='9' color='grey'>(ID {sr['id']})</font>",
            heading_student
        ))

        for asgn in sr["assignments"]:
            story.append(Paragraph(asgn["label"], heading_asgn))

            if asgn["flagged"] is None:
                story.append(Paragraph("— No submission found", mono))

            elif len(asgn["flagged"]) == 0:
                story.append(Paragraph(
                    "<font color='green'>✓ Clean — no suspicious patterns</font>",
                    mono
                ))

            else:
                for lineno, line, reasons in asgn["flagged"]:
                    tag  = ", ".join(reasons)
                    text = escape(line)
                    story.append(Paragraph(
                        f"<b>Line {lineno:>3}  [{tag}]</b>  {text}",
                        flag_style
                    ))

        story.append(Spacer(1, 0.05*inch))
        story.append(HRFlowable(width="100%", thickness=0.5,
                                color=colors.lightgrey))

    doc.build(story)

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    students = get_all_students()
    urls     = load_urls()
    username, password = get_credentials()

    print(f"\n[*] {len(students)} students  |  {len(urls)} assignments")

    options = Options()
    # options.add_argument("--headless=new")
    driver = webdriver.Chrome(options=options)
    wait   = WebDriverWait(driver, 20)

    all_results = []

    try:
        print("[*] Logging in ...")
        login(driver, wait, username, password)

        for idx, student in enumerate(students, start=1):
            name = f"{student['First name']} {student['Last name']}"
            sid  = student["ID"]
            print(f"\n[{idx}/{len(students)}] {name} (ID {sid})")

            student_record = {"name": name, "id": sid, "assignments": []}

            for url in urls:
                label   = url_label(url)
                flagged = check_student_url(driver, wait, url, name, sid)

                if flagged is None:
                    status = "no submission"
                elif len(flagged) == 0:
                    status = "clean"
                else:
                    status = f"{len(flagged)} flag(s)"

                print(f"    {label}: {status}")
                student_record["assignments"].append(
                    {"label": label, "flagged": flagged}
                )

            all_results.append(student_record)

    finally:
        driver.quit()

    # Write PDF
    ts       = datetime.now().strftime("%Y%m%d_%H%M%S")
    pdf_name = f"ai_check_{ts}.pdf"
    print(f"\n[*] Writing {pdf_name} ...")
    build_pdf(all_results, urls, pdf_name)
    print(f"[+] Done — {pdf_name}")


if __name__ == "__main__":
    main()
