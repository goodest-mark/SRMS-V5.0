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
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from database import connect
from settings_page import get_setting
from watermark import draw_watermark
from ranking_engine import compute_student_scores
from grade_utils import get_grade
from remarks_utils import get_default_remark, get_headteacher_remark, get_developmental_note
from ui_helpers import get_subject_short_name

# Color scheme
NAVY = colors.HexColor('#1B3A5C')
NAVY_LIGHT = colors.HexColor('#E8EDF2')
LIGHT_BG = colors.HexColor('#F8FAFC')
GRID_COLOR = colors.HexColor('#D0D5DD')
WHITE = colors.white

# Page dimensions — landscape A4, generous but balanced margins
PAGE_SIZE = landscape(A4)
L_MARGIN = 28
R_MARGIN = 28
T_MARGIN = 20
B_MARGIN = 20
PAGE_W = PAGE_SIZE[0] - L_MARGIN - R_MARGIN

STUDENT_PAGE_SIZE = A4
STUDENT_L_MARGIN = 16
STUDENT_R_MARGIN = 16
STUDENT_T_MARGIN = 14
STUDENT_B_MARGIN = 14
STUDENT_PAGE_W = STUDENT_PAGE_SIZE[0] - STUDENT_L_MARGIN - STUDENT_R_MARGIN
STUDENT_PAGE_H = STUDENT_PAGE_SIZE[1] - STUDENT_T_MARGIN - STUDENT_B_MARGIN

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
               academic_master, discipline_master, class_master,
               head_teacher_signature, academic_master_signature,
               discipline_master_signature, class_master_signature,
               watermark_text, school_website,
               head_teacher_signature_enabled, academic_master_signature_enabled,
               discipline_master_signature_enabled, class_master_signature_enabled
        FROM school_profile
        LIMIT 1
    """)
    profile = cur.fetchone()
    head_signature_enabled = bool(profile and len(profile) > 17 and profile[17])
    academic_signature_enabled = bool(profile and len(profile) > 18 and profile[18])
    discipline_signature_enabled = bool(profile and len(profile) > 19 and profile[19])
    class_signature_enabled = bool(profile and len(profile) > 20 and profile[20])
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
        "class_master": "",
        "head_teacher_signature": profile[11] if head_signature_enabled and profile and profile[11] and os.path.exists(profile[11]) else None,
        "academic_master_signature": profile[12] if academic_signature_enabled and profile and profile[12] and os.path.exists(profile[12]) else None,
        "discipline_master_signature": profile[13] if discipline_signature_enabled and profile and profile[13] and os.path.exists(profile[13]) else None,
        "class_master_signature": None,
        "watermark_text": profile[15] if profile and profile[15] else "CONFIDENTIAL",
        "school_website": profile[16] if profile and len(profile) > 16 and profile[16] else "",
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
    """Return exams that have report data for a student, regardless of status."""
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


def _get_styles():
    if _styles_cache:
        return _styles_cache
    _styles_cache['title'] = ParagraphStyle(
        'rc_title', fontName='Helvetica-Bold', fontSize=15,
        alignment=TA_CENTER, leading=18, textColor=NAVY)
    _styles_cache['motto'] = ParagraphStyle(
        'rc_motto', fontName='Helvetica-Oblique', fontSize=8,
        alignment=TA_CENTER, leading=11, textColor=NAVY)
    _styles_cache['section_hdr'] = ParagraphStyle(
        'rc_section_hdr', fontName='Helvetica-Bold', fontSize=8,
        alignment=TA_CENTER, textColor=NAVY, leading=11)
    _styles_cache['section_left'] = ParagraphStyle(
        'rc_section_left', fontName='Helvetica-Bold', fontSize=8,
        alignment=TA_LEFT, textColor=NAVY, leading=11)
    _styles_cache['label'] = ParagraphStyle(
        'rc_label', fontName='Helvetica-Bold', fontSize=7.5,
        alignment=TA_LEFT, leading=10)
    _styles_cache['value'] = ParagraphStyle(
        'rc_value', fontName='Helvetica', fontSize=7.5,
        alignment=TA_LEFT, leading=10)
    _styles_cache['small'] = ParagraphStyle(
        'rc_small', fontName='Helvetica', fontSize=7,
        alignment=TA_LEFT, leading=9)
    _styles_cache['small_c'] = ParagraphStyle(
        'rc_small_c', fontName='Helvetica', fontSize=7,
        alignment=TA_CENTER, leading=9)
    _styles_cache['small_b'] = ParagraphStyle(
        'rc_small_b', fontName='Helvetica-Bold', fontSize=7,
        alignment=TA_CENTER, leading=9)
    _styles_cache['small_b_left'] = ParagraphStyle(
        'rc_small_b_left', fontName='Helvetica-Bold', fontSize=7,
        alignment=TA_LEFT, leading=9)
    _styles_cache['center'] = ParagraphStyle(
        'rc_center', fontName='Helvetica', fontSize=7.5,
        alignment=TA_CENTER, leading=10)
    _styles_cache['center_b'] = ParagraphStyle(
        'rc_center_b', fontName='Helvetica-Bold', fontSize=7.5,
        alignment=TA_CENTER, leading=10)
    _styles_cache['right_b'] = ParagraphStyle(
        'rc_right_b', fontName='Helvetica-Bold', fontSize=7.5,
        alignment=TA_RIGHT, leading=10)
    _styles_cache['note'] = ParagraphStyle(
        'rc_note', fontName='Helvetica-Oblique', fontSize=7,
        alignment=TA_CENTER, leading=10, textColor=NAVY)
    _styles_cache['sig'] = ParagraphStyle(
        'rc_sig', fontName='Helvetica', fontSize=7,
        alignment=TA_LEFT, leading=11)
    _styles_cache['sig_hdr'] = ParagraphStyle(
        'rc_sig_hdr', fontName='Helvetica-Bold', fontSize=7.5,
        alignment=TA_CENTER, leading=10, textColor=NAVY)
    _styles_cache['tiny'] = ParagraphStyle(
        'rc_tiny', fontName='Helvetica', fontSize=6,
        alignment=TA_CENTER, leading=8)
    _styles_cache['tiny_b'] = ParagraphStyle(
        'rc_tiny_b', fontName='Helvetica-Bold', fontSize=6,
        alignment=TA_LEFT, leading=8)
    _styles_cache['contact_hdr'] = ParagraphStyle(
        'rc_contact_hdr', fontName='Helvetica-Bold', fontSize=8,
        alignment=TA_LEFT, leading=11, textColor=NAVY)
    _styles_cache['acad_hdr'] = ParagraphStyle(
        'rc_acad_hdr', fontName='Helvetica-Bold', fontSize=8,
        alignment=TA_LEFT, leading=11, textColor=NAVY)
    _styles_cache['comment_body'] = ParagraphStyle(
        'rc_comment_body', fontName='Helvetica', fontSize=7,
        alignment=TA_LEFT, leading=14)
    return _styles_cache


def _get_student_styles():
    if _student_styles_cache:
        return _student_styles_cache

    _student_styles_cache['title'] = ParagraphStyle(
        'student_title', fontName='Helvetica-Bold', fontSize=20,
        alignment=TA_CENTER, leading=22, textColor=NAVY)
    _student_styles_cache['motto'] = ParagraphStyle(
        'student_motto', fontName='Helvetica-BoldOblique', fontSize=9,
        alignment=TA_CENTER, leading=10, textColor=NAVY)
    _student_styles_cache['contact'] = ParagraphStyle(
        'student_contact', fontName='Helvetica', fontSize=8,
        alignment=TA_CENTER, leading=10)
    _student_styles_cache['section_hdr'] = ParagraphStyle(
        'student_section_hdr', fontName='Helvetica-Bold', fontSize=8,
        alignment=TA_LEFT, leading=10, textColor=WHITE)
    _student_styles_cache['label'] = ParagraphStyle(
        'student_label', fontName='Helvetica-Bold', fontSize=7.2,
        alignment=TA_LEFT, leading=8.5, textColor=NAVY)
    _student_styles_cache['value'] = ParagraphStyle(
        'student_value', fontName='Helvetica', fontSize=7.2,
        alignment=TA_LEFT, leading=8.5)
    _student_styles_cache['tiny'] = ParagraphStyle(
        'student_tiny', fontName='Helvetica', fontSize=6.5,
        alignment=TA_CENTER, leading=8)
    _student_styles_cache['tiny_left'] = ParagraphStyle(
        'student_tiny_left', fontName='Helvetica', fontSize=6.5,
        alignment=TA_LEFT, leading=8)
    _student_styles_cache['tiny_b'] = ParagraphStyle(
        'student_tiny_b', fontName='Helvetica-Bold', fontSize=6.5,
        alignment=TA_CENTER, leading=8)
    _student_styles_cache['summary_label'] = ParagraphStyle(
        'student_summary_label', fontName='Helvetica-Bold', fontSize=7,
        alignment=TA_CENTER, leading=8, textColor=NAVY)
    _student_styles_cache['summary_value'] = ParagraphStyle(
        'student_summary_value', fontName='Helvetica-Bold', fontSize=12,
        alignment=TA_CENTER, leading=13)
    _student_styles_cache['summary_small'] = ParagraphStyle(
        'student_summary_small', fontName='Helvetica', fontSize=7,
        alignment=TA_CENTER, leading=8)
    _student_styles_cache['table_head'] = ParagraphStyle(
        'student_table_head', fontName='Helvetica-Bold', fontSize=7.2,
        alignment=TA_CENTER, leading=8.5)
    _student_styles_cache['table_body'] = ParagraphStyle(
        'student_table_body', fontName='Helvetica', fontSize=6.5,
        alignment=TA_CENTER, leading=7.2)
    _student_styles_cache['table_body_left'] = ParagraphStyle(
        'student_table_body_left', fontName='Helvetica', fontSize=6.5,
        alignment=TA_LEFT, leading=7.2)
    _student_styles_cache['note'] = ParagraphStyle(
        'student_note', fontName='Helvetica-Oblique', fontSize=6.8,
        alignment=TA_CENTER, leading=8, textColor=NAVY)
    _student_styles_cache['student_comment'] = ParagraphStyle(
        'student_comment', fontName='Helvetica', fontSize=7,
        alignment=TA_LEFT, leading=8.5)
    _student_styles_cache['comment'] = _student_styles_cache['student_comment']
    return _student_styles_cache



def generate_report_book(parent, exam_id, class_name, save_path, progress_callback=None):
    """
    Generates one portrait A4 page per student using the same layout
    as the single-student report card.
    """
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

    # ── Fetch school profile ──
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
    class_master = profile["class_master"]
    head_teacher_signature = profile["head_teacher_signature"]
    academic_master_signature = profile["academic_master_signature"]
    discipline_master_signature = profile["discipline_master_signature"]
    class_master_signature = profile["class_master_signature"]
    watermark_text = profile["watermark_text"]
    school_website = profile["school_website"]

    # ── Academic context ──
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

    # ── Requirements ──
    cur.execute("""
        SELECT item_name, quantity
        FROM requirements
        WHERE academic_year_id=? AND term_id=? AND level=?
          AND (class_name=? OR class_name='-- All Classes --')
    """, (year_id, term_id, level, class_name))
    requirements_data = cur.fetchall()

    # ── Ranking ──
    ranking_data = compute_student_scores(level, exam_id, class_name)
    class_students = [s for s in ranking_data if s.get('class') == class_name]

    if not class_students:
        conn.close()
        return False, "No students found in this class with results."
    report_progress(15, "Preparing student pages")

    # ── Settings ──
    use_watermark = get_setting('show_watermark', '1') == '1'
    use_req = get_setting('show_requirements', '1') == '1'
    use_logo = get_setting('show_logo', '1') == '1'
    generated_date = datetime.now().strftime("%A, %d %B %Y %I:%M %p")

    # ── Page callback (border + watermark) ──
    def on_page(canvas, doc):
        if use_watermark:
            draw_watermark(canvas, doc, school_name, year_name, watermark_text)
        canvas.saveState()
        canvas.setStrokeColor(NAVY)
        canvas.setLineWidth(2.5)
        x = doc.leftMargin - 8
        y = doc.bottomMargin - 8
        w = doc.pagesize[0] - doc.leftMargin - doc.rightMargin + 16
        h = doc.pagesize[1] - doc.topMargin - doc.bottomMargin + 16
        canvas.rect(x, y, w, h)
        canvas.restoreState()

    # We'll generate one PDF per student into temporary files then merge them.
    temp_files = []

    class_students = sorted(
        class_students,
        key=lambda x: (
            -_numeric_or_zero(x.get('average')),
            -_numeric_or_zero(x.get('total_marks')),
            x.get('admission', '')
        )
    )
    for pos, student in enumerate(class_students, start=1):
        student['class_position'] = pos

    # Fetch manual remarks for all students in one go
    cur.execute("""
        SELECT admission_no, teacher_remarks, headteacher_remarks, developmental_notes
        FROM exam_remarks
        WHERE exam_id = ?
    """, (exam_id,))
    all_remarks = {r[0]: (r[1], r[2], r[3]) for r in cur.fetchall()}

    total_students = len([s for s in class_students if s['status'] == 'READY'])

    for index, student in enumerate(class_students):
        adm = student['admission']
        t_rem, h_rem, d_notes = all_remarks.get(adm, (None, None, None))
        
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

        # Build single-student content and write to a temp PDF.
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
            class_position=student.get('class_position', student.get('position', '-')),
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
            class_master=class_master,
            student_comment=student_comment,
            include_page_break=False,
            school_stamp=school_stamp,
            teacher_remarks=t_rem,
            head_remarks=h_rem,
            dev_notes=d_notes
        )

        # Write this student's single page to a temporary PDF file.
        tf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        tf.close()
        temp_files.append(tf.name)
        try:
            student_doc = SimpleDocTemplate(
                tf.name, pagesize=STUDENT_PAGE_SIZE,
                rightMargin=STUDENT_R_MARGIN, leftMargin=STUDENT_L_MARGIN,
                topMargin=STUDENT_T_MARGIN, bottomMargin=STUDENT_B_MARGIN
            )
            student_doc.build(content, onFirstPage=on_page, onLaterPages=on_page)
        except Exception as e:
            # Clean up temp files on error
            for p in temp_files:
                try:
                    os.unlink(p)
                except Exception:
                    pass
            conn.close()
            return False, str(e)

        report_progress(20 + int(((index + 1) / max(len(class_students), 1)) * 75), f"Rendered {index + 1}/{len(class_students)} students")

    # Merge temp PDFs into final output
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
        # cleanup temp files and DB connection
        for p in temp_files:
            try:
                os.unlink(p)
            except Exception:
                pass
        conn.close()


def generate_student_report_card(parent, admission_no, level, save_path=None, progress_callback=None, exam_id=None):
    """
    Generate a single-student PDF report card using the existing report-book layout.
    Prefer the latest completed exam, but fall back to the latest open/closed
    exam with marks so student report viewing does not return blank while an
    exam is still active.
    """
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
    class_master = profile["class_master"]
    head_teacher_signature = profile["head_teacher_signature"]
    academic_master_signature = profile["academic_master_signature"]
    discipline_master_signature = profile["discipline_master_signature"]
    class_master_signature = profile["class_master_signature"]
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

    # Fetch manual remarks
    cur.execute("""
        SELECT teacher_remarks, headteacher_remarks, developmental_notes
        FROM exam_remarks
        WHERE admission_no = ? AND exam_id = ?
    """, (student_adm, exam_id))
    remarks_row = cur.fetchone()
    teacher_remarks, head_remarks, dev_notes = remarks_row if remarks_row else (None, None, None)

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

    class_students = sorted(
        class_students,
        key=lambda x: (
            -_numeric_or_zero(x.get('average')),
            -_numeric_or_zero(x.get('total_marks')),
            x.get('admission', '')
        )
    )
    for pos, student in enumerate(class_students, start=1):
        student['class_position'] = pos

    ready_students = [s for s in class_students if s['status'] == 'READY']
    total_in_class = len(ready_students)

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
        canvas.setLineWidth(2.5)
        x = doc.leftMargin - 8
        y = doc.bottomMargin - 8
        w = doc.pagesize[0] - doc.leftMargin - doc.rightMargin + 16
        h = doc.pagesize[1] - doc.topMargin - doc.bottomMargin + 16
        canvas.rect(x, y, w, h)
        canvas.restoreState()

    doc = SimpleDocTemplate(
        save_path, pagesize=STUDENT_PAGE_SIZE,
        rightMargin=STUDENT_R_MARGIN, leftMargin=STUDENT_L_MARGIN,
        topMargin=STUDENT_T_MARGIN, bottomMargin=STUDENT_B_MARGIN
    )

    class_position = target_student.get('class_position', target_student.get('position', '-'))
    overall_grade = get_grade(average, level=level) if marks_vals else '-'
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
        class_master=class_master,
        student_comment=student_comment,
        include_page_break=False,
        school_stamp=school_stamp,
        head_teacher_signature=head_teacher_signature,
        academic_master_signature=academic_master_signature,
        discipline_master_signature=discipline_master_signature,
        class_master_signature=class_master_signature,
        teacher_remarks=teacher_remarks,
        head_remarks=head_remarks,
        dev_notes=dev_notes
    )

    keeper = KeepInFrame(
        doc.width,
        doc.height,
        content,
        mode='shrink',
        hAlign='CENTER',
        vAlign='TOP'
    )

    try:
        report_progress(90, "Rendering PDF")
        doc.build([keeper], onFirstPage=on_page, onLaterPages=on_page)
        report_progress(100, "Report card generated")
        return True, save_path
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


# ======================================================================
# BUILDER HELPERS
# ======================================================================

def _build_header(ST, school_name, motto, addr, phone, email, website,
                  logo_path, use_logo, year, term, exam, level, cls,
                  stream, gen_date):
    """Three-column header: contacts | logo+name | academic info."""

    # ── Left: School Contacts ──
    contact_lines = ['<b><u>SCHOOL CONTACTS</u></b>']
    if addr:
        contact_lines.append(addr.replace('\n', '<br/>'))
    if phone:
        contact_lines.append(phone)
    if email:
        contact_lines.append(email)
    if website:
        contact_lines.append(website)
    left = Paragraph('<br/>'.join(contact_lines), ST['small'])

    # ── Center: Logo + Name + Motto ──
    center_parts = []
    if use_logo and logo_path:
        try:
            logo = Image(logo_path, width=0.7 * inch, height=0.7 * inch)
            center_parts.append([logo])
        except Exception as e:
            print(f"[WARNING] Could not load logo '{logo_path}': {e}")
    center_parts.append(
        [Paragraph(f'<b>{school_name.upper()}</b>', ST['title'])])
    if motto:
        center_parts.append(
            [Paragraph(f'<i>{motto}</i>', ST['motto'])])

    center = Table(center_parts, colWidths=[4.2 * inch])
    center.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
    ]))

    # ── Right: Academic Information ──
    term_display = term if term else ''
    acad_text = (
        f'<b><u>ACADEMIC INFORMATION</u></b><br/>'
        f'<b>ACADEMIC YEAR</b> : {year}<br/>'
        f'<b>TERM</b> : {term_display}<br/>'
        f'<b>EXAMINATION</b> : {exam}<br/>'
        f'<b>LEVEL</b> : {level}<br/>'
        f'<b>CLASS</b> : {cls}<br/>'
        f'<b>STREAM</b> : {stream}<br/>'
        f'<b>DATE</b> : {gen_date}'
    )
    right = Paragraph(acad_text, ST['small'])

    header = Table(
        [[left, center, right]],
        colWidths=[2.6 * inch, 4.8 * inch, 3.0 * inch])
    header.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (1, 0), (1, 0), 'CENTER'),
        ('LINEBELOW', (0, 0), (-1, 0), 1.5, NAVY),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    return header


def _build_student_page_header(ST, school_name, motto, addr, phone, email, website,
                               logo_path, use_logo, year, term, exam, level, cls,
                               stream, gen_date):
    contact_lines = []
    if phone:
        contact_lines.append(phone)
    if email:
        contact_lines.append(email)
    if website:
        contact_lines.append(website)
    if addr:
        contact_lines.append(addr)

    left = Table([[
        Paragraph('<b>SCHOOL</b>', ST['tiny_b'])
    ]], colWidths=[0.92 * inch])
    left.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.5, GRID_COLOR),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))

    if use_logo and logo_path:
        try:
            logo = Image(logo_path, width=0.8 * inch, height=0.8 * inch)
            left = Table([[logo]], colWidths=[0.92 * inch])
            left.setStyle(TableStyle([
                ('BOX', (0, 0), (-1, -1), 0.5, GRID_COLOR),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 2),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ]))
        except Exception as e:
            print(f"[WARNING] Could not load logo '{logo_path}': {e}")

    center_lines = [Paragraph(f'<b>{school_name.upper()}</b>', ST['title'])]
    if motto:
        center_lines.append(Paragraph(f'{motto}', ST['motto']))
    center = Table([[flow] for flow in center_lines], colWidths=[STUDENT_PAGE_W * 0.64])
    center.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
    ]))

    right_rows = [[Paragraph('<b>CONTACTS</b>', ST['tiny_b'])]]
    for text in contact_lines:
        right_rows.append([Paragraph(text, ST['tiny'])])
    right = Table(right_rows, colWidths=[1.5 * inch])
    right.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.5, GRID_COLOR),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))

    header = Table([[left, center, right]],
                   colWidths=[0.98 * inch, STUDENT_PAGE_W - (0.98 * inch + 1.5 * inch), 1.5 * inch])
    header.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (1, 0), (1, 0), 'CENTER'),
        ('LINEBELOW', (0, 0), (-1, 0), 1.0, NAVY),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
    ]))
    return header


def _build_student_page_identity(ST, student_name, admission_no, exam_no, gender,
                                  class_name, stream, level, report_id, status,
                                  year_name, term_name, exam_name, gen_date):
    profile = _student_info_block(
        ST,
        "STUDENT PROFILE",
        [
            ("Student Name", student_name),
            ("Gender", gender or "-"),
            ("Level", level),
        ],
    )

    context = _student_info_block(
        ST,
        "ACADEMIC CONTEXT",
        [
            ("Academic Year", year_name),
            ("Term", term_name),
            ("Examination", exam_name),
            ("Class", class_name),
            ("Stream", stream),
            ("Admission No", admission_no),
            ("Exam No", exam_no or "-"),
        ],
    )

    return Table([[profile], [context]], colWidths=[STUDENT_PAGE_W])


def _student_info_block(ST, title, rows, width=STUDENT_PAGE_W):
    body_rows = []
    for label, value in rows:
        body_rows.append([
            Paragraph(label, ST['label']),
            Paragraph(':', ST['value']),
            Paragraph(_safe_text(value), ST['value'])
        ])
    body = Table(body_rows, colWidths=[width * 0.42, width * 0.04, width * 0.54])
    body.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.6, NAVY),
        ('INNERGRID', (0, 0), (-1, -1), 0.35, GRID_COLOR),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))

    title_tbl = Table([[Paragraph(title, ST['section_hdr'])]], colWidths=[width])
    title_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), NAVY),
        ('TEXTCOLOR', (0, 0), (-1, -1), WHITE),
        ('BOX', (0, 0), (-1, -1), 0.6, NAVY),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
    ]))

    return Table([[title_tbl], [body]], colWidths=[width])


def _build_student_page_metrics(ST, position, total_students, division, points, average, status):
    rows = [[
        Paragraph('RANK', ST['summary_label']),
        Paragraph('DIVISION', ST['summary_label']),
        Paragraph('POINTS', ST['summary_label']),
        Paragraph('PERCENTAGE', ST['summary_label']),
        Paragraph('STATUS', ST['summary_label']),
    ], [
        Paragraph(f"{_safe_text(position)} / {_safe_text(total_students)}", ST['summary_value']),
        Paragraph(_safe_text(division), ST['summary_value']),
        Paragraph(_safe_text(points), ST['summary_value']),
        Paragraph(f"{_safe_text(average)}%", ST['summary_value']),
        Paragraph(_safe_text(status), ST['summary_value']),
    ]]
    tbl = Table(rows, colWidths=[STUDENT_PAGE_W / 5.0] * 5)
    tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), NAVY_LIGHT),
        ('TEXTCOLOR', (0, 0), (-1, 0), NAVY),
        ('BOX', (0, 0), (-1, -1), 0.6, NAVY),
        ('GRID', (0, 0), (-1, -1), 0.45, GRID_COLOR),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    return tbl


def _get_remark(grade):
    remarks = {
        'A': 'Excellent',
        'B': 'Very Good',
        'C': 'Good',
        'D': 'Satisfactory',
        'E': 'Fair',
        'S': 'Pass',
        'F': 'Fail'
    }
    return remarks.get(grade, '-')


def _build_student_page_results(ST, short_names, marks, grades):
    if short_names:
        rows = [
            [Paragraph('ITEM', ST['table_head'])] + [Paragraph(sn, ST['table_head']) for sn in short_names],
            [Paragraph('MARKS (%)', ST['table_head'])] + [Paragraph(str(mark), ST['table_body']) for mark in marks],
            [Paragraph('GRADE', ST['table_head'])] + [Paragraph(g, ST['table_body']) for g in grades],
        ]
        label_w = 1.0 * inch
        subject_w = max(0.58 * inch, (STUDENT_PAGE_W - label_w) / max(len(short_names), 1))
        col_widths = [label_w] + [subject_w] * len(short_names)
    else:
        rows = [
            [Paragraph('ITEM', ST['table_head']), Paragraph('-', ST['table_head'])],
            [Paragraph('MARKS (%)', ST['table_head']), Paragraph('-', ST['table_body'])],
            [Paragraph('GRADE', ST['table_head']), Paragraph('-', ST['table_body'])],
        ]
        col_widths = [1.0 * inch, STUDENT_PAGE_W - 1.0 * inch]

    table = Table(rows, colWidths=col_widths)
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
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))
    return table


def _build_student_page_totals(ST, total_marks, average, overall_grade, division, points):
    rows = [[
        Paragraph('TOTAL MARKS', ST['summary_label']),
        Paragraph('AVERAGE', ST['summary_label']),
        Paragraph('OVERALL GRADE', ST['summary_label']),
        Paragraph('DIVISION', ST['summary_label']),
        Paragraph('AGGR. POINTS', ST['summary_label']),
    ], [
        Paragraph(_safe_text(total_marks), ST['summary_value']),
        Paragraph(f"{average:.2f}%", ST['summary_value']),
        Paragraph(_safe_text(overall_grade), ST['summary_value']),
        Paragraph(_safe_text(division), ST['summary_value']),
        Paragraph(_safe_text(points), ST['summary_value']),
    ]]
    table = Table(rows, colWidths=[STUDENT_PAGE_W / 5.0] * 5)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), LIGHT_BG),
        ('BOX', (0, 0), (-1, -1), 0.5, NAVY),
        ('GRID', (0, 0), (-1, -1), 0.3, GRID_COLOR),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    return table


def _build_student_page_requirements(ST, requirements_data, use_req, opening_date="", closing_date=""):
    title = Table([[Paragraph('STUDENT REQUIREMENTS / REMINDERS', ST['section_hdr'])]],
                  colWidths=[STUDENT_PAGE_W])
    title.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), NAVY),
        ('TEXTCOLOR', (0, 0), (-1, -1), WHITE),
        ('BOX', (0, 0), (-1, -1), 0.6, NAVY),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
    ]))

    rows = [[
        Paragraph('ITEM / REQUIREMENT', ST['table_head']),
        Paragraph('DESCRIPTION', ST['table_head']),
        Paragraph('STATUS', ST['table_head']),
        Paragraph('REMARKS', ST['table_head']),
    ]]
    if use_req and requirements_data:
        for idx, (item, qty) in enumerate(requirements_data, start=1):
            rows.append([
                Paragraph(_safe_text(item), ST['tiny_left']),
                Paragraph(_safe_text(qty), ST['tiny_left']),
                Paragraph('\u2713', ST['table_body']),
                Paragraph('', ST['table_body']),
            ])
    else:
        rows.append([
            Paragraph('-', ST['table_body']),
            Paragraph('No requirements available for this class/term.', ST['tiny_left']),
            Paragraph('-', ST['table_body']),
            Paragraph('-', ST['table_body']),
        ])

    body = Table(rows, colWidths=[
        2.0 * inch,
        STUDENT_PAGE_W - (2.0 * inch + 0.6 * inch + 1.0 * inch),
        0.6 * inch,
        1.0 * inch,
    ])
    body.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.55, NAVY),
        ('GRID', (0, 0), (-1, -1), 0.35, GRID_COLOR),
        ('BACKGROUND', (0, 0), (-1, 0), NAVY_LIGHT),
        ('ALIGN', (2, 0), (2, -1), 'CENTER'),
        ('ALIGN', (3, 0), (3, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))
    return Table([[title], [body]], colWidths=[STUDENT_PAGE_W])




def _build_student_page_comments(ST, head_teacher, academic_master, student_comment, stamp_path=None, average=0, division='-', level='O_LEVEL', teacher_remarks=None, head_remarks=None, dev_notes=None):
    title = Table([[Paragraph('COMMENTS', ST['section_hdr'])]],
                  colWidths=[STUDENT_PAGE_W])
    title.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), NAVY),
        ('TEXTCOLOR', (0, 0), (-1, -1), WHITE),
        ('BOX', (0, 0), (-1, -1), 0.5, NAVY),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
    ]))

    smart_comment = get_default_remark(average, division, level)
    
    # Defaults if not provided
    if not teacher_remarks:
        teacher_remarks = smart_comment
    if not head_remarks:
        head_remarks = get_headteacher_remark(division)
    if not dev_notes:
        dev_notes = get_developmental_note(average)

    # Priority for development/general comment: Developmental Notes > Student General Comment
    main_comment = dev_notes if dev_notes else student_comment

    stamp = ""
    if stamp_path and os.path.exists(stamp_path):
        try:
            stamp = Image(stamp_path, width=0.8*inch, height=0.8*inch)
        except:
            pass

    # Teacher Remarks fallback
    t_rem_display = f"<i>{teacher_remarks}</i>" if teacher_remarks else '<font color="#9AA4B2">______________________________________________</font>'
    h_rem_display = f"<i>{head_remarks}</i>" if head_remarks else '<font color="#9AA4B2">______________________________________________</font>'

    rows = [
        [
            Paragraph('<b>Developmental Note</b>', ST['label']),
            Paragraph(main_comment, ST['student_comment']),
            stamp,
        ],
        [
            Paragraph('<b>CLASS TEACHER COMMENT</b>', ST['label']),
            Paragraph(t_rem_display, ST['comment']),
            Paragraph('<font color="#9AA4B2">Reviewed below</font>', ST['tiny_left']),
        ],
        [
            Paragraph('<b>ACADEMIC MASTER COMMENT</b>', ST['label']),
            Paragraph('<font color="#9AA4B2">______________________________________________</font>', ST['comment']),
            Paragraph('<font color="#9AA4B2">Reviewed below</font>', ST['tiny_left']),
        ],
        [
            Paragraph('<b>HEAD TEACHER COMMENT</b>', ST['label']),
            Paragraph(h_rem_display, ST['comment']),
            Paragraph('<font color="#9AA4B2">Reviewed below</font>', ST['tiny_left']),
        ],
    ]
    body = Table(
        rows,
        colWidths=[1.3 * inch, STUDENT_PAGE_W - 1.3 * inch - 1.35 * inch, 1.35 * inch],
        rowHeights=[0.82 * inch, 0.5 * inch, 0.5 * inch, 0.5 * inch]
    )
    body.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.5, NAVY),
        ('GRID', (0, 0), (-1, -1), 0.3, GRID_COLOR),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (2, 0), (2, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))
    return Table([[title], [body]], colWidths=[STUDENT_PAGE_W])


def _build_student_page_footer(ST):
    footer = Table([[
        Paragraph(
            '<b><i>Education is the most powerful weapon which you can use to change the world.</i></b>',
            ST['note']
        )
    ]], colWidths=[STUDENT_PAGE_W])
    footer.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.45, GRID_COLOR),
        ('BACKGROUND', (0, 0), (-1, -1), NAVY_LIGHT),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    return footer


def _normalize_gender_label(gender):
    gender_text = (gender or '').strip().lower()
    if gender_text.startswith('m'):
        return 'boys'
    if gender_text.startswith('f'):
        return 'girls'
    return 'students'


def _safe_text(value):
    if value is None:
        return '-'
    text = str(value).strip()
    return text if text else '-'


def _build_student_page_dates(ST, opening_date="", closing_date=""):
    rows = [[
        Paragraph(f"<b>OPENING DATE</b><br/>{_safe_text(opening_date)}", ST['label']),
        Paragraph(f"<b>CLOSING DATE</b><br/>{_safe_text(closing_date)}", ST['label']),
    ]]
    tbl = Table(rows, colWidths=[STUDENT_PAGE_W / 2, STUDENT_PAGE_W / 2])
    tbl.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    return tbl


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
    class_master=None, class_master_signature=None,
    teacher_remarks=None, head_remarks=None, dev_notes=None
):
    content = [
        _build_student_page_header(
            ST, school_name, school_motto, school_addr, school_phone,
            school_email, school_website, school_logo, use_logo,
            year_name, term_name, exam_name, level, class_name,
            student_stream, generated_date
        ),
        Spacer(1, 6),
        _build_student_page_identity(
            ST, student_name, student_adm, exam_no, student_gender,
            class_name, student_stream, level,
            f"SRMS-{year_name}-{student_adm.replace('/', '')}",
            student_status, year_name, term_name, exam_name, generated_date
        ),
        Spacer(1, 6),
        _build_student_page_metrics(
            ST, class_position, total_students, division, points, average, student_status
        ),
        Spacer(1, 6),
        _build_student_page_results(ST, short_names, marks_vals, grades_vals),
        Spacer(1, 6),
        _build_student_page_dates(ST, opening_date, closing_date),
        Spacer(1, 6),
        _build_student_page_requirements(ST, requirements_data, use_req, opening_date, closing_date),
        Spacer(1, 4),
        _build_student_page_comments(
            ST, head_teacher, academic_master, student_comment,
            stamp_path=school_stamp, average=average, division=division, level=level,
            teacher_remarks=teacher_remarks, head_remarks=head_remarks, dev_notes=dev_notes
        ),
        Spacer(1, 4),
        _build_signatures(
            ST,
            head_teacher=head_teacher,
            academic_master=academic_master,
            discipline_master=discipline_master,
            class_master=class_master,
            head_teacher_signature=head_teacher_signature,
            academic_master_signature=academic_master_signature,
            discipline_master_signature=discipline_master_signature,
            class_master_signature=class_master_signature,
            stamp_path=school_stamp,
        ),
        Spacer(1, 4),
        _build_student_page_footer(ST),
        Spacer(1, 3),
        Paragraph(
            '<b>Note:</b> This report is computer generated and requires only the head teacher signature field above.',
            ST['note']
        ),
    ]
    if include_page_break:
        content.append(PageBreak())
    return content


def _build_student_info(ST, name, adm, gender, report_id, status):
    """Bordered student information section — 2 rows."""

    info = [
        [Paragraph('<b>STUDENT NAME</b>', ST['label']),
         Paragraph(f': {name}', ST['value']),
         Paragraph('<b>ADM NO.</b>', ST['label']),
         Paragraph(f': {adm}', ST['value']),
         Paragraph('<b>GENDER</b>', ST['label']),
         Paragraph(f': {gender}', ST['value']),
         Paragraph('<b>STATUS</b>', ST['label']),
         Paragraph(f': {status}', ST['value'])],
        [Paragraph('<b>REPORT ID</b>', ST['label']),
         Paragraph(f': {report_id}', ST['value']),
         Paragraph('<b>CLASS TEACHER</b>', ST['label']),
         Paragraph(': -', ST['value']),
         Paragraph('<b>DATE OF BIRTH</b>', ST['label']),
         Paragraph(': -', ST['value']),
         '', ''],
    ]
    tbl = Table(info, colWidths=[
        1.0 * inch, 2.1 * inch, 1.0 * inch, 1.2 * inch,
        1.0 * inch, 0.8 * inch, 0.7 * inch, 0.7 * inch])
    tbl.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOX', (0, 0), (-1, -1), 1, NAVY),
        ('INNERGRID', (0, 0), (-1, -1), 0.4, GRID_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
    ]))
    return tbl


def _build_results_and_summary(ST, short_names, full_names, marks,
                               grades, total_marks, average, position,
                               total_class, gender_pos, gender_total,
                               division, points):
    """Subject results table (left) + academic summary (right)."""
    n = len(marks)

    label_w = 1.0 * inch
    sub_col_w = min(0.68 * inch,
                    max(0.48 * inch, (6.5 * inch - label_w) / max(n, 1)))
    sub_tbl_w = label_w + sub_col_w * n

    row_hdr = [Paragraph('<b>SUBJECTS</b>', ST['small_b'])]
    row_full = [Paragraph('<b>FULL NAME</b>', ST['tiny_b'])]
    row_marks = [Paragraph('<b>MARKS</b>', ST['small_b'])]
    row_grade = [Paragraph('<b>GRADE</b>', ST['small_b'])]

    for i in range(n):
        row_hdr.append(Paragraph(f'<b>{short_names[i]}</b>', ST['small_b']))
        row_full.append(Paragraph(full_names[i], ST['tiny']))
        row_marks.append(Paragraph(f'<b>{marks[i]}</b>', ST['center_b']))
        row_grade.append(Paragraph(f'<b>{grades[i]}</b>', ST['center_b']))

    col_widths = [label_w] + [sub_col_w] * n
    tbl = Table([row_hdr, row_full, row_marks, row_grade],
                colWidths=col_widths)
    tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), NAVY),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('BACKGROUND', (0, 1), (-1, 1), NAVY_LIGHT),
        ('BACKGROUND', (0, 2), (0, 2), NAVY),
        ('TEXTCOLOR', (0, 2), (0, 2), WHITE),
        ('BACKGROUND', (0, 3), (0, 3), NAVY),
        ('TEXTCOLOR', (0, 3), (0, 3), WHITE),
        ('GRID', (0, 0), (-1, -1), 0.5, NAVY),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 2),
        ('RIGHTPADDING', (0, 0), (-1, -1), 2),
    ]))

    # ── Academic summary ──
    summary_w = PAGE_W - sub_tbl_w - 6
    lw = summary_w * 0.6
    rw = summary_w * 0.4

    sum_hdr = Table(
        [[Paragraph('<b>ACADEMIC SUMMARY</b>', ST['section_hdr'])]],
        colWidths=[summary_w])
    sum_hdr.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), NAVY_LIGHT),
        ('LINEBELOW', (0, 0), (-1, 0), 1, NAVY),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))

    rows = [
        [Paragraph('<b>TOTAL MARKS</b>', ST['small_b_left']),
         Paragraph(f'<b>{total_marks}</b>', ST['right_b'])],
        [Paragraph('<b>AVERAGE (%)</b>', ST['small_b_left']),
         Paragraph(f'<b>{average}</b>', ST['right_b'])],
        [Paragraph('<b>CLASS POSITION</b>', ST['small_b_left']),
         Paragraph(f'<b>{position} / {total_class}</b>', ST['right_b'])],
        [Paragraph('<b>GENDER POSITION</b>', ST['small_b_left']),
         Paragraph(f'<b>{gender_pos} / {gender_total}</b>', ST['right_b'])],
        [Paragraph('<b>DIVISION</b>', ST['small_b_left']),
         Paragraph(f'<b>{division}</b>', ST['right_b'])],
        [Paragraph('<b>POINTS</b>', ST['small_b_left']),
         Paragraph(f'<b>{points}</b>', ST['right_b'])],
    ]
    sum_body = Table(rows, colWidths=[lw, rw])
    sum_body.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.5, NAVY),
        ('INNERGRID', (0, 0), (-1, -1), 0.4, GRID_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_BG),
    ]))

    summary_col = Table(
        [[sum_hdr], [sum_body]], colWidths=[summary_w])
    summary_col.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.5, NAVY),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))

    combined = Table(
        [[tbl, summary_col]],
        colWidths=[sub_tbl_w, summary_w + 6])
    combined.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    return combined


def _build_lower_section(ST, marks, full_names, grades,
                         requirements_data, use_req):
    """Three columns: comments | best/worst subjects | requirements."""
    col_w = PAGE_W / 3
    inner = col_w - 6

    # ── Teacher's Comments ──
    c_hdr = _section_header("TEACHER'S COMMENTS", ST, inner)
    c_body = Paragraph(
        'Class Teacher: ______________________________________<br/><br/>'
        'Academic Master: ____________________________________<br/><br/>'
        'Head Teacher: _______________________________________',
        ST['comment_body'])
    comments = _boxed([c_hdr, c_body], inner)

    # ── Best & Weakest Subjects ──
    bw_hdr = _section_header("BEST & WEAKEST SUBJECTS", ST, inner)

    if marks:
        best_i = marks.index(max(marks))
        worst_i = marks.index(min(marks))
        best_name, best_mk, best_gr = full_names[best_i], marks[best_i], grades[best_i]
        worst_name, worst_mk, worst_gr = full_names[worst_i], marks[worst_i], grades[worst_i]
    else:
        best_name = worst_name = '-'
        best_mk = worst_mk = 0
        best_gr = worst_gr = '-'

    qw = inner / 4
    bw_data = [
        [Paragraph('<b>BEST SUBJECT</b>', ST['small_b']), '',
         Paragraph('<b>WEAKEST SUBJECT</b>', ST['small_b']), ''],
        [Paragraph(best_name, ST['small_c']), '',
         Paragraph(worst_name, ST['small_c']), ''],
        [Paragraph('<b>MARKS</b>', ST['small_b']),
         Paragraph('<b>GRADE</b>', ST['small_b']),
         Paragraph('<b>MARKS</b>', ST['small_b']),
         Paragraph('<b>GRADE</b>', ST['small_b'])],
        [Paragraph(f'<b>{best_mk}</b>', ST['center_b']),
         Paragraph(f'<b>{best_gr}</b>', ST['center_b']),
         Paragraph(f'<b>{worst_mk}</b>', ST['center_b']),
         Paragraph(f'<b>{worst_gr}</b>', ST['center_b'])],
    ]
    bw_tbl = Table(bw_data, colWidths=[qw] * 4)
    bw_tbl.setStyle(TableStyle([
        ('SPAN', (0, 0), (1, 0)), ('SPAN', (2, 0), (3, 0)),
        ('SPAN', (0, 1), (1, 1)), ('SPAN', (2, 1), (3, 1)),
        ('GRID', (0, 2), (-1, -1), 0.5, NAVY),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    best_worst = _boxed([bw_hdr, bw_tbl], inner)

    # ── School Requirements ──
    rq_hdr = _section_header("SCHOOL REQUIREMENTS", ST, inner)
    rq_rows = [
        [Paragraph('<b>NO.</b>', ST['small_b']),
         Paragraph('<b>ITEM</b>', ST['small_b']),
         Paragraph('<b>STATUS</b>', ST['small_b'])]]
    if use_req and requirements_data:
        for i, (item, qty) in enumerate(requirements_data, 1):
            rq_rows.append([
                Paragraph(str(i), ST['small_c']),
                Paragraph(item, ST['small']),
                Paragraph('\u2713', ST['small_c'])])
    else:
        rq_rows.append([
            Paragraph('-', ST['small_c']),
            Paragraph('-', ST['small']),
            Paragraph('-', ST['small_c'])])

    rq_tbl = Table(rq_rows, colWidths=[
        0.3 * inch, inner - 0.3 * inch - 0.5 * inch, 0.5 * inch])
    rq_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), NAVY_LIGHT),
        ('GRID', (0, 0), (-1, -1), 0.4, GRID_COLOR),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (2, 0), (2, -1), 'CENTER'),
        ('ALIGN', (1, 1), (1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    reqs = _boxed([rq_hdr, rq_tbl], inner)

    row = Table([[comments, best_worst, reqs]],
                colWidths=[col_w, col_w, col_w])
    row.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    return row


def _build_signatures(
    ST,
    head_teacher,
    academic_master,
    discipline_master,
    class_master,
    head_teacher_signature=None,
    academic_master_signature=None,
    discipline_master_signature=None,
    class_master_signature=None,
    stamp_path=None,
):
    """Signature section with one official signature and school stamp."""
    col_w = (PAGE_W - 12) / 2
    sig_style = ST.get('tiny_left') or ST.get('sig')
    sig_hdr_style = ST.get('tiny_b') or ST.get('sig_hdr')

    head_signature = _safe_image(head_teacher_signature, 1.15 * inch, 0.35 * inch)
    if head_signature is None:
        head_signature = Paragraph('Signature: ____________________', sig_style)

    head_block = Table(
        [
            [Paragraph('<b>HEAD TEACHER / HEADMASTER SIGNATURE</b>', sig_hdr_style)],
            [head_signature],
            [Paragraph(f'Name: {head_teacher}' if head_teacher else 'Name: ____________________', sig_style)],
        ],
        colWidths=[col_w - 10],
        rowHeights=[0.24 * inch, 0.42 * inch, 0.26 * inch],
    )
    head_block.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('LEFTPADDING', (0, 0), (-1, -1), 2),
        ('RIGHTPADDING', (0, 0), (-1, -1), 2),
        ('TOPPADDING', (0, 0), (-1, -1), 1),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
    ]))

    stamp_image = _safe_image(stamp_path, 0.62 * inch, 0.62 * inch)
    if stamp_image is None:
        stamp_image = Paragraph('STAMP', sig_hdr_style)

    stamp_block = Table(
        [
            [Paragraph('<b>SCHOOL OFFICIAL STAMP</b>', sig_hdr_style)],
            [stamp_image],
        ],
        colWidths=[col_w - 10],
        rowHeights=[0.24 * inch, 0.58 * inch],
    )
    stamp_block.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('LEFTPADDING', (0, 0), (-1, -1), 2),
        ('RIGHTPADDING', (0, 0), (-1, -1), 2),
        ('TOPPADDING', (0, 0), (-1, -1), 1),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
    ]))

    tbl = Table([[head_block, stamp_block]], colWidths=[col_w, col_w])
    tbl.setStyle(TableStyle([
        ('LINEABOVE', (0, 0), (-1, 0), 1, NAVY),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    return tbl


def _section_header(title, ST, width):
    t = Table(
        [[Paragraph(f'<b>{title}</b>', ST['section_hdr'])]],
        colWidths=[width])
    t.setStyle(TableStyle([
        ('LINEBELOW', (0, 0), (-1, 0), 1, NAVY),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
    ]))
    return t


def _boxed(items, width):
    rows = [[item] for item in items]
    t = Table(rows, colWidths=[width])
    t.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.5, NAVY),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))
    return t
