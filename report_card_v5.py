import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from database import connect
from settings_page import get_setting
from watermark import draw_watermark
from ranking_engine import compute_student_scores
from grade_utils import get_grade, get_points


def generate_report_book(parent, exam_id, class_name, save_path):
    """
    Core PDF Generation Logic
    Generates a single PDF containing one page per student.
    """
    conn = connect()
    cur = conn.cursor()

    cur.execute("""
        SELECT school_name, school_motto, school_address, school_phone, school_email,
               school_logo, school_stamp, head_teacher, academic_master, watermark_text
        FROM school_profile
        LIMIT 1
    """)
    profile = cur.fetchone()

    school_name = profile[0] if profile else "SCHOOL MANAGEMENT SYSTEM"
    school_motto = profile[1] if profile and profile[1] else ""
    school_addr = profile[2] if profile else "-"
    school_phone = profile[3] if profile else ""
    school_email = profile[4] if profile else ""
    school_logo = profile[5] if profile and profile[5] and os.path.exists(profile[5]) else None
    school_stamp = profile[6] if profile and profile[6] and os.path.exists(profile[6]) else None
    head_teacher = profile[7] if profile else ""
    academic_master = profile[8] if profile else ""
    watermark_text = profile[9] if profile and profile[9] else "CONFIDENTIAL"

    contact_info = " | ".join([item for item in [school_addr, school_phone, school_email] if item])

    cur.execute("""
        SELECT t.term_name, y.year_name, e.exam_name, e.level, t.id, t.academic_year_id
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

    cur.execute("""
        SELECT item_name, quantity
        FROM requirements
        WHERE academic_year_id=? AND term_id=? AND level=? AND (class_name=? OR class_name='-- All Classes --')
    """, (year_id, term_id, level, class_name))
    requirements_data = cur.fetchall()

    ranking_data = compute_student_scores(level, exam_id)
    class_students = [s for s in ranking_data if s.get('class') == class_name]

    if not class_students:
        conn.close()
        return False, "No students found in this class with results."

    use_watermark = get_setting('show_watermark', '1') == '1'
    use_req = get_setting('show_requirements', '1') == '1'

    def on_page(canvas, doc):
        if use_watermark:
            draw_watermark(canvas, doc, school_name, year_name, watermark_text)
        canvas.saveState()
        canvas.setFont('Helvetica', 8)
        footer_text = f"{school_name} | Page {canvas.getPageNumber()}"
        canvas.drawRightString(doc.pagesize[0] - doc.rightMargin, 15, footer_text)
        canvas.restoreState()

    doc = SimpleDocTemplate(save_path, pagesize=landscape(A4), rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    elements = []
    styles = getSampleStyleSheet()

    style_center = ParagraphStyle(name='Center', alignment=TA_CENTER, fontSize=11, leading=14)
    style_header = ParagraphStyle(name='Header', alignment=TA_CENTER, fontSize=18, fontName='Helvetica-Bold', leading=22)
    style_subheader = ParagraphStyle(name='SubHeader', alignment=TA_CENTER, fontSize=13, leading=16)
    style_label = ParagraphStyle(name='Label', fontName='Helvetica-Bold', fontSize=10, alignment=TA_LEFT)
    style_value = ParagraphStyle(name='Value', fontSize=10, alignment=TA_LEFT)
    style_note = ParagraphStyle(name='Note', fontSize=9, leading=12, alignment=TA_LEFT)

    for student in class_students:
        adm = student['admission']

        header_cells = []
        if school_logo:
            try:
                logo = Image(school_logo, width=1.0 * inch, height=1.0 * inch)
                header_cells.append(logo)
            except Exception as e:
                print(f"[WARNING] Could not load school logo '{school_logo}': {e}")
                header_cells.append(Paragraph('', styles['Normal']))
        else:
            header_cells.append(Paragraph('', styles['Normal']))

        school_info = [f"<b>{school_name.upper()}</b>"]
        if school_motto:
            school_info.append(f"<i>{school_motto}</i>")
        if contact_info:
            school_info.append(contact_info)
        school_info.append(f"<b>{exam_name.upper()}</b>")
        school_info.append(f"{term_name} - {year_name}")

        header_cells.append(Paragraph('<br/>'.join(school_info), style_center))

        header_table = Table([header_cells], colWidths=[1.2 * inch, 5.4 * inch])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (1, 0), (1, 0), 'CENTER')
        ]))
        elements.append(header_table)
        elements.append(Spacer(1, 0.12 * inch))
        elements.append(HRFlowable(width='100%', thickness=1, color=colors.black, spaceBefore=5, spaceAfter=8))

        cur.execute("SELECT full_name, gender, stream FROM students WHERE admission_no=?", (adm,))
        s_extra = cur.fetchone() or [student.get('name', ''), student.get('gender', ''), '']

        details_data = [
            [Paragraph('<b>Admission No:</b>', style_label), adm, Paragraph('<b>Gender:</b>', style_label), s_extra[1] or '-'],
            [Paragraph('<b>Student Name:</b>', style_label), s_extra[0], Paragraph('<b>Stream:</b>', style_label), s_extra[2] or '-'],
            [Paragraph('<b>Class:</b>', style_label), class_name, Paragraph('<b>Level:</b>', style_label), level],
            [Paragraph('<b>Exam:</b>', style_label), exam_name, Paragraph('<b>Term / Year:</b>', style_label), f"{term_name} - {year_name}"]
        ]
        dt = Table(details_data, colWidths=[1.25 * inch, 2.05 * inch, 1.25 * inch, 2.05 * inch])
        dt.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(dt)
        elements.append(Spacer(1, 0.18 * inch))

        cur.execute("""
            SELECT r.subject_name,
                   COALESCE(s.subject_short_name, r.subject_name),
                   r.marks
            FROM results r
            LEFT JOIN subjects s ON s.subject_name = r.subject_name AND s.level = ?
            WHERE r.admission_no=? AND r.exam_id=?
            ORDER BY r.subject_name
        """, (level, adm, exam_id))
        marks_rows = cur.fetchall()
        subjects = []
        marks_row = ["MARKS"]
        grades_row = ["GRADE"]

        for _, short_name, mark in marks_rows:

            grade = get_grade(
                mark,
                level=level
            )

            subjects.append(short_name)
            marks_row.append(str(mark))
            grades_row.append(grade)

        results_data = [
            ["SUBJECT"] + subjects,
            marks_row,
            grades_row
        ]

        total_cols = len(results_data[0])

        results_table = Table(
            results_data,
            colWidths=[
                9.6 * inch / total_cols
            ] * total_cols
        )

        results_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0),
             colors.HexColor('#D9E2F3')),
            ('FONTNAME', (0, 0), (-1, 0),
             'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (0, -1),
             'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1),
             0.8, colors.black),
            ('ALIGN', (0, 0), (-1, -1),
             'CENTER'),
            ('VALIGN', (0, 0), (-1, -1),
             'MIDDLE'),
            ('FONTSIZE', (0, 0), (-1, -1),
             8),
            ('BOTTOMPADDING', (0, 0), (-1, -1),
             5),
            ('TOPPADDING', (0, 0), (-1, -1),
             5),
        ]))

        elements.append(
            Paragraph(
                '<b>SUBJECT RESULTS</b>',
                style_subheader
            )
        )

        elements.append(results_table)

        elements.append(
            Spacer(
                1,
                0.10 * inch
            )
        )


        summary_data = [
            ["POSITION", "DIVISION", "POINTS", "AVERAGE", "STATUS"],
            [str(student['position']), str(student['division']), str(student['points']), str(student['average']), student['status']]
        ]
        summary_table = Table(summary_data, colWidths=[1.2 * inch, 1.2 * inch, 1.2 * inch, 1.2 * inch, 1.2 * inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.whitesmoke),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(Paragraph('<b>ACADEMIC SUMMARY</b>', style_subheader))
        elements.append(summary_table)
        elements.append(Spacer(1, 0.2 * inch))

        if use_req:
            elements.append(Paragraph('<b>SCHOOL REQUIREMENTS</b>', style_subheader))
            req_data = [["ITEM", "QUANTITY"]]
            if requirements_data:
                for item, qty in requirements_data:
                    req_data.append([item, qty])
            else:
                req_data.append(["-", "-"])

            req_table = Table(req_data, colWidths=[4.0 * inch, 1.6 * inch])
            req_table.setStyle(TableStyle([
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
            ]))
            elements.append(req_table)
            elements.append(Spacer(1, 0.2 * inch))

        elements.append(Paragraph('<b>TEACHER COMMENTS</b>', style_subheader))
        comments = [
            [Paragraph('Class Teacher: ________________________________________________________________', style_value)],
            [Paragraph('Academic Master: _____________________________________________________________', style_value)],
            [Paragraph('Head Teacher: ________________________________________________________________', style_value)]
        ]

        if school_stamp:
            try:
                stamp_image = Image(school_stamp, width=1.2 * inch, height=1.2 * inch)
                elements.append(Spacer(1, 0.15 * inch))
                elements.append(stamp_image)
            except Exception as e:
                print(f"[WARNING] Could not load school stamp '{school_stamp}': {e}")


    try:
        doc.build(elements, onFirstPage=on_page, onLaterPages=on_page)
        conn.close()
        return True, 'Report Book generated successfully.'
    except Exception as e:
        conn.close()
        return False, str(e)
