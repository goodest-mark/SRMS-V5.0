# SRMS V5

School Report Management System (SRMS) is a desktop-based application designed to help secondary schools manage students, examinations, grading, report cards, rankings, and academic records efficiently.

Repository: `https://github.com/fizzoh/SRMSV5.0.git`

## Features

### Student Management

* Student registration
* Student profile management
* Student status tracking
* Enrollment management

### Teacher Management

* Teacher profiles
* Subject assignments
* Class assignments

### Academic Management

* Academic years
* Terms and examinations
* Subject management
* Class management

### Results Management

* Marks entry
* Excel results import
* Ranking engine
* Division calculation
* Subject performance analysis

### Reports

* Report cards
* Report books
* Broadsheets
* PDF export

## Technology Stack

* Python
* PySide6
* SQLite
* Pandas
* OpenPyXL
* ReportLab

## Installation

```bash
git clone https://github.com/fizzoh/SRMSV5.0.git

cd SRMSV5.0

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt

python app.py
```

## Screenshots

### Dashboard

![Dashboard](screenshots/dashboard.png)

### Students Module

![Students Module](screenshots/students.png)

### Results Dashboard

![Results Dashboard](screenshots/results.png)


## Project Status

Current Version: V5

Development Status:

* Core modules implemented with active student, exam, grading, and report generation workflows
* Manual backup export/import supported; pre-operation backups available
* Auto backup setting exists in Settings, but scheduled daily/weekly backup execution is not yet implemented
* Report book and broadsheet summary preview controls are available
* Ranking engine restricts output to enrolled subjects and enforces NECTA-style eligibility rules
* Advanced features remaining: audit trail, smart comments, checklist-style requirements, full school export package
* UI/UX polish ongoing

Current Completion Estimate: ~75%

## Contributing

Contributions, suggestions, bug reports, and pull requests are welcome.

## License

Open Source

