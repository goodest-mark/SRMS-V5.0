import os
import tempfile
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
    PageBreak, Image
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from database import connect
from settings_page import get_setting
from watermark import draw_watermark
from ranking_engine import compute_student_scores
from grade_utils import get_grade

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

_styles_cache = {}


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


def generate_report_book(parent, exam_id, class_name, save_path):
    """
    Generates professional report cards matching the SRMS V5 layout.
    One landscape A4 page per student in a single PDF.
    """
    conn = connect()
    cur = conn.cursor()
    ST = _get_styles()

    # ── Fetch school profile ──
    cur.execute("""
        SELECT school_name, school_motto, school_address, school_phone,
               school_email, school_logo, school_stamp, head_teacher,
               academic_master, watermark_text, school_website
        FROM school_profile LIMIT 1
    """)
    profile = cur.fetchone()

    school_name = profile[0] if profile else "SCHOOL MANAGEMENT SYSTEM"
    school_motto = profile[1] if profile and profile[1] else ""
    school_addr = profile[2] if profile else "-"
    school_phone = profile[3] if profile else ""
    school_email = profile[4] if profile else ""
    school_logo = (profile[5] if profile and profile[5]
                   and os.path.exists(profile[5]) else None)
    school_stamp = (profile[6] if profile and profile[6]
                    and os.path.exists(profile[6]) else None)
    head_teacher = profile[7] if profile else ""
    academic_master = profile[8] if profile else ""
    watermark_text = (profile[9] if profile and profile[9]
                      else "CONFIDENTIAL")
    try:
        school_website = profile[10] if profile and len(profile) > 10 and profile[10] else ""
    except (IndexError, TypeError):
        school_website = ""

    # ── Academic context ──
    cur.execute("""
        SELECT t.term_name, y.year_name, e.exam_name, e.level,
               t.id, t.academic_year_id
        FROM exams e
        JOIN terms t ON e.term_id = t.id
        JOIN academic_years y ON t.academic_year_id = y.id
        WHERE e.id = ?
    """, (exam_id,))
    context = cur.fetchone()
    if not context:
        conn.close()
        return False, "Selected exam does not exist."

    term_name, year_name, exam_name, level, term_id, year_id = context

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

    class_students = sorted(
        class_students,
        key=lambda x: (
            -float(x.get('average', 0) or 0),
            -float(x.get('total_marks', 0) or 0),
            x.get('admission', '')
        )
    )
    for pos, student in enumerate(class_students, start=1):
        student['class_position'] = pos

    ready_students = [s for s in class_students if s['status'] == 'READY']
    total_in_class = len(ready_students)

    # Gender position computation
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

    # ── Settings ──
    use_watermark = get_setting('show_watermark', '1') == '1'
    use_req = get_setting('show_requirements', '1') == '1'
    use_logo = get_setting('show_logo', '1') == '1'
    generated_date = datetime.now().strftime("%d %B %Y")

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

    doc = SimpleDocTemplate(
        save_path, pagesize=PAGE_SIZE,
        rightMargin=R_MARGIN, leftMargin=L_MARGIN,
        topMargin=T_MARGIN, bottomMargin=B_MARGIN
    )
    elements = []

    for student in class_students:
        adm = student['admission']

        cur.execute(
            "SELECT full_name, gender, stream FROM students WHERE admission_no=?",
            (adm,))
        s_row = cur.fetchone()
        student_name = s_row[0] if s_row else student.get('name', '')
        student_gender = s_row[1] if s_row else student.get('gender', '')
        student_stream = (s_row[2] if s_row and s_row[2] else '-')

        # ── HEADER ──
        elements.append(_build_header(
            ST, school_name, school_motto, school_addr, school_phone,
            school_email, school_website, school_logo, use_logo,
            year_name, term_name, exam_name, level, class_name,
            student_stream, generated_date
        ))
        elements.append(Spacer(1, 6))

        # ── STUDENT INFORMATION ──
        report_id = f"SRMS-{year_name}-{adm.replace('/', '')}"
        elements.append(_build_student_info(
            ST, student_name, adm, student_gender, report_id,
            student['status']))
        elements.append(Spacer(1, 6))

        # ── RESULTS + ACADEMIC SUMMARY ──
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
            short_names.append(sn if sn != fn else fn[:4].upper())
            marks_vals.append(mk)
            grades_vals.append(g)

        total_marks = sum(marks_vals) if marks_vals else 0
        num_subj = len(marks_vals)
        average = round(total_marks / num_subj, 2) if num_subj else 0

        gender_pos = gender_positions.get(adm, '-')
        gender_total = gender_counts.get(student_gender, '-')

        class_position = student.get('class_position', student.get('position', '-'))
        elements.append(_build_results_and_summary(
            ST, short_names, full_names, marks_vals, grades_vals,
            total_marks, average, class_position, total_in_class,
            gender_pos, gender_total, student['division'],
            student['points']))
        elements.append(Spacer(1, 6))

        # ── COMMENTS / BEST-WORST / REQUIREMENTS ──
        elements.append(_build_lower_section(
            ST, marks_vals, full_names, grades_vals,
            requirements_data, use_req))
        elements.append(Spacer(1, 6))

        # ── SIGNATURES ──
        elements.append(_build_signatures(
            ST, head_teacher, academic_master, school_stamp))
        elements.append(Spacer(1, 4))

        # ── FOOTER NOTE ──
        elements.append(Paragraph(
            '<b>Note:</b> <i>This report is computer generated and does '
            'not require a signature except the above.</i>',
            ST['note']))

        elements.append(PageBreak())

    try:
        doc.build(elements, onFirstPage=on_page, onLaterPages=on_page)
        return True, 'Report cards generated successfully.'
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()


def generate_student_report_card(parent, admission_no, level, save_path=None, progress_callback=None):
    """
    Generate a single-student PDF report card using the existing report-book layout.
    The latest completed exam for the student's class is used as the report context.
    """
    conn = connect()
    cur = conn.cursor()
    ST = _get_styles()

    def report_progress(percent, message):
        if progress_callback is not None:
            progress_callback(int(percent), message)

    cur.execute("""
        SELECT school_name, school_motto, school_address, school_phone,
               school_email, school_logo, school_stamp, head_teacher,
               academic_master, watermark_text, school_website
        FROM school_profile LIMIT 1
    """)
    profile = cur.fetchone()

    school_name = profile[0] if profile else "SCHOOL MANAGEMENT SYSTEM"
    school_motto = profile[1] if profile and profile[1] else ""
    school_addr = profile[2] if profile else "-"
    school_phone = profile[3] if profile else ""
    school_email = profile[4] if profile else ""
    school_logo = (profile[5] if profile and profile[5]
                   and os.path.exists(profile[5]) else None)
    school_stamp = (profile[6] if profile and profile[6]
                    and os.path.exists(profile[6]) else None)
    head_teacher = profile[7] if profile else ""
    academic_master = profile[8] if profile else ""
    watermark_text = (profile[9] if profile and profile[9]
                      else "CONFIDENTIAL")
    try:
        school_website = profile[10] if profile and len(profile) > 10 and profile[10] else ""
    except (IndexError, TypeError):
        school_website = ""

    cur.execute("""
        SELECT admission_no, full_name, gender, class, stream, level
        FROM students
        WHERE admission_no=? AND level=?
    """, (admission_no, level))
    student_row = cur.fetchone()
    if not student_row:
        conn.close()
        return False, "Student record was not found."
    report_progress(10, "Loading student record")

    student_adm, student_name, student_gender, class_name, student_stream, _student_level = student_row

    cur.execute("""
        SELECT e.id, t.term_name, y.year_name, e.exam_name, e.level,
               t.id, t.academic_year_id
        FROM exams e
        JOIN terms t ON e.term_id = t.id
        JOIN academic_years y ON t.academic_year_id = y.id
        WHERE e.level = ?
          AND e.status = 'COMPLETED'
          AND EXISTS (
              SELECT 1
              FROM results r
              WHERE r.exam_id = e.id
                AND r.admission_no = ?
          )
        ORDER BY e.id DESC
        LIMIT 1
    """, (level, student_adm))
    context = cur.fetchone()
    if not context:
        conn.close()
        return False, "No completed exam report is available for this student yet."
    report_progress(25, "Loading exam context")

    exam_id, term_name, year_name, exam_name, _, term_id, year_id = context

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
        return False, "No completed class results are available for this student."

    class_students = sorted(
        class_students,
        key=lambda x: (
            -float(x.get('average', 0) or 0),
            -float(x.get('total_marks', 0) or 0),
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
        return False, "The selected student does not have a completed report yet."
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
        short_names.append(sn if sn != fn else fn[:4].upper())
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
    generated_date = datetime.now().strftime("%d %B %Y")

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
        save_path, pagesize=PAGE_SIZE,
        rightMargin=R_MARGIN, leftMargin=L_MARGIN,
        topMargin=T_MARGIN, bottomMargin=B_MARGIN
    )

    class_position = target_student.get('class_position', target_student.get('position', '-'))

    elements = [
        _build_header(
            ST, school_name, school_motto, school_addr, school_phone,
            school_email, school_website, school_logo, use_logo,
            year_name, term_name, exam_name, level, class_name,
            student_stream or "-", generated_date
        ),
        Spacer(1, 6),
        _build_student_info(
            ST, student_name, student_adm, student_gender, f"SRMS-{year_name}-{student_adm.replace('/', '')}",
            target_student['status']
        ),
        Spacer(1, 6),
        _build_results_and_summary(
            ST, short_names, full_names, marks_vals, grades_vals,
            total_marks, average, class_position,
            total_in_class, gender_positions.get(student_adm, '-'),
            gender_counts.get(student_gender, '-'), target_student['division'],
            target_student['points']
        ),
        Spacer(1, 6),
        _build_lower_section(
            ST, marks_vals, full_names, grades_vals,
            requirements_data, use_req
        ),
        Spacer(1, 6),
        _build_signatures(
            ST, head_teacher, academic_master, school_stamp
        ),
        Spacer(1, 4),
        Paragraph(
            '<b>Note:</b> <i>This report is computer generated and does not require a signature except the above.</i>',
            ST['note']
        ),
    ]

    try:
        report_progress(90, "Rendering PDF")
        doc.build(elements, onFirstPage=on_page, onLaterPages=on_page)
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


def _build_signatures(ST, head_teacher, academic_master, stamp_path):
    """Signature section with four columns."""
    col_w = PAGE_W / 4

    data = [
        [Paragraph('<b>CLASS TEACHER</b>', ST['sig_hdr']),
         Paragraph('<b>ACADEMIC MASTER</b>', ST['sig_hdr']),
         Paragraph('<b>HEAD TEACHER</b>', ST['sig_hdr']),
         Paragraph('<b>PARENT / GUARDIAN</b>', ST['sig_hdr'])],
        [Paragraph('Signature: ______________', ST['sig']),
         Paragraph('Signature: ______________', ST['sig']),
         Paragraph('Signature: ______________', ST['sig']),
         Paragraph('Signature: ______________', ST['sig'])],
        [Paragraph('Name: ______________', ST['sig']),
         Paragraph(
             f'Name: {academic_master}' if academic_master
             else 'Name: ______________', ST['sig']),
         Paragraph(
             f'Name: {head_teacher}' if head_teacher
             else 'Name: ______________', ST['sig']),
         Paragraph('Name: ______________', ST['sig'])],
        [Paragraph('Date: ______________', ST['sig']),
         Paragraph('Date: ______________', ST['sig']),
         Paragraph('Date: ______________', ST['sig']),
         Paragraph('Date: ______________', ST['sig'])],
    ]

    tbl = Table(data, colWidths=[col_w] * 4)
    tbl.setStyle(TableStyle([
        ('LINEABOVE', (0, 0), (-1, 0), 1, NAVY),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
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
