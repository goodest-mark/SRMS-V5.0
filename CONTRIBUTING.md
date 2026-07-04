# SRMS V5 Contributing

Repository: `https://github.com/fizzoh/SRMSV5.0.git`

# SRMS V5 Development Roadmap

## Current Project Status

| Area                | Status |
| ------------------- | ------ |
| Database            | 90%    |
| Students Module     | 90%    |
| Teachers Module     | 85%    |
| Subjects Module     | 85%    |
| Academics Module    | 85%    |
| Examinations Module | 85%    |
| Results Entry       | 85%    |
| Ranking Engine      | 90%    |
| Broadsheet Reports  | 90%    |
| Report Card Engine  | 65%    |
| Dashboard UI        | 70%    |
| Settings            | 85%    |
| Security            | 60%    |

### Overall Completion Estimate

**Approximately 75% Complete**

---

# Sprint 1 – Critical Release Blockers

These issues must be completed before SRMS V5 can be considered production-ready.

## SRMS-001: Stabilize Report Card Layout Engine

### Objective

Ensure all report cards fit correctly on a single landscape page.

### Issues

* Layout breaks with many subjects.
* Academic Summary placement needs improvement.
* Requirements section needs redesign.
* Comments section requires proper alignment.
* Signature section needs professional layout.
* Support both O-Level and A-Level report formats.

### Priority

🔴 High

---

## SRMS-002: Harden PDF Generation Engine

### Objective

Improve PDF generation reliability.

### Issues

* Prevent NameError exceptions.
* Prevent NoneType errors.
* Handle missing data safely.
* Handle missing logo and school information.
* Improve exception handling and error reporting.

### Priority

🔴 High

---

## SRMS-003: Validate NECTA Ranking Rules

### Objective

Ensure ranking calculations follow NECTA standards.

### Validation Areas

* Student Position
* Gender Position
* Division Calculation
* Points Calculation
* Best Subject Selection

### Priority

🔴 High

---

## SRMS-004: Restrict Results to Enrolled Subjects

### Objective

Display only subjects officially enrolled by a student.

### Examples

* HKL students should not display Physics.
* PCM students should not display History.
* O-Level students should display only assigned subjects.

### Priority

🔴 High

---

# Sprint 2 – Performance and Stability

## SRMS-005: Investigate Memory and Process Crashes

### Objective

Identify causes of application termination.

### Areas to Investigate

* Recursive EventBus calls
* Infinite refresh loops
* Heavy PDF operations
* Large dataset loading

### Priority

🟠 Medium

---

## SRMS-006: Optimize Dashboard Refresh Logic

### Objective

Improve dashboard performance.

### Improvements

* Lazy loading
* Background loading
* Reduce unnecessary refresh operations

### Priority

🟠 Medium

---

## SRMS-007: Add PDF Generation Progress Indicator

### Objective

Show generation progress to users.

### Features

* Progress percentage
* Progress bar
* Completion notification

*Status: Implemented for report book generation and backup export workflows.*

### Priority

🟠 Medium

---

# Sprint 3 – Professional Features

## SRMS-008: Add Report Preview Window

### Objective

Allow users to preview reports before PDF generation.

*Status: Summary preview functionality exists for report book and broadsheet modules, but full PDF preview is not yet implemented.*

### Priority

🟠 Medium

---

## SRMS-009: Implement Smart Comment System

### Features

* Automatic comments
* Manual comments
* Comment templates

### Examples

* Excellent Performance
* Good Progress
* Needs Improvement

*Status: Not implemented; report cards include comment placeholders but lack comment automation or templates.*

### Priority

🟠 Medium

---

## SRMS-010: Redesign Requirements Module

### Objective

Convert requirements into checklist format.

*Status: Requirements import/export and class-based requirement entry are implemented, but checklist-style UI remains pending.*

### Priority

🟠 Medium

---

# Sprint 4 – Administration and Security

## SRMS-011: Add Audit Trail System

### Track Activities

* Student Added
* Student Edited
* Marks Imported
* Results Reprocessed
* Report Generated

*Status: No audit trail tables or logging workflow are present in the current codebase.*

### Priority

🟢 Low

---

## SRMS-012: Add Automatic Backup System

### Backup Types

* Daily Backup
* Weekly Backup
* Before Major Operations

*Status: Manual backup export/import and pre-operation backups are implemented; scheduled backups are pending.*

### Priority

🟢 Low

---

## SRMS-013: Export Complete School Package

### Export Contents

* Database
* School Logo
* School Stamp
* Settings
* Requirements

*Status: No dedicated school export package workflow is currently implemented. A test pack generator exists but it does not export live school data.*

### Output

Single ZIP Package

### Priority

🟢 Low

---

# Sprint 5 – User Experience Improvements

## SRMS-014: Simplify Dashboard Navigation

### Proposed Modules

* Dashboard
* Students
* Academics
* Examinations
* Results
* Reports
* Settings

### Priority

🟡 Medium

---

## SRMS-015: Improve Sidebar Experience

### Improvements

* Collapse animation
* Better icons
* Improved active states

### Priority

🟡 Medium

---

## SRMS-016: Improve Small Screen Support

### Target Devices

* Low-resolution monitors
* Small laptop screens

### Priority

🟡 Medium

---

## SRMS-017: Add Empty State Components

### Examples

* No Students Found
* No Examinations Found
* No Results Found

### Priority

🟡 Medium
