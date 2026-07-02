# SRMS V5 Roadmap

## Current Progress

Estimated Completion: 75%

---

# Phase 1 – Core System Stabilization

## High Priority

### SRMS-001

Stabilize Report Card Layout Engine

### SRMS-002

Harden PDF Generation Engine

### SRMS-003

Validate NECTA Ranking Rules

* Implemented in the ranking engine with eligibility rules and division mapping.

### SRMS-004

Restrict Results to Enrolled Subjects

* Implemented by filtering results against official enrollments for the selected exam and year.

### SRMS-005

Investigate Memory and Process Crashes

Goal:
Deliver a stable and reliable report generation system.

---

# Phase 2 – Performance Improvements

### Dashboard Optimization

* Lazy loading
* Faster refresh operations
* Reduced database queries

### PDF Progress Tracking

* Progress bar
* Percentage indicator
* Background generation

*Status: Progress tracking is implemented for report book generation and backup export workflows.*

Goal:
Improve responsiveness and user experience.

---

# Phase 3 – Professional Features

### Report Preview

Preview reports before PDF export.

*Status: Summary preview functionality exists for report book and broadsheet modules.*

### Smart Comment System

* Automatic comments
* Manual comments
* Comment templates

*Status: Report cards include comment placeholders, but automated comments/templates are not implemented.*

### Requirements Management

* Template imports
* Student-specific requirements
* Checklist support

*Status: Template import/export and class-specific requirement entry are implemented. Checklist-style UI is pending.*

Goal:
Improve academic workflow.

---

# Phase 4 – Security and Administration

### Audit Trail

Track:

* Student Added
* Student Updated
* Marks Imported
* Results Reprocessed
* Reports Generated

### Automatic Backup

* Daily backups
* Weekly backups
* Pre-operation backups

*Status: Manual export/import and pre-operation backups are available. Scheduled daily/weekly backups remain pending.*

### School Export Package

Export:

* Database
* Logo
* Stamp
* Settings
* Requirements

*Status: No dedicated school export package workflow is currently implemented.*

Goal:
Improve data protection and portability.

---

# Phase 5 – User Experience

### Dashboard Simplification

Modules:

* Dashboard
* Students
* Academics
* Examinations
* Results
* Reports
* Settings

### Sidebar Improvements

* Better navigation
* Better icons
* Active states
* Collapse animation

### Empty States

* No Students Found
* No Results Found
* No Examinations Found

Goal:
Provide a cleaner and more modern interface.

---

# Long-Term Vision

SRMS aims to become a comprehensive school academic management platform for secondary schools with:

* Student management
* Examination management
* Report generation
* Academic analytics
* School data portability
* Professional reporting

Built with:

* Python
* PySide6
* SQLite
* ReportLab

