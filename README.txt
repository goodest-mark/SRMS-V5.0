===============================================================================
SRMS-V5.0 – Student Results Management System
===============================================================================

A modern desktop application for managing student results, rankings, broadsheets,
remarks, and report books. Built with PySide6 (Qt for Python) and SQLite.


FEATURES
===============================================================================

Core Modules:

  Dashboard    – Overview of key metrics and quick access to all modules
  Students     – Manage student profiles, enrollment, and class assignments
  Academics    – Subject configuration, grading rules, and division settings
  Exams        – Create and manage examinations across terms and years
  Results      – Enter and manage student marks per subject
  Ranking      – Detailed student ranking with positions, points, and divisions
  Broadsheet   – Scrollable full‑view with analytics, top/bottom students,
                 subject performance, and full results table.
                 Export to Excel and PDF.
  Remarks      – Add and save teacher, headteacher, academic master, and
                 discipline master remarks with async loading.
  Reports      – Generate PDF report books for any exam/class.

Key Capabilities:

  - Unified Filter Bar – One central filter (Year, Term, Exam, Class) controls all views
  - Async Loading – Non-blocking background threads for ranking and remarks
  - Export – Broadsheet export to Excel (.xlsx) and PDF
  - Report Books – Generate individual student report cards as PDF
  - Grading Engine – Configurable grade rules, points, and division calculations
  - SQLite Database – Lightweight, no server required


TECHNOLOGY STACK
===============================================================================

  Python 3.8+
  PySide6 – Qt for Python GUI framework
  SQLite – Embedded database
  Pandas – Data manipulation and Excel export
  OpenPyXL – Excel file generation
  ReportLab – PDF generation


REQUIREMENTS
===============================================================================

  PySide6
  pandas>=2.2.0
  openpyxl
  reportlab
  pytest
  pypdf


INSTALLATION & SETUP
===============================================================================

1. Clone the repository:
   git clone https://github.com/goodest-mark/SRMS-V5.0.git
   cd SRMS-V5.0

2. Create a virtual environment (recommended):
   python -m venv venv
   source venv/bin/activate      # Linux / macOS
   venv\Scripts\activate         # Windows

3. Install dependencies:
   pip install -r requirements.txt

4. Run the application:
   python app.py


BUILDING A STANDALONE EXECUTABLE
===============================================================================

Windows release packaging is intentionally kept separate from school data. The
installed app stores its SQLite database under the current user's application
data folder, while a source checkout uses `srms.db` in the repository. Do not
ship a live school database, backups, virtual environments, or development
files to users.


PROJECT STRUCTURE
===============================================================================

SRMS-V5.0/
├── app.py                     # Main entry point
├── ui/
│   ├── pages/                 # Individual page widgets
│   │   ├── historical_results_page.py   # Unified filter + stacked views
│   │   ├── broadsheet_page.py
│   │   ├── remarks_page.py
│   │   ├── report_book_page.py
│   │   └── ranking.py
│   ├── main_window.py
│   ├── cards.py
│   └── ...
├── srms.db                    # Local development/sample SQLite database
├── requirements.txt
└── README.txt


TESTING
===============================================================================

Run tests with pytest:
   pytest tests/


CONTRIBUTING
===============================================================================

1. Fork the repository
2. Create a feature branch (git checkout -b feature/amazing-feature)
3. Commit your changes (git commit -m 'Add amazing feature')
4. Push to the branch (git push origin feature/amazing-feature)
5. Open a Pull Request


LICENSE
===============================================================================

This project is distributed under the MIT License. See the LICENSE file for
full terms and conditions.


DEVELOPER
===============================================================================
Issa Twalibu – https://github.com/goodest-mark


ACKNOWLEDGEMENTS
===============================================================================

Built with PySide6 (https://doc.qt.io/qtforpython/)
Icons from Feather Icons (https://feathericons.com/)
