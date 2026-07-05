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
from ui_helpers import get_subject_short_name


def _safe_image(path, width, height):
    if not path or not os.path.exists(path):
        return None
    try:
        return Image(path, width=width, height=height)
    except Exception:
        return None


def _load_school_profile_assets(cur):
    cur.execute("""
        SELECT school_name, school_address, school_phone, school_email,
               school_logo, school_stamp, head_teacher, academic_master,
               discipline_master, class_master, head_teacher_signature,
               academic_master_signature, discipline_master_signature,
               class_master_signature, watermark_text, school_website,
               head_teacher_signature_enabled, academic_master_signature_enabled,
               discipline_master_signature_enabled, class_master_signature_enabled
        FROM school_profile LIMIT 1
    """)
    profile = cur.fetchone()
    head_signature_enabled = bool(profile and len(profile) > 16 and profile[16])
    academic_signature_enabled = bool(profile and len(profile) > 17 and profile[17])
    discipline_signature_enabled = bool(profile and len(profile) > 18 and profile[18])
    class_signature_enabled = bool(profile and len(profile) > 19 and profile[19])
    return {
        "school_name": profile[0] if profile else "SCHOOL MANAGEMENT SYSTEM",
        "school_address": profile[1] if profile else "-",
        "school_phone": profile[2] if profile else "",
        "school_email": profile[3] if profile else "",
        "school_logo": profile[4] if profile and profile[4] and os.path.exists(profile[4]) else None,
        "school_stamp": profile[5] if profile and profile[5] and os.path.exists(profile[5]) else None,
        "head_teacher": profile[6] if profile else "",
        "academic_master": profile[7] if profile else "",
        "discipline_master": profile[8] if profile else "",
        "class_master": "",
        "head_teacher_signature": profile[10] if head_signature_enabled and profile and profile[10] and os.path.exists(profile[10]) else None,
        "academic_master_signature": profile[11] if academic_signature_enabled and profile and profile[11] and os.path.exists(profile[11]) else None,
        "discipline_master_signature": profile[12] if discipline_signature_enabled and profile and profile[12] and os.path.exists(profile[12]) else None,
        "class_master_signature": None,
        "watermark_text": profile[14] if profile and profile[14] else "CONFIDENTIAL",
        "school_website": profile[15] if profile and len(profile) > 15 and profile[15] else "",
    }

def generate_report_book(parent, exam_id, class_name, save_path, progress_callback=None):
    """
    Core PDF Generation Logic
    Generates a single PDF containing one page per student.
    """
    conn = connect()
    cur = conn.cursor()

    def report_progress(percent, message):
        if progress_callback is not None:
            progress_callback(int(percent), message)

    # 1. Get School Profile
    profile = _load_school_profile_assets(cur)
    school_name = profile["school_name"]
    school_addr = profile["school_address"]
    watermark_text = profile["watermark_text"]
    school_stamp = profile["school_stamp"]
    head_teacher = profile["head_teacher"]
    academic_master = profile["academic_master"]
    discipline_master = profile["discipline_master"]
    class_master = profile["class_master"]
    head_teacher_signature = profile["head_teacher_signature"]
    academic_master_signature = profile["academic_master_signature"]
    discipline_master_signature = profile["discipline_master_signature"]
    class_master_signature = profile["class_master_signature"]
    # 2. Get Academic Context
    cur.execute("""
        SELECT t.term_name, y.year_name, e.exam_name, e.level, t.id, t.academic_year_id,
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

    # 3. Get Requirements for this class/term
    cur.execute("""
        SELECT item_name, quantity 
        FROM requirements 
        WHERE academic_year_id=? AND term_id=? AND level=? AND (class_name=? OR class_name='-- All Classes --')
    """, (year_id, term_id, level, class_name))
    requirements_data = cur.fetchall()

    # 4. Get Ranking Data (Single source of truth)
    ranking_data = compute_student_scores(level, exam_id, class_name)
    # Filter for selected class in-memory (No N+1 database queries)
    class_students = [s for s in ranking_data if s.get('class') == class_name]

    if not class_students:
        conn.close()
        return False, "No students found in this class with results."
    report_progress(10, "Preparing report pages")

    # Check Settings
    use_watermark = get_setting('show_watermark', '1') == '1'
    use_req = get_setting('show_requirements', '1') == '1'

    def on_page(canvas, doc):
        if use_watermark:
            draw_watermark(canvas, doc, school_name, year_name, watermark_text)

    # PDF SETUP
    doc = SimpleDocTemplate(save_path, pagesize=landscape(A4), rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom Styles
    style_center = ParagraphStyle(name='Center', alignment=TA_CENTER, fontSize=12, leading=14)
    style_header = ParagraphStyle(name='Header', alignment=TA_CENTER, fontSize=16, fontName='Helvetica-Bold', leading=20)
    style_label = ParagraphStyle(name='Label', fontName='Helvetica-Bold', fontSize=10, alignment=TA_LEFT)
    style_value = ParagraphStyle(name='Value', fontSize=10, alignment=TA_LEFT)

    total_students = max(len(class_students), 1)
    for index, student in enumerate(class_students, start=1):
        adm = student['admission']
        
        # --- HEADER SECTION ---
        elements.append(Paragraph(f"<b>{school_name.upper()}</b>", style_header))
        elements.append(Paragraph(school_addr, style_center))
        elements.append(Spacer(1, 0.1 * inch))
        elements.append(Paragraph(f"<b>PROGRESS REPORT BOOK: {exam_name.upper()}</b>", style_center))
        elements.append(Paragraph(f"{term_name} - {year_name}", style_center))
        elements.append(Spacer(1, 0.2 * inch))
        
        # Header Info Table (Logo/Photo space)
        header_data = [
            [Paragraph(f"<b>CLASS:</b> {class_name}", style_center), 
             Paragraph(f"<b>LEVEL:</b> {level}", style_center)]
        ]
        ht = Table(header_data, colWidths=[3*inch, 3*inch])
        ht.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER')]))
        elements.append(ht)
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.black, spaceBefore=5, spaceAfter=5))

        # --- SECTION 1: STUDENT DETAILS ---
        # Fetch full details
        cur.execute("SELECT exam_no, full_name, gender, stream FROM students WHERE admission_no=?", (adm,))
        s_extra = cur.fetchone()
        if not s_extra:
            print(f"[WARNING] Student record not found for admission_no='{adm}', skipping.")
            elements.append(PageBreak())
            continue
        
        details_data = [
            [Paragraph("<b>ADMISSION NO:</b>", style_label), adm, Paragraph("<b>GENDER:</b>", style_label), s_extra[2] or "-"],
            [Paragraph("<b>EXAM NO:</b>", style_label), s_extra[0] or "-", Paragraph("<b>FULL NAME:</b>", style_label), s_extra[1] or "-"],
            [Paragraph("<b>STREAM:</b>", style_label), s_extra[3] or "-", "", ""]
        ]
        dt = Table(details_data, colWidths=[1.5*inch, 2*inch, 1.5*inch, 2*inch])
        dt.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
        elements.append(dt)
        elements.append(Spacer(1, 0.2 * inch))

        # --- SECTION 2: ACADEMIC RESULTS ---
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
        
        res_header = ["SUBJECT", "MARKS", "GRADE", "POINTS"]
        res_data = [res_header]
        
        for fn, sn, m_val in marks_rows:
            subject_label = get_subject_short_name(fn, sn)
            g = get_grade(m_val, level=level)
            p = get_points(g, level=level)
            res_data.append([subject_label, str(m_val), g, str(p)])
            
        rt = Table(res_data, colWidths=[3.2*inch, 0.8*inch, 0.8*inch, 0.8*inch])
        rt.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'), # Align subject names to left
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(rt)
        elements.append(Spacer(1, 0.2 * inch))

        # --- SECTION 3: ACADEMIC SUMMARY ---
        summary_data = [
            ["POSITION", "DIVISION", "POINTS", "AVERAGE", "STATUS"],
            [str(student['position']), str(student['division']), str(student['points']), str(student['average']), student['status']]
        ]
        st = Table(summary_data, colWidths=[1.2*inch, 1.2*inch, 1.2*inch, 1.2*inch, 1.2*inch])
        st.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.whitesmoke),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ]))
        elements.append(Paragraph("<b>ACADEMIC SUMMARY</b>", styles['Normal']))
        elements.append(st)
        elements.append(Spacer(1, 0.2 * inch))

        # --- SECTION 4: SCHOOL REQUIREMENTS ---
        if use_req:
            elements.append(Paragraph("<b>SCHOOL REQUIREMENTS</b>", styles['Normal']))
            date_data = [[
                Paragraph(f"<b>OPENING DATE</b><br/>{opening_date or '-'}", style_value),
                Paragraph(f"<b>CLOSING DATE</b><br/>{closing_date or '-'}", style_value),
            ]]
            date_tbl = Table(date_data, colWidths=[3*inch, 3*inch])
            date_tbl.setStyle(TableStyle([
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BACKGROUND', (0, 0), (-1, -1), colors.whitesmoke),
            ]))
            elements.append(date_tbl)
            elements.append(Spacer(1, 0.12 * inch))
            req_data = [["ITEM", "QUANTITY"]]
            if requirements_data:
                for item, qty in requirements_data:
                    req_data.append([item, qty])
            else:
                req_data.append(["-", "-"])
            
            req_t = Table(req_data, colWidths=[4*inch, 1.6*inch])
            req_t.setStyle(TableStyle([
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
            ]))
            elements.append(req_t)
            elements.append(Spacer(1, 0.2 * inch))

        # --- SECTION 5: COMMENTS ---
        elements.append(Paragraph("<b>TEACHER COMMENTS</b>", styles['Normal']))
        comm_data = [
            [Paragraph("<b>CLASS TEACHER</b>", style_value), Paragraph(".........................................................................................................................................................", style_value)],
            [Paragraph("<b>ACADEMIC MASTER</b>", style_value), Paragraph(".........................................................................................................................................................", style_value)],
            [Paragraph("<b>HEAD TEACHER</b>", style_value), Paragraph(".........................................................................................................................................................", style_value)],
        ]
        ct = Table(comm_data, colWidths=[1.4*inch, 4.6*inch])
        ct.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ]))
        elements.append(ct)
        elements.append(Spacer(1, 0.2 * inch))

        # --- SECTION 6: SIGNATURES ---
        sig_blocks = [
            [
                Paragraph("<b>CLASS MASTER / MISTRESS</b>", style_center),
                _safe_image(class_master_signature, 0.75 * inch, 0.32 * inch) or Paragraph("Signature: ______________", style_value),
                Paragraph(f"Name: {class_master}" if class_master else "Name: ______________", style_value),
                Paragraph("Date: ______________", style_value),
            ],
            [
                Paragraph("<b>ACADEMIC MASTER / MISTRESS</b>", style_center),
                _safe_image(academic_master_signature, 0.75 * inch, 0.32 * inch) or Paragraph("Signature: ______________", style_value),
                Paragraph(f"Name: {academic_master}" if academic_master else "Name: ______________", style_value),
                Paragraph("Date: ______________", style_value),
            ],
            [
                Paragraph("<b>DISCIPLINE MASTER / MISTRESS</b>", style_center),
                _safe_image(discipline_master_signature, 0.75 * inch, 0.32 * inch) or Paragraph("Signature: ______________", style_value),
                Paragraph(f"Name: {discipline_master}" if discipline_master else "Name: ______________", style_value),
                Paragraph("Date: ______________", style_value),
            ],
            [
                Paragraph("<b>HEAD TEACHER / HEAD MISTRESS</b>", style_center),
                _safe_image(head_teacher_signature, 0.75 * inch, 0.32 * inch) or Paragraph("Signature: ______________", style_value),
                Paragraph(f"Name: {head_teacher}" if head_teacher else "Name: ______________", style_value),
                Paragraph("Date: ______________", style_value),
            ],
        ]
        sig_rows = [
            [Table([[sig_blocks[0][0]], [sig_blocks[0][1]], [sig_blocks[0][2]], [sig_blocks[0][3]]], colWidths=[3.0*inch]),
             Table([[sig_blocks[1][0]], [sig_blocks[1][1]], [sig_blocks[1][2]], [sig_blocks[1][3]]], colWidths=[3.0*inch])],
            [Table([[sig_blocks[2][0]], [sig_blocks[2][1]], [sig_blocks[2][2]], [sig_blocks[2][3]]], colWidths=[3.0*inch]),
             Table([[sig_blocks[3][0]], [sig_blocks[3][1]], [sig_blocks[3][2]], [sig_blocks[3][3]]], colWidths=[3.0*inch])],
        ]
        sigt = Table(sig_rows, colWidths=[3.0*inch, 3.0*inch])
        sigt.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(sigt)

        # START NEW PAGE FOR NEXT STUDENT
        elements.append(PageBreak())
        report_progress(10 + int((index / total_students) * 80), f"Building student {index}/{total_students}")

    try:
        report_progress(95, "Rendering PDF")
        doc.build(elements, onFirstPage=on_page, onLaterPages=on_page)
        report_progress(100, "Report book generated")
        return True, "Report Book generated successfully."
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()
