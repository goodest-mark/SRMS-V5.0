import os
print('Running headless PDF export test...')
# Monkeypatch QFileDialog and QMessageBox to avoid GUI
import PySide6.QtWidgets as QtW
QtW.QFileDialog.getSaveFileName = lambda parent, title, fname, filter: ('/tmp/test_broadsheet.pdf', filter)
QtW.QMessageBox.information = lambda parent, title, msg: print('INFO:', msg)
QtW.QMessageBox.critical = lambda parent, title, msg: print('ERROR:', msg)

# Prepare minimal sample data
from datetime import datetime
from progress_dialog import ProgressDialog
from broadsheet_export import to_pdf
from progress_dialog import ProgressDialog

subjects = ['Mathematics', 'Biology', 'Chemistry']
rows = []
for i in range(1, 16):
    marks = {s: (60 - i if s == 'Mathematics' else 50 + i) for s in subjects}
    total = sum(marks.values())
    avg = round(total / len(subjects), 2)
    rows.append({
        'Position': i,
        'Admission No': f'ADM{i:03}',
        'Student Name': f'Student {i}',
        'Gender': 'Male' if i % 2 == 0 else 'Female',
        'marks': marks,
        'Total': total,
        'Average': avg,
        'Points': max(1, 100 - int(avg)),
        'Division': 'I' if avg>=70 else ('II' if avg>=60 else ('III' if avg>=50 else '0'))
    })

meta = {
    'year': '2025/2026',
    'term': 'Term 1',
    'exam': 'Midterm',
    'class': 'Form 1A',
    'level': 'Senior',
    'school_profile': {
        'school_name': 'Example Academy',
        'school_address': '123 School Rd',
        'school_phone': '+123456789',
        'school_email': 'info@example.ac',
        'school_logo': '',
        'watermark_text': 'CONFIDENTIAL'
    },
    'generated_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
}

class_perf = {'total_students': len(rows), 'class_average': round(sum(r['Average'] for r in rows)/len(rows),2),
              'highest_average': max(r['Average'] for r in rows), 'lowest_average': min(r['Average'] for r in rows),
              'pass_count': sum(1 for r in rows if r['Division'] in ['I','II','III','IV']),
              'fail_count': sum(1 for r in rows if r['Division']=='0'), 'pass_rate':0, 'fail_rate':0}
if class_perf['total_students']>0:
    class_perf['pass_rate'] = round(class_perf['pass_count']/class_perf['total_students']*100,2)
    class_perf['fail_rate'] = round(class_perf['fail_count']/class_perf['total_students']*100,2)

male = sum(1 for r in rows if r['Gender']=='Male')
female = sum(1 for r in rows if r['Gender']=='Female')

division_summary = {'I': sum(1 for r in rows if r['Division']=='I'), 'II': sum(1 for r in rows if r['Division']=='II'),
                    'III': sum(1 for r in rows if r['Division']=='III'), 'IV':0, '0': sum(1 for r in rows if r['Division']=='0'), 'Incomplete':0}

# Subject performance
subject_performance = {}
for s in subjects:
    marks_list = [r['marks'][s] for r in rows if isinstance(r['marks'].get(s), int)]
    avg = round(sum(marks_list)/len(marks_list),2) if marks_list else 0
    passes = sum(1 for m in marks_list if m>=50)
    fails = sum(1 for m in marks_list if m<50)
    subject_performance[s] = {'average': avg, 'passes': passes, 'fails': fails}

subject_ranking = sorted(subject_performance.items(), key=lambda it: it[1]['average'], reverse=True)

data = {
    'subjects': subjects,
    'rows': rows,
    'meta': meta,
    'class_performance': class_perf,
    'gender_summary': {'Male': male, 'Female': female, 'Total': male+female},
    'division_summary': division_summary,
    'top_students': rows[:10],
    'bottom_students': sorted(rows, key=lambda x: x['Average'])[:10],
    'subject_performance': subject_performance,
    'subject_ranking': subject_ranking,
    'best_subject': subject_ranking[0][0],
    'worst_subject': subject_ranking[-1][0],
    'max_avg': subject_ranking[0][1]['average'],
    'min_avg': subject_ranking[-1][1]['average'],
    'settings': {'show_gender_summary': True, 'show_subject_ranking': True, 'show_logo': False, 'show_watermark': True}
}

# Run export
try:
    to_pdf(None, data)
    print('PDF written to /tmp/test_broadsheet.pdf')
except Exception as e:
    print('Export failed:', e)
