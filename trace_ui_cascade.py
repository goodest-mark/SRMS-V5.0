"""
Reproduces the exact filter cascade historical_results_page.py runs
(year -> term -> exam -> class -> stream), without opening the GUI,
so we can see exactly what values it actually passes to compute_student_scores.

Run:
    python trace_ui_cascade.py
"""
import sys
from PySide6.QtWidgets import QApplication, QComboBox

app = QApplication.instance() or QApplication(sys.argv)

import combo_loaders
from class_utils import get_classes
from system_state import SystemState
from ranking_engine import compute_student_scores

level = SystemState.get_level()
print(f"SystemState.get_level() -> {repr(level)}\n")

year_box = QComboBox()
term_box = QComboBox()
exam_box = QComboBox()
class_box = QComboBox()
stream_box = QComboBox()

# ---- Year ----
combo_loaders.load_years(year_box)
print("Year combo items:")
for i in range(year_box.count()):
    print(f"  [{i}] text={repr(year_box.itemText(i))} data={repr(year_box.itemData(i))}")
year_id = year_box.currentData()
print(f"-> currentData: {repr(year_id)}\n")

# ---- Term ----
combo_loaders.load_terms(term_box, year_id)
print("Term combo items:")
for i in range(term_box.count()):
    print(f"  [{i}] text={repr(term_box.itemText(i))} data={repr(term_box.itemData(i))}")
term_id = term_box.currentData()
print(f"-> currentData: {repr(term_id)}\n")

# ---- Exam (this is the "Reports"/historical exam list, ALL statuses shown) ----
combo_loaders.load_all_exams_for_report(exam_box, year_id=year_id, term_id=term_id, level=level)
print("Exam combo items:")
for i in range(exam_box.count()):
    print(f"  [{i}] text={repr(exam_box.itemText(i))} data={repr(exam_box.itemData(i))}")
exam_id = exam_box.currentData()
print(f"-> currentData: {repr(exam_id)}\n")

# ---- Class ----
class_box.addItems(get_classes())
print("Class combo items:")
for i in range(class_box.count()):
    print(f"  [{i}] text={repr(class_box.itemText(i))}")
class_name = class_box.currentText().strip()
print(f"-> currentText (stripped): {repr(class_name)}\n")

# ---- Stream ----
combo_loaders.load_streams(stream_box, class_name=class_name, exam_id=exam_id)
print("Stream combo items:")
for i in range(stream_box.count()):
    print(f"  [{i}] text={repr(stream_box.itemText(i))} data={repr(stream_box.itemData(i))}")
stream = stream_box.currentData()
print(f"-> currentData: {repr(stream)}\n")

print("=" * 60)
print(f"Final context that would be sent to set_history_context:")
print(f"  exam_id={repr(exam_id)}, class_name={repr(class_name)}, stream={repr(stream)}, level={repr(level)}")
print("=" * 60)

result = compute_student_scores(level, exam_id=exam_id, class_name=class_name, stream=stream)
print(f"\ncompute_student_scores(...) with THESE exact values -> {len(result)} students")
if not result:
    print("!! EMPTY with the UI's real values, even though the direct test worked.")
    print("!! Compare the repr() values above against exam_id=1, class_name='Form I', level='O_LEVEL' to spot the difference.")
