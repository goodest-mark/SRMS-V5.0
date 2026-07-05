# SRMS V5 Test Pack

This pack is intentionally mixed: valid rows, duplicates, boundary values, and invalid rows are included so the import paths can be exercised from multiple angles.

## Suggested order

1. Import students.
2. Import subjects.
3. Import enrollments.
4. Import requirements.
5. Import results after the relevant enrollments exist.

## Files

- `students_import.xlsx` - Mixed O-Level and A-Level student rows, plus duplicates and invalid records.
- `students_legacy_import.xlsx` - Legacy 7-column student layout for backward-compatibility testing.
- `subjects_import.xlsx` - Duplicate subjects, type changes, and cross-level subject coverage.
- `enrollments_import.xlsx` - Enrollment stress file with duplicates, cross-level rows, blanks, and unknown references.
- `requirements_import.xlsx` - Requirement rows with duplicates, blank quantities, long names, and punctuation.
- `mathematics_results.xlsx` - O-Level results for Mathematics with duplicate marks and invalid rows.
- `english_results.xlsx` - O-Level results for English with duplicate marks and invalid rows.
- `kiswahili_results.xlsx` - O-Level results for Kiswahili with duplicate marks and invalid rows.
- `biology_results.xlsx` - O-Level results for Biology with duplicate marks and invalid rows.
- `chemistry_results.xlsx` - O-Level results for Chemistry with duplicate marks and invalid rows.
- `physics_results.xlsx` - O-Level results for Physics with duplicate marks and invalid rows.
- `history_results.xlsx` - O-Level results for History with duplicate marks and invalid rows.
- `geography_results.xlsx` - O-Level results for Geography with duplicate marks and invalid rows.
- `civics_results.xlsx` - O-Level results for Civics with duplicate marks and invalid rows.
- `history_al_results.xlsx` - A-Level results for History with duplicate marks and invalid rows.
- `geography_al_results.xlsx` - A-Level results for Geography with duplicate marks and invalid rows.
- `economics_al_results.xlsx` - A-Level results for Economics with duplicate marks and invalid rows.
- `general_studies_al_results.xlsx` - A-Level results for General Studies with duplicate marks and invalid rows.
