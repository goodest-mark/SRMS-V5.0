import os
import tempfile
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
    PageBreak, Image, KeepInFrame
)
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from database import connect
from settings_page import get_setting
from watermark import draw_watermark
from ranking_engine import compute_student_scores
from grade_utils import get_grade
from remarks_utils import get_default_remark, get_headteacher_remark, get_academic_master_remark, get_discipline_master_remark
from ui_helpers import get_subject_short_name

# ============================================================
# STRICT A4 PORTRAIT LAYOUT (210mm x 297mm)
# ============================================================
NAVY = colors.HexColor('#1B3A5C')
NAVY_LIGHT = colors.HexColor('#E8EDF2')
LIGHT_BG = colors.HexColor('#F8FAFC')
GRID_COLOR = colors.HexColor('#D0D5DD')
WHITE = colors.white
ACCENT = colors.HexColor('#2E7D32')
GOLD = colors.HexColor('#C9A227')

GREEN_BG = colors.HexColor('#EAF3DE')
GREEN_TX = colors.HexColor('#27500A')
AMBER_BG = colors.HexColor('#FAEEDA')
AMBER_TX = colors.HexColor('#854F0B')
RED_BG = colors.HexColor('#FCEBEB')
RED_TX = colors.HexColor('#791F1F')


def _grade_band(grade):
    """Map a grade letter to a (background, text) color pair for chips/pills."""
    g = (grade or '').strip().upper()
    if g in ('A', 'B'):
        return GREEN_BG, GREEN_TX
    if g == 'C':
        return AMBER_BG, AMBER_TX
    if g in ('D', 'E', 'F'):
        return RED_BG, RED_TX
    return NAVY_LIGHT, NAVY


def _status_color(status):
    s = (status or '').strip().upper()
    if s in ('READY', 'PASS', 'COMPLETE'):
        return GREEN_TX
    if s in ('PENDING', 'INCOMPLETE'):
        return AMBER_TX
    return RED_TX

PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN = 8
USABLE_WIDTH = PAGE_WIDTH - (MARGIN * 2)
USABLE_HEIGHT = PAGE_HEIGHT - (MARGIN * 2)

_styles_cache = {}
_student_styles_cache = {}


def _numeric_or_zero(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _safe_image(path, width, height):
    if not path or not os.path.exists(path):
        return None
    try:
        return Image(path, width=width, height=height)
    except Exception:
        return None


def _load_school_profile_assets(cur):
    cur.execute("""
        SELECT school_name, school_motto, school_address, school_phone,
               school_email, school_logo, school_stamp, head_teacher,
               academic_master, discipline_master,
               head_teacher_signature, academic_master_signature,
               discipline_master_signature,
               watermark_text, school_website,
               head_teacher_signature_enabled, academic_master_signature_enabled,
               discipline_master_signature_enabled
        FROM school_profile
        LIMIT 1
    """)
    profile = cur.fetchone()
    head_signature_enabled = bool(profile and len(profile) > 15 and profile[15])
    academic_signature_enabled = bool(profile and len(profile) > 16 and profile[16])
    discipline_signature_enabled = bool(profile and len(profile) > 17 and profile[17])
    return {
        "school_name": profile[0] if profile else "SCHOOL MANAGEMENT SYSTEM",
        "school_motto": profile[1] if profile and profile[1] else "",
        "school_address": profile[2] if profile else "-",
        "school_phone": profile[3] if profile else "",
        "school_email": profile[4] if profile else "",
        "school_logo": profile[5] if profile and profile[5] and os.path.exists(profile[5]) else None,
        "school_stamp": profile[6] if profile and profile[6] and os.path.exists(profile[6]) else None,
        "head_teacher": profile[7] if profile else "",
        "academic_master": profile[8] if profile else "",
        "discipline_master": profile[9] if profile else "",
        "head_teacher_signature": profile[10] if head_signature_enabled and profile and profile[10] and os.path.exists(profile[10]) else None,
        "academic_master_signature": profile[11] if academic_signature_enabled and profile and profile[11] and os.path.exists(profile[11]) else None,
        "discipline_master_signature": profile[12] if discipline_signature_enabled and profile and profile[12] and os.path.exists(profile[12]) else None,
        "watermark_text": profile[13] if profile and profile[13] else "CONFIDENTIAL",
        "school_website": profile[14] if profile and len(profile) > 14 and profile[14] else "",
    }


def _resolve_historical_class(cur, admission_no, exam_id, fallback_class):
    cur.execute("""
        SELECT class_name
        FROM results
        WHERE admission_no = ? AND exam_id = ? AND class_name IS NOT NULL AND class_name <> ''
        ORDER BY id DESC
        LIMIT 1
    """, (admission_no, exam_id))
    row = cur.fetchone()
    if row and row[0]:
        return row[0]
    return fallback_class


def list_student_report_exams(admission_no, level):
    conn = connect()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT
                e.id,
                e.exam_name,
                t.term_name,
                y.year_name,
                e.status,
                COUNT(r.id) AS subject_count,
                ROUND(AVG(r.marks), 2) AS average_mark
            FROM results r
            JOIN exams e ON e.id = r.exam_id
            JOIN terms t ON t.id = e.term_id
            JOIN academic_years y ON y.id = t.academic_year_id
            WHERE r.admission_no = ?
              AND e.level = ?
            GROUP BY e.id, e.exam_name, t.term_name, y.year_name, e.status
            ORDER BY
              y.year_name DESC,
              t.id DESC,
              CASE e.status
                WHEN 'OPEN' THEN 0
                WHEN 'CLOSED' THEN 1
                WHEN 'COMPLETED' THEN 2
                ELSE 3
              END,
              e.id DESC
        """, (admission_no, level))
        return [
            {
                "exam_id": exam_id,
                "exam_name": exam_name,
                "term_name": term_name,
                "year_name": year_name,
                "status": status,
                "subject_count": subject_count,
                "average": average_mark,
            }
            for (
                exam_id,
                exam_name,
                term_name,
                year_name,
                status,
                subject_count,
                average_mark,
            ) in cur.fetchall()
        ]
    finally:
        conn.close()


def _get_student_styles():
    if _student_styles_cache:
        return _student_styles_cache

    _student_styles_cache['title'] = ParagraphStyle(
        'student_title', fontName='Times-Bold', fontSize=21,
        alignment=TA_CENTER, leading=24, textColor=NAVY)
    _student_styles_cache['motto'] = ParagraphStyle(
        'student_motto', fontName='Times-Italic', fontSize=9,
        alignment=TA_CENTER, leading=11, textColor=NAVY)
    _student_styles_cache['student_name'] = ParagraphStyle(
        'student_name_banner', fontName='Times-Bold', fontSize=17,
        alignment=TA_CENTER, leading=20, textColor=NAVY)
    _student_styles_cache['credential_line'] = ParagraphStyle(
        'credential_line', fontName='Helvetica', fontSize=8.5,
        alignment=TA_CENTER, leading=11, textColor=colors.HexColor('#5B6472'))
    _student_styles_cache['credential_tag'] = ParagraphStyle(
        'credential_tag', fontName='Helvetica', fontSize=7.5,
        alignment=TA_CENTER, leading=9.5, textColor=NAVY)
    _student_styles_cache['credential_tag_b'] = ParagraphStyle(
        'credential_tag_b', fontName='Helvetica-Bold', fontSize=8.5,
        alignment=TA_CENTER, leading=10.5, textColor=NAVY)
    _student_styles_cache['section_underline'] = ParagraphStyle(
        'section_underline', fontName='Helvetica-Bold', fontSize=10,
        alignment=TA_LEFT, leading=12, textColor=NAVY)
    _student_styles_cache['srms_tag'] = ParagraphStyle(
        'srms_tag', fontName='Helvetica', fontSize=6.5,
        alignment=TA_CENTER, leading=8, textColor=colors.HexColor('#B4B2A9'))
    _student_styles_cache['comment_role'] = ParagraphStyle(
        'comment_role', fontName='Helvetica-Bold', fontSize=11,
        alignment=TA_LEFT, leading=13, textColor=NAVY)
    _student_styles_cache['comment_quote'] = ParagraphStyle(
        'comment_quote', fontName='Helvetica-Oblique', fontSize=11,
        alignment=TA_LEFT, leading=15, textColor=colors.HexColor('#333333'))
    _student_styles_cache['contact'] = ParagraphStyle(
        'student_contact', fontName='Helvetica', fontSize=7.5,
        alignment=TA_CENTER, leading=9.5)
    _student_styles_cache['section_hdr'] = ParagraphStyle(
        'student_section_hdr', fontName='Helvetica-Bold', fontSize=8,
        alignment=TA_LEFT, leading=9.5, textColor=WHITE)
    _student_styles_cache['label'] = ParagraphStyle(
        'student_label', fontName='Helvetica-Bold', fontSize=11,
        alignment=TA_LEFT, leading=13, textColor=NAVY)
    _student_styles_cache['value'] = ParagraphStyle(
        'student_value', fontName='Helvetica', fontSize=7.2,
        alignment=TA_LEFT, leading=8.5)
    _student_styles_cache['tiny'] = ParagraphStyle(
        'student_tiny', fontName='Helvetica', fontSize=6.5,
        alignment=TA_CENTER, leading=7.5)
    _student_styles_cache['tiny_left'] = ParagraphStyle(
        'student_tiny_left', fontName='Helvetica', fontSize=6.5,
        alignment=TA_LEFT, leading=7.5)
    _student_styles_cache['req_item'] = ParagraphStyle(
        'req_item', fontName='Helvetica', fontSize=11,
        alignment=TA_LEFT, leading=13)
    _student_styles_cache['tiny_b'] = ParagraphStyle(
        'student_tiny_b', fontName='Helvetica-Bold', fontSize=6.5,
        alignment=TA_CENTER, leading=7.5)
    _student_styles_cache['contact_value'] = ParagraphStyle(
        'contact_value', parent=_student_styles_cache['tiny'],
        fontSize=6.5, leading=7.5, wordWrap='CJK'
    )
    _student_styles_cache['summary_label'] = ParagraphStyle(
        'student_summary_label', fontName='Helvetica-Bold', fontSize=7,
        alignment=TA_CENTER, leading=8, textColor=NAVY)
    _student_styles_cache['summary_value'] = ParagraphStyle(
        'student_summary_value', fontName='Helvetica-Bold', fontSize=11.5,
        alignment=TA_CENTER, leading=12.5)
    _student_styles_cache['summary_small'] = ParagraphStyle(
        'student_summary_small', fontName='Helvetica', fontSize=7,
        alignment=TA_CENTER, leading=8)
    _student_styles_cache['table_head'] = ParagraphStyle(
        'student_table_head', fontName='Helvetica-Bold', fontSize=11,
        alignment=TA_CENTER, leading=13)
    _student_styles_cache['table_body'] = ParagraphStyle(
        'student_table_body', fontName='Helvetica', fontSize=11,
        alignment=TA_CENTER, leading=13)
    _student_styles_cache['table_body_left'] = ParagraphStyle(
        'student_table_body_left', fontName='Helvetica', fontSize=6.6,
        alignment=TA_LEFT, leading=7.2)
    _student_styles_cache['note'] = ParagraphStyle(
        'student_note', fontName='Helvetica-Oblique', fontSize=7.2,
        alignment=TA_CENTER, leading=8.2, textColor=NAVY)
    _student_styles_cache['total_line'] = ParagraphStyle(
        'total_line', fontName='Helvetica-Bold', fontSize=11,
        alignment=TA_RIGHT, leading=13, textColor=NAVY)
    _student_styles_cache['student_comment'] = ParagraphStyle(
        'student_comment', fontName='Helvetica', fontSize=7.2,
        alignment=TA_LEFT, leading=8.6)
    _student_styles_cache['comment'] = _student_styles_cache['student_comment']
    return _student_styles_cache


def generate_report_book(parent, exam_id, class_name, save_path, progress_callback=None):
    try:
        from pypdf import PdfWriter
    except Exception:
        PdfWriter = None
    conn = connect()
    cur = conn.cursor()
    ST = _get_student_styles()

    def report_progress(percent, message):
        if progress_callback is not None:
            progress_callback(int(percent), message)

    profile = _load_school_profile_assets(cur)
    school_name = profile["school_name"]
    school_motto = profile["school_motto"]
    school_addr = profile["school_address"]
    school_phone = profile["school_phone"]
    school_email = profile["school_email"]
    school_logo = profile["school_logo"]
    school_stamp = profile["school_stamp"]
    head_teacher = profile["head_teacher"]
    academic_master = profile["academic_master"]
    discipline_master = profile["discipline_master"]
    head_teacher_signature = profile["head_teacher_signature"]
    academic_master_signature = profile["academic_master_signature"]
    discipline_master_signature = profile["discipline_master_signature"]
    watermark_text = profile["watermark_text"]
    school_website = profile["school_website"]

    cur.execute("""
        SELECT t.term_name, y.year_name, e.exam_name, e.level,
               t.id, t.academic_year_id,
               e.it_has_holiday, e.opening_date, e.closing_date
        FROM exams e
        JOIN terms t ON e.term_id = t.id
        JOIN academic_years y ON t.academic_year_id = y.id
        WHERE e.id = ?
    """, (exam_id,))
    context = cur.fetchone()
    if not context:
        conn.close()
        return False, "Selected exam does not exist."

    term_name, year_name, exam_name, level, term_id, year_id, exam_has_holiday, exam_opening_date, exam_closing_date = context
    opening_date = exam_opening_date if exam_has_holiday and exam_opening_date else ""
    closing_date = exam_closing_date if exam_has_holiday and exam_closing_date else ""
    report_progress(5, "Loading exam context")

    cur.execute("""
        SELECT item_name, quantity
        FROM requirements
        WHERE academic_year_id=? AND term_id=? AND level=?
          AND (class_name=? OR class_name='-- All Classes --')
    """, (year_id, term_id, level, class_name))
    requirements_data = cur.fetchall()

    ranking_data = compute_student_scores(level, exam_id, class_name)
    class_students = [s for s in ranking_data if s.get('class') == class_name]

    if not class_students:
        conn.close()
        return False, "No students found in this class with results."
    report_progress(15, "Preparing student pages")

    use_watermark = get_setting('show_watermark', '1') == '1'
    use_req = get_setting('show_requirements', '1') == '1'
    use_logo = get_setting('show_logo', '1') == '1'
    generated_date = datetime.now().strftime("%A, %d %B %Y %I:%M %p")

    def on_page(canvas, doc):
        if use_watermark:
            draw_watermark(canvas, doc, school_name, year_name, watermark_text)
        canvas.saveState()
        canvas.setStrokeColor(NAVY)
        canvas.setLineWidth(2.0)
        x = doc.leftMargin - 6
        y = doc.bottomMargin - 6
        w = doc.pagesize[0] - doc.leftMargin - doc.rightMargin + 12
        h = doc.pagesize[1] - doc.topMargin - doc.bottomMargin + 12
        canvas.rect(x, y, w, h)
        canvas.restoreState()

    temp_files = []

    for student in class_students:
        student['class_position'] = student.get('position', '-')

    cur.execute("""
        SELECT admission_no, teacher_remarks, headteacher_remarks, academic_master_remarks, discipline_master_remarks
        FROM exam_remarks
        WHERE exam_id = ?
    """, (exam_id,))
    all_remarks = {r[0]: (r[1], r[2], r[3], r[4]) for r in cur.fetchall()}

    total_students = len(class_students)

    for index, student in enumerate(class_students):
        adm = student['admission']
        t_rem, h_rem, a_rem, d_rem = all_remarks.get(adm, (None, None, None, None))

        cur.execute(
            "SELECT exam_no, full_name, gender, stream, comments FROM students WHERE admission_no=?",
            (adm,)
        )
        s_row = cur.fetchone()
        exam_no = s_row[0] if s_row and s_row[0] else student.get('exam_no', '')
        student_name = s_row[1] if s_row else student.get('name', '')
        student_gender = s_row[2] if s_row else student.get('gender', '')
        student_stream = (s_row[3] if s_row and s_row[3] else '-')
        student_comment = s_row[4] if s_row and s_row[4] else ''

        cur.execute("""
            SELECT r.subject_name,
                   COALESCE(s.subject_short_name, r.subject_name),
                   r.marks
            FROM results r
            LEFT JOIN subjects s
              ON s.subject_name = r.subject_name AND s.level = ?
            WHERE r.admission_no=? AND r.exam_id=?
            ORDER BY r.subject_name
        """, (level, adm, exam_id))
        marks_rows = cur.fetchall()

        full_names, short_names, marks_vals, grades_vals = [], [], [], []
        for fn, sn, mk in marks_rows:
            g = get_grade(mk, level=level)
            full_names.append(fn)
            short_names.append(get_subject_short_name(fn, sn))
            marks_vals.append(mk)
            grades_vals.append(g)

        total_marks = sum(marks_vals) if marks_vals else 0
        num_subj = len(marks_vals)
        average = round(total_marks / num_subj, 2) if num_subj else 0
        overall_grade = get_grade(average, level=level) if marks_vals else '-'

        try:
            content = _build_student_report_content(
                ST=ST,
                school_name=school_name,
                school_motto=school_motto,
                school_addr=school_addr,
                school_phone=school_phone,
                school_email=school_email,
                school_website=school_website,
                school_logo=school_logo,
                use_logo=use_logo,
                year_name=year_name,
                term_name=term_name,
                exam_name=exam_name,
                level=level,
                class_name=class_name,
                generated_date=generated_date,
                student_name=student_name,
                student_adm=adm,
                exam_no=exam_no,
                student_gender=student_gender,
                student_stream=student_stream or "-",
                student_status=student['status'],
                class_position=student.get('class_position', '-'),
                total_students=total_students,
                division=student['division'],
                points=student['points'],
                overall_grade=overall_grade,
                full_names=full_names,
                short_names=short_names,
                marks_vals=marks_vals,
                grades_vals=grades_vals,
                total_marks=total_marks,
                average=average,
                requirements_data=requirements_data,
                use_req=use_req,
                opening_date=opening_date,
                closing_date=closing_date,
                head_teacher=head_teacher,
                academic_master=academic_master,
                discipline_master=discipline_master,
                student_comment=student_comment,
                include_page_break=False,
                school_stamp=school_stamp,
                head_teacher_signature=head_teacher_signature,
                academic_master_signature=academic_master_signature,
                discipline_master_signature=discipline_master_signature,
                teacher_remarks=t_rem,
                head_remarks=h_rem,
                academic_remarks=a_rem,
                discipline_remarks=d_rem
            )

            tf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
            tf.close()
            temp_files.append(tf.name)
            student_doc = SimpleDocTemplate(
                tf.name,
                pagesize=A4,
                rightMargin=MARGIN,
                leftMargin=MARGIN,
                topMargin=MARGIN,
                bottomMargin=MARGIN
            )
            student_doc.build(content, onFirstPage=on_page, onLaterPages=on_page)
        except Exception as e:
            for p in temp_files:
                try:
                    os.unlink(p)
                except Exception:
                    pass
            conn.close()
            return False, f"Failed while generating report for {student_name or adm}: {e}"

        report_progress(20 + int(((index + 1) / max(len(class_students), 1)) * 75), f"Rendered {index + 1}/{len(class_students)} students")

    try:
        if PdfWriter is None:
            raise RuntimeError("pypdf is required to merge temporary PDFs. Install 'pypdf' in your environment.")
        merger = PdfWriter()
        for tf in temp_files:
            merger.append(tf)
        with open(save_path, 'wb') as out_f:
            merger.write(out_f)
        merger.close()
        report_progress(100, "Report cards generated")
        return True, save_path
    except Exception as e:
        return False, str(e)
    finally:
        for p in temp_files:
            try:
                os.unlink(p)
            except Exception:
                pass
        conn.close()


def generate_student_report_card(parent, admission_no, level, save_path=None, progress_callback=None, exam_id=None):
    conn = connect()
    cur = conn.cursor()
    ST = _get_student_styles()

    def report_progress(percent, message):
        if progress_callback is not None:
            progress_callback(int(percent), message)

    profile = _load_school_profile_assets(cur)
    school_name = profile["school_name"]
    school_motto = profile["school_motto"]
    school_addr = profile["school_address"]
    school_phone = profile["school_phone"]
    school_email = profile["school_email"]
    school_logo = profile["school_logo"]
    school_stamp = profile["school_stamp"]
    head_teacher = profile["head_teacher"]
    academic_master = profile["academic_master"]
    discipline_master = profile["discipline_master"]
    head_teacher_signature = profile["head_teacher_signature"]
    academic_master_signature = profile["academic_master_signature"]
    discipline_master_signature = profile["discipline_master_signature"]
    watermark_text = profile["watermark_text"]
    school_website = profile["school_website"]

    cur.execute("""
        SELECT admission_no, exam_no, full_name, gender, class, stream, level, comments
        FROM students
        WHERE admission_no=? AND level=?
    """, (admission_no, level))
    student_row = cur.fetchone()
    if not student_row:
        conn.close()
        return False, "Student record was not found."
    report_progress(10, "Loading student record")

    student_adm, exam_no, student_name, student_gender, current_class, student_stream, _student_level, student_comment = student_row

    context_query = """
        SELECT e.id, t.term_name, y.year_name, e.exam_name, e.level,
               t.id, t.academic_year_id, e.status,
               e.it_has_holiday, e.opening_date, e.closing_date
        FROM exams e
        JOIN terms t ON e.term_id = t.id
        JOIN academic_years y ON t.academic_year_id = y.id
        WHERE e.level = ?
    """
    context_params = [level]

    if exam_id is not None:
        context_query += " AND e.id = ?"
        context_params.append(exam_id)

    context_query += """
          AND EXISTS (
              SELECT 1
              FROM results r
              WHERE r.exam_id = e.id
                AND r.admission_no = ?
          )
        ORDER BY
          CASE e.status
            WHEN 'COMPLETED' THEN 0
            WHEN 'OPEN' THEN 1
            WHEN 'CLOSED' THEN 2
            ELSE 3
          END,
          e.id DESC
        LIMIT 1
    """
    context_params.append(student_adm)
    cur.execute(context_query, tuple(context_params))
    context = cur.fetchone()
    if not context:
        conn.close()
        return False, "No exam report is available for this student and exam yet."
    report_progress(25, "Loading exam context")

    exam_id, term_name, year_name, exam_name, _, term_id, year_id, _exam_status, exam_has_holiday, exam_opening_date, exam_closing_date = context
    opening_date = exam_opening_date if exam_has_holiday and exam_opening_date else ""
    closing_date = exam_closing_date if exam_has_holiday and exam_closing_date else ""
    class_name = _resolve_historical_class(cur, student_adm, exam_id, current_class)

    cur.execute("""
        SELECT teacher_remarks, headteacher_remarks, academic_master_remarks, discipline_master_remarks
        FROM exam_remarks
        WHERE admission_no = ? AND exam_id = ?
    """, (student_adm, exam_id))
    remarks_row = cur.fetchone()
    teacher_remarks, head_remarks, academic_remarks, discipline_remarks = remarks_row if remarks_row else (None, None, None, None)

    cur.execute("""
        SELECT item_name, quantity
        FROM requirements
        WHERE academic_year_id=? AND term_id=? AND level=?
          AND (class_name=? OR class_name='-- All Classes --')
    """, (year_id, term_id, level, class_name))
    requirements_data = cur.fetchall()

    ranking_data = compute_student_scores(level, exam_id, class_name)
    class_students = [s for s in ranking_data if s.get('class') == class_name]
    if not class_students:
        conn.close()
        return False, "No class results are available for this student."

    for student in class_students:
        student['class_position'] = student.get('position', '-')

    total_in_class = len(class_students)

    gender_pos_tracker = {}
    gender_counts = {}
    gender_positions = {}
    for s in class_students:
        g = s.get('gender', '')
        if g not in gender_counts:
            gender_counts[g] = 0
        if s['status'] == 'READY':
            gender_counts[g] += 1
            gender_pos_tracker.setdefault(g, 0)
            gender_pos_tracker[g] += 1
            gender_positions[s['admission']] = gender_pos_tracker[g]

    target_student = next(
        (s for s in class_students if s['admission'] == student_adm),
        None
    )
    if not target_student:
        conn.close()
        return False, "The selected student does not have report data yet."
    report_progress(50, "Preparing report data")

    cur.execute("""
        SELECT r.subject_name,
               COALESCE(s.subject_short_name, r.subject_name),
               r.marks
        FROM results r
        LEFT JOIN subjects s
          ON s.subject_name = r.subject_name AND s.level = ?
        WHERE r.admission_no=? AND r.exam_id=?
        ORDER BY r.subject_name
    """, (level, student_adm, exam_id))
    marks_rows = cur.fetchall()

    full_names, short_names, marks_vals, grades_vals = [], [], [], []
    for fn, sn, mk in marks_rows:
        g = get_grade(mk, level=level)
        full_names.append(fn)
        short_names.append(get_subject_short_name(fn, sn))
        marks_vals.append(mk)
        grades_vals.append(g)
    report_progress(70, "Building report sections")

    total_marks = sum(marks_vals) if marks_vals else 0
    num_subj = len(marks_vals)
    average = round(total_marks / num_subj, 2) if num_subj else 0

    if save_path is None:
        output_dir = os.path.join(tempfile.gettempdir(), "srms_report_cards")
        os.makedirs(output_dir, exist_ok=True)
        safe_exam = "".join(ch for ch in str(exam_name) if ch.isalnum() or ch in (" ", "_", "-")).strip().replace(" ", "_")
        safe_adm = student_adm.replace("/", "_")
        save_path = os.path.join(output_dir, f"{safe_adm}_{safe_exam}.pdf")
    else:
        os.makedirs(os.path.dirname(save_path) or ".", exist_ok=True)

    use_watermark = get_setting('show_watermark', '1') == '1'
    use_req = get_setting('show_requirements', '1') == '1'
    use_logo = get_setting('show_logo', '1') == '1'
    generated_date = datetime.now().strftime("%A, %d %B %Y %I:%M %p")

    def on_page(canvas, doc):
        if use_watermark:
            draw_watermark(canvas, doc, school_name, year_name, watermark_text)
        canvas.saveState()
        canvas.setStrokeColor(NAVY)
        canvas.setLineWidth(2.0)
        x = doc.leftMargin - 6
        y = doc.bottomMargin - 6
        w = doc.pagesize[0] - doc.leftMargin - doc.rightMargin + 12
        h = doc.pagesize[1] - doc.topMargin - doc.bottomMargin + 12
        canvas.rect(x, y, w, h)
        canvas.restoreState()

    doc = SimpleDocTemplate(
        save_path,
        pagesize=A4,
        rightMargin=MARGIN,
        leftMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=MARGIN
    )

    class_position = target_student.get('class_position', target_student.get('position', '-'))
    overall_grade = get_grade(average, level=level) if marks_vals else '-'
    try:
        content = _build_student_report_content(
            ST=ST,
            school_name=school_name,
            school_motto=school_motto,
            school_addr=school_addr,
            school_phone=school_phone,
            school_email=school_email,
            school_website=school_website,
            school_logo=school_logo,
            use_logo=use_logo,
            year_name=year_name,
            term_name=term_name,
            exam_name=exam_name,
            level=level,
            class_name=class_name,
            generated_date=generated_date,
            student_name=student_name,
            student_adm=student_adm,
            exam_no=exam_no,
            student_gender=student_gender,
            student_stream=student_stream or "-",
            student_status=target_student['status'],
            class_position=class_position,
            total_students=total_in_class,
            division=target_student['division'],
            points=target_student['points'],
            overall_grade=overall_grade,
            full_names=full_names,
            short_names=short_names,
            marks_vals=marks_vals,
            grades_vals=grades_vals,
            total_marks=total_marks,
            average=average,
            requirements_data=requirements_data,
            use_req=use_req,
            opening_date=opening_date,
            closing_date=closing_date,
            head_teacher=head_teacher,
            academic_master=academic_master,
            discipline_master=discipline_master,
            student_comment=student_comment,
            include_page_break=False,
            school_stamp=school_stamp,
            head_teacher_signature=head_teacher_signature,
            academic_master_signature=academic_master_signature,
            discipline_master_signature=discipline_master_signature,
            teacher_remarks=teacher_remarks,
            head_remarks=head_remarks,
            academic_remarks=academic_remarks,
            discipline_remarks=discipline_remarks,
        )
        doc.build(content, onFirstPage=on_page, onLaterPages=on_page)
        return True, save_path
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


# ======================================================================
# BUILDER HELPERS
# ======================================================================

def _build_student_page_header(ST, school_name, motto, addr, phone, email, website,
                               logo_path, use_logo, year, term, exam, level, cls,
                               stream, gen_date):
    left = None
    if use_logo and logo_path:
        try:
            logo = Image(logo_path, width=0.62 * inch, height=0.62 * inch)
            left = Table([[logo]], colWidths=[0.85 * inch])
            left.setStyle(TableStyle([
                ('BOX', (0, 0), (-1, -1), 1.0, NAVY),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
        except Exception as e:
            print(f"[WARNING] Could not load logo '{logo_path}': {e}")

    if left is None:
        left = Table([[
            Paragraph('<b>SCHOOL</b>', ST['tiny_b'])
        ]], colWidths=[0.85 * inch])
        left.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 1.0, NAVY),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))

    center_lines = [Paragraph(f'{school_name.upper()}', ST['title'])]
    gold_rule = Table([['']], colWidths=[1.1 * inch], rowHeights=[1.6])
    gold_rule.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), GOLD),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    center_flow = [center_lines[0], Spacer(1, 2),
                   Table([[gold_rule]], colWidths=[USABLE_WIDTH * 0.5],
                         style=TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER')]))]
    if motto:
        center_flow.append(Spacer(1, 2))
        center_flow.append(Paragraph(f'{motto}', ST['motto']))
    center = Table([[flow] for flow in center_flow], colWidths=[USABLE_WIDTH * 0.6])
    center.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))

    credential_rows = [
        [Paragraph(f'<b>{_safe_text(year)} &middot; {_safe_text(term)}</b>', ST['credential_tag_b'])],
        [Paragraph(_safe_text(exam), ST['credential_tag'])],
    ]
    right = Table(credential_rows, colWidths=[1.35 * inch])
    right.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.75, NAVY),
        ('BACKGROUND', (0, 0), (-1, -1), NAVY_LIGHT),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))

    header = Table([[left, center, right]],
                   colWidths=[0.85 * inch, USABLE_WIDTH - (0.85 * inch + 1.35 * inch), 1.35 * inch])
    header.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (1, 0), (1, 0), 'CENTER'),
        ('LINEBELOW', (0, 0), (-1, 0), 1.0, GRID_COLOR),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
    ]))
    return header


def _build_student_name_banner(ST, student_name, admission_no, class_name, level, gender, status):
    gender_full = "Male" if gender and gender.lower().startswith("m") else "Female" if gender and gender.lower().startswith("f") else _safe_text(gender)
    credential_bits = [
        f"Admission {_safe_text(admission_no)}",
        _safe_text(class_name),
        _safe_text(level).replace('_', '-'),
        gender_full,
    ]
    credential_text = " &middot; ".join(credential_bits)
    status_hex = _status_color(status).hexval()[2:]

    rows = [
        [Paragraph(_safe_text(student_name), ST['student_name'])],
        [Paragraph(
            f'{credential_text} &nbsp;&nbsp;'
            f'<font color="#{status_hex}"><b>{_safe_text(status)}</b></font>',
            ST['credential_line']
        )],
    ]
    tbl = Table(rows, colWidths=[USABLE_WIDTH])
    tbl.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, 0), 6),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 1),
        ('TOPPADDING', (0, 1), (-1, 1), 1),
        ('BOTTOMPADDING', (0, 1), (-1, 1), 4),
    ]))
    return tbl


def _build_student_page_metrics(ST, position, total_students, division, points, average, status):
    status_hex = _status_color(status).hexval()[2:]
    rows = [[
        Paragraph('RANK', ST['summary_label']),
        Paragraph('DIVISION', ST['summary_label']),
        Paragraph('POINTS', ST['summary_label']),
        Paragraph('AVERAGE', ST['summary_label']),
        Paragraph('STATUS', ST['summary_label']),
    ], [
        Paragraph(f"{_safe_text(position)} / {_safe_text(total_students)}", ST['summary_value']),
        Paragraph(_safe_text(division), ST['summary_value']),
        Paragraph(_safe_text(points), ST['summary_value']),
        Paragraph(f"{_safe_text(average)}%", ST['summary_value']),
        Paragraph(f'<font color="#{status_hex}">{_safe_text(status)}</font>', ST['summary_value']),
    ]]
    tbl = Table(rows, colWidths=[USABLE_WIDTH / 5.0] * 5)
    tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), NAVY_LIGHT),
        ('TEXTCOLOR', (0, 0), (-1, 0), NAVY),
        ('BOX', (0, 0), (-1, -1), 0.5, NAVY),
        ('GRID', (0, 0), (-1, -1), 0.3, GRID_COLOR),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    return tbl


def _build_student_page_results(ST, short_names, marks, grades):
    fs_head, fs_body = 11, 10.5
    table_head = ParagraphStyle(
        'dynamic_table_head', parent=ST['table_head'],
        fontSize=fs_head, leading=fs_head + 2
    )
    table_body = ParagraphStyle(
        'dynamic_table_body', parent=ST['table_body'],
        fontSize=fs_body, leading=fs_body + 2
    )

    if not short_names:
        label_w = 1.0 * inch
        rows = [
            [Paragraph('SUBJECT', table_head), Paragraph('-', table_head)],
            [Paragraph('MARKS', table_head), Paragraph('-', table_body)],
            [Paragraph('GRADE', table_head), Paragraph('-', table_body)],
        ]
        table = Table(rows, colWidths=[label_w, USABLE_WIDTH - label_w])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), NAVY),
            ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
            ('BACKGROUND', (0, 1), (-1, 1), NAVY_LIGHT),
            ('BACKGROUND', (0, 2), (0, 2), NAVY),
            ('TEXTCOLOR', (0, 2), (0, 2), WHITE),
            ('BOX', (0, 0), (-1, -1), 0.5, NAVY),
            ('GRID', (0, 0), (-1, -1), 0.3, GRID_COLOR),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        return [table]

    # Cap subjects per row so the font never has to shrink below the floor above;
    # once a student has more subjects than this, wrap into additional rows instead.
    CHUNK = 8
    label_w = 0.9 * inch
    n = len(short_names)
    chunks = [list(range(i, min(i + CHUNK, n))) for i in range(0, n, CHUNK)]

    flowables = []
    for ci, idxs in enumerate(chunks):
        chunk_names = [short_names[i] for i in idxs]
        chunk_marks = [marks[i] for i in idxs]
        chunk_grades = [grades[i] for i in idxs]
        col_count = len(idxs)
        subject_w = (USABLE_WIDTH - label_w) / col_count

        subject_row = [Paragraph('SUBJECT', table_head)] + [Paragraph(sn, table_head) for sn in chunk_names]
        marks_row = [Paragraph('MARKS', table_head)] + [Paragraph(str(m), table_body) for m in chunk_marks]
        grade_cells = [Paragraph('GRADE', table_head)]
        for g in chunk_grades:
            _, tx = _grade_band(g)
            grade_cells.append(Paragraph(f'<font color="#{tx.hexval()[2:]}"><b>{_safe_text(g)}</b></font>', table_body))

        col_widths = [label_w] + [subject_w] * col_count
        table = Table([subject_row, marks_row, grade_cells], colWidths=col_widths)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), NAVY),
            ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
            ('BACKGROUND', (0, 1), (-1, 1), NAVY_LIGHT),
            ('BACKGROUND', (0, 2), (0, 2), NAVY),
            ('TEXTCOLOR', (0, 2), (0, 2), WHITE),
            ('BOX', (0, 0), (-1, -1), 0.5, NAVY),
            ('GRID', (0, 0), (-1, -1), 0.3, GRID_COLOR),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ]))
        flowables.append(table)
        if ci < len(chunks) - 1:
            flowables.append(Spacer(1, 3))

    total_marks = sum(marks) if marks else 0
    flowables.append(Spacer(1, 3))
    flowables.append(Paragraph(f'Total: <b>{total_marks}</b>', ST['total_line']))
    return flowables


def _build_requirements_block(ST, requirements_data, opening_date, closing_date, width):
    title = Table([[Paragraph('REQUIREMENTS', ST['section_underline'])]], colWidths=[width])
    title.setStyle(TableStyle([
        ('LINEBELOW', (0, 0), (-1, -1), 1.5, NAVY),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
    ]))

    dates = Paragraph(
        f"<b>Opening:</b> {_safe_text(opening_date)} &nbsp;&nbsp; <b>Closing:</b> {_safe_text(closing_date)}",
        ST['label']
    )

    rows = [[
        Paragraph('ITEM', ST['table_head']),
        Paragraph('QTY', ST['table_head']),
    ]]
    for item, qty in requirements_data:
        rows.append([
            Paragraph(_safe_text(item), ST['req_item']),
            Paragraph(_safe_text(qty), ST['table_body']),
        ])

    body = Table(rows, colWidths=[width - 0.7 * inch, 0.7 * inch])
    style_cmds = [
        ('BOX', (0, 0), (-1, -1), 0.5, NAVY),
        ('LINEBELOW', (0, 0), (-1, 0), 0.3, GRID_COLOR),
        ('BACKGROUND', (0, 0), (-1, 0), NAVY_LIGHT),
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
    ]
    # Alternating row shading for scannability instead of a full grid
    for r in range(2, len(rows), 2):
        style_cmds.append(('BACKGROUND', (0, r), (-1, r), LIGHT_BG))
    body.setStyle(TableStyle(style_cmds))

    return Table([[title], [Spacer(1, 3)], [dates], [Spacer(1, 3)], [body]], colWidths=[width])


def _build_comments_block(ST, discipline_remarks, teacher_remarks, academic_remarks, width):
    title = Table([[Paragraph('COMMENTS', ST['section_underline'])]], colWidths=[width])
    title.setStyle(TableStyle([
        ('LINEBELOW', (0, 0), (-1, -1), 1.5, NAVY),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
    ]))

    entries = [
        ('DISCIPLINE MASTER', discipline_remarks),
        ('CLASS TEACHER', teacher_remarks),
        ('ACADEMIC MASTER', academic_remarks),
    ]
    rows = [[title]]
    for role, text in entries:
        block = Table(
            [
                [Paragraph(role, ST['comment_role'])],
                [Paragraph(text, ST['comment_quote'])],
            ],
            colWidths=[width]
        )
        block.setStyle(TableStyle([
            ('LINEBEFORE', (0, 1), (0, 1), 2.5, GOLD),
            ('BACKGROUND', (0, 1), (0, 1), LIGHT_BG),
            ('LEFTPADDING', (0, 1), (0, 1), 8),
            ('RIGHTPADDING', (0, 1), (0, 1), 6),
            ('TOPPADDING', (0, 1), (0, 1), 4),
            ('BOTTOMPADDING', (0, 1), (0, 1), 6),
            ('TOPPADDING', (0, 0), (0, 0), 0),
            ('BOTTOMPADDING', (0, 0), (0, 0), 2),
        ]))
        rows.append([block])
        rows.append([Spacer(1, 6)])

    return Table(rows, colWidths=[width])


def _build_lower_section(ST, requirements_data, use_req, opening_date, closing_date,
                          average, division, level,
                          teacher_remarks=None, academic_remarks=None, discipline_remarks=None):
    smart_teacher = get_default_remark(average, division, level)
    if not teacher_remarks:
        teacher_remarks = smart_teacher
    if not academic_remarks:
        academic_remarks = get_academic_master_remark(division)
    if not discipline_remarks:
        discipline_remarks = get_discipline_master_remark(average)

    has_requirements = bool(use_req and requirements_data)
    GAP = 14

    if has_requirements:
        col_w = (USABLE_WIDTH - GAP) / 2
        req_block = _build_requirements_block(ST, requirements_data, opening_date, closing_date, col_w)
        com_block = _build_comments_block(ST, discipline_remarks, teacher_remarks, academic_remarks, col_w)
        outer = Table([[req_block, '', com_block]], colWidths=[col_w, GAP, col_w])
        outer.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
        return outer
    else:
        # No requirements to show (disabled or empty) — comments take the full width
        # instead of leaving a lopsided half-empty column.
        return _build_comments_block(ST, discipline_remarks, teacher_remarks, academic_remarks, USABLE_WIDTH)


def _build_student_page_footer(ST):
    footer = Table([[
        Paragraph(
            '<b><i>Education is the most powerful weapon which you can use to change the world.</i></b>',
            ST['note']
        )
    ]], colWidths=[USABLE_WIDTH])
    footer.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.4, GRID_COLOR),
        ('BACKGROUND', (0, 0), (-1, -1), NAVY_LIGHT),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    return footer


def _build_footer_contacts(ST, addr, phone, email, website):
    items = [v for v in [addr, phone, email, website] if v and v != '-']
    if not items:
        return None
    text = " &nbsp;&nbsp;&nbsp; ".join(_safe_text(v) for v in items)
    return Paragraph(text, ST['contact'])


def _build_srms_tag(ST, school_name, year_name):
    text = f"Generated by SRMS V5.0 &middot; {_safe_text(school_name)} {_safe_text(year_name)}"
    return Paragraph(text, ST['srms_tag'])


def _safe_text(value):
    if value is None:
        return '-'
    text = str(value).strip()
    return text if text else '-'


def _build_qr_drawing(data, size):
    try:
        widget = QrCodeWidget(data)
        b = widget.getBounds()
        w, h = b[2] - b[0], b[3] - b[1]
        d = Drawing(size, size, transform=[size / w, 0, 0, size / h, 0, 0])
        d.add(widget)
        return d
    except Exception:
        return None


def _build_student_report_content(
    ST, school_name, school_motto, school_addr, school_phone,
    school_email, school_website, school_logo, use_logo,
    year_name, term_name, exam_name, level, class_name, generated_date,
    student_name, student_adm, exam_no, student_gender, student_stream, student_status,
    class_position, total_students, division, points, overall_grade,
    full_names, short_names, marks_vals, grades_vals, total_marks, average,
    requirements_data, use_req, opening_date, closing_date, head_teacher, academic_master,
    student_comment='', include_page_break=False, school_stamp=None,
    head_teacher_signature=None, academic_master_signature=None,
    discipline_master=None, discipline_master_signature=None,
    teacher_remarks=None, head_remarks=None,
    academic_remarks=None, discipline_remarks=None
):
    content = [
        _build_student_page_header(
            ST, school_name, school_motto, school_addr, school_phone,
            school_email, school_website, school_logo, use_logo,
            year_name, term_name, exam_name, level, class_name,
            student_stream, generated_date
        ),
        _build_student_name_banner(
            ST, student_name, student_adm, class_name, level, student_gender, student_status
        ),
        Spacer(1, 5),
        _build_student_page_metrics(
            ST, class_position, total_students, division, points, average, student_status
        ),
        Spacer(1, 3),
    ]
    content.extend(_build_student_page_results(ST, short_names, marks_vals, grades_vals))
    content.append(Spacer(1, 5))
    content.append(
        _build_lower_section(
            ST, requirements_data, use_req, opening_date, closing_date,
            average, division, level,
            teacher_remarks=teacher_remarks,
            academic_remarks=academic_remarks,
            discipline_remarks=discipline_remarks,
        )
    )
    content.append(Spacer(1, 5))
    content.append(
        _build_signatures(
            ST,
            head_teacher=head_teacher,
            academic_master=academic_master,
            discipline_master=discipline_master,
            head_teacher_signature=head_teacher_signature,
            academic_master_signature=academic_master_signature,
            discipline_master_signature=discipline_master_signature,
            stamp_path=school_stamp,
            student_adm=student_adm,
            exam_name=exam_name,
        )
    )
    content.append(Spacer(1, 3))
    content.append(_build_student_page_footer(ST))
    content.append(Spacer(1, 2))
    content.append(Paragraph(
        '<b>Note:</b> This report is computer generated and requires only the head teacher signature.',
        ST['note']
    ))
    contacts_line = _build_footer_contacts(ST, school_addr, school_phone, school_email, school_website)
    if contacts_line is not None:
        content.append(Spacer(1, 4))
        content.append(contacts_line)
    content.append(Spacer(1, 2))
    content.append(_build_srms_tag(ST, school_name, year_name))
    if include_page_break:
        content.append(PageBreak())
    return content


def _build_signatures(
    ST,
    head_teacher,
    academic_master,
    discipline_master,
    head_teacher_signature=None,
    academic_master_signature=None,
    discipline_master_signature=None,
    stamp_path=None,
    student_adm='',
    exam_name='',
):
    GAP = 8
    col_w = (USABLE_WIDTH - GAP * 3) / 4
    sig_style = ST.get('tiny_left') or ST.get('sig')
    sig_hdr_style = ST.get('tiny_b') or ST.get('sig_hdr')

    def labeled_block(title, body_flowable, caption_text):
        tbl = Table(
            [
                [Paragraph(f'<b>{title}</b>', sig_hdr_style)],
                [body_flowable],
                [Paragraph(caption_text, sig_style)],
            ],
            colWidths=[col_w],
            rowHeights=[0.22 * inch, 0.42 * inch, 0.24 * inch],
        )
        tbl.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('LEFTPADDING', (0, 0), (-1, -1), 2),
            ('RIGHTPADDING', (0, 0), (-1, -1), 2),
            ('TOPPADDING', (0, 0), (-1, -1), 1),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ]))
        return tbl

    head_signature = _safe_image(head_teacher_signature, 1.0 * inch, 0.35 * inch)
    if head_signature is None:
        head_signature = Paragraph('Signature: __________', sig_style)
    head_block = labeled_block(
        'HEADMASTER/MISTRESS',
        head_signature,
        f'Name: {head_teacher}' if head_teacher else 'Name: __________',
    )

    parent_block = labeled_block(
        'PARENT / GUARDIAN',
        Paragraph('Signature: __________', sig_style),
        'Date: __________',
    )

    stamp_image = _safe_image(stamp_path, 0.55 * inch, 0.55 * inch)
    if stamp_image is None:
        stamp_image = Paragraph('STAMP', sig_hdr_style)
    stamp_block = labeled_block('OFFICIAL STAMP', stamp_image, '')

    qr_data = f"SRMS|{_safe_text(student_adm)}|{_safe_text(exam_name)}"
    qr_drawing = _build_qr_drawing(qr_data, 0.42 * inch)
    verify_body = qr_drawing if qr_drawing is not None else Paragraph('QR', sig_hdr_style)
    verify_block = labeled_block('VERIFY', verify_body, '')

    tbl = Table(
        [[head_block, parent_block, stamp_block, verify_block]],
        colWidths=[col_w, col_w, col_w, col_w]
    )
    tbl.setStyle(TableStyle([
        ('LINEABOVE', (0, 0), (-1, 0), 1, NAVY),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), GAP // 2),
        ('RIGHTPADDING', (0, 0), (-1, -1), GAP // 2),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    return tbl