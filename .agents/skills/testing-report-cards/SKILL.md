---
name: testing-srms-report-cards
description: Test SRMS report card PDF generation end-to-end. Use when verifying report_card_v5.py changes, ranking_engine.py fixes, or PDF layout modifications.
---

# Testing SRMS Report Card Generation

## Overview
SRMS is a PySide6 desktop app for school result management. The report card generation (`report_card_v5.py`) can be tested without the full GUI since the entry function `generate_report_book(parent, exam_id, class_name, save_path)` accepts `parent=None`.

## Setup

### Dependencies
```bash
cd <repo_root>
pip install PySide6 reportlab openpyxl
```

### Database Seeding
The app uses SQLite (`srms.db` in the working directory). To test:
1. Delete any existing `srms.db`
2. Call `from database import init_db; init_db()` — this creates all tables with default data (academic year 2026, terms, exams, division rules, system settings)
3. Seed additional test data: school_profile, subjects, students, enrollments, results, requirements

### Key Tables for Report Cards
- `school_profile`: school_name, school_motto, school_address, school_phone, school_email, school_website, head_teacher, academic_master, school_logo, school_stamp, watermark_text
- `subjects`: subject_name, subject_short_name, level (O_LEVEL/A_LEVEL), subject_type (COUNTED/PRINCIPAL)
- `students`: admission_no, full_name, gender, class, stream, level
- `enrollments`: admission_no, subject_name, academic_year_id, term_id
- `results`: admission_no, subject_name, marks, exam_id
- `requirements`: academic_year_id, term_id, level, class_name, item_name, quantity
- `system_settings`: key-value pairs including o_level_counted, a_level_principal, show_requirements, show_watermark, show_logo
- `division_rules`: level, division (I-IV, 0), min_points, max_points

### Generating a PDF
```python
from report_card_v5 import generate_report_book
success, message = generate_report_book(None, exam_id, "Form IV", "/tmp/test_report.pdf")
```

### Visual Verification
Open the PDF in Chrome: `file:///tmp/test_report.pdf`

## Code Architecture
- `report_book_page.py` — GUI page that triggers generation (imports `report_card_v5` as `report_book_pdf`)
- `report_card_v5.py` — Main PDF generation (uses ReportLab)
- `report_book_pdf.py` — Alternative report book PDF generation
- `ranking_engine.py` — Computes student scores, positions, divisions
- `grade_utils.py` — Grade/points mapping (O-Level: A=1, B=2, C=3, D=4, F=5; A-Level has extra S=6 grade)
- `division_utils.py` — Division lookup from division_rules table
- `settings_page.py` — `get_setting(key, default)` reads from system_settings table
- `db_utils.py` — Shared `get_cursor()` context manager for safe DB access
- `database.py` — `connect()` returns raw connection; `init_db()` creates schema + seeds defaults

## Testing Error Handling

### Approach
Error handling in UI modules (students_page.py, results_page.py, school_profile.py, main_window.py) uses QMessageBox dialogs that require a running PySide6 event loop. For headless testing:
- **Runtime tests**: Call `generate_report_book()` and `report_book_pdf.generate_report_book()` with invalid save paths to verify error messages are returned (not swallowed)
- **Static verification**: Check source code for anti-patterns like bare `except Exception:` (without `as e`) or `except: pass`

### Key Findings
- ReportLab 5.0.0's `Image()` constructor does **NOT** validate file paths at construction time — errors only surface during `doc.build()`. So the logo warning path in `_build_header` cannot be triggered by simply providing a bad logo path. The `Image()` object is created successfully and the exception only occurs later during PDF rendering.
- Both `report_card_v5.py` and `report_book_pdf.py` use `try/finally` to ensure `conn.close()` is called. Test by calling with an invalid save path (e.g. `/proc/nonexistent/test.pdf`) — should return `(False, "[Errno 2] No such file...")`.
- GUI error dialogs (QMessageBox) in students_page, results_page, school_profile, main_window can only be verified via static code analysis in headless mode.

### Running Tests
```bash
# Existing unit tests
python -m pytest tests/ -v

# Error handling verification (creates temp DB, runs assertions, cleans up)
# Write a script that seeds data and calls generate_report_book with bad inputs
```

## Key Test Scenarios

### 1. Full Report Card Generation
- Seed 5+ students with 7+ COUNTED subjects for O-Level
- Verify PDF generates without errors and file size > 10KB
- Open in Chrome and verify all sections render

### 2. Ranking Engine Settings
- Change `o_level_counted` setting and verify ranking uses the new value
- Verify points are calculated from the best N subjects (sorted by points ascending)

### 3. Null Safety
- Delete a student from `students` table while their results still exist
- Verify both `report_card_v5.py` and `report_book_pdf.py` handle this without crashing

### 4. Edge Cases
- Student with fewer subjects than required — should show as INCOMPLETE
- Missing school_profile — verify graceful fallback
- Missing subjects short names — verify column headers still render

### 5. Connection Leak Testing
- Call `generate_report_book` with invalid save path (e.g. `/proc/nonexistent/test.pdf`)
- Should return `(False, "<error message>")` without leaking DB connections
- Do the same for `report_book_pdf.generate_report_book`

## Common Issues
- Each student may generate 2 pages (landscape A4 overflows with rich content)
- TERM field may display just the number if term_name format varies
- `SystemState.level` defaults to "O_LEVEL" — set it before calling ranking for A-Level tests
- The `watermark.py` module uses hardcoded canvas positioning (300, 400) — watermark position may vary on different page sizes
- The repo path is `/home/ubuntu/repos/SRMS` (not `/home/ubuntu/SRMS`)
- The existing test suite has a pre-existing failure in `test_system_security_default_passcode` (hash mismatch due to random salt in PBKDF2) — this is unrelated to report card changes
- No CI is configured on this repo — tests must be run locally

## Devin Secrets Needed
None — this is a local SQLite application with no external dependencies or API keys.
