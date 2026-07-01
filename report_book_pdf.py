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
    cur.execute("SELECT school_name, school_address, school_phone, school_email, watermark_text FROM school_profile LIMIT 1")
    profile = cur.fetchone()
    school_name = profile[0] if profile else "SCHOOL MANAGEMENT SYSTEM"
    school_addr = profile[1] if profile else "-"
    watermark_text = profile[4] if profile and profile[4] else "CONFIDENTIAL"
    
    # 2. Get Academic Context
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
        cur.execute("SELECT full_name, gender, stream FROM students WHERE admission_no=?", (adm,))
        s_extra = cur.fetchone()
        if not s_extra:
            print(f"[WARNING] Student record not found for admission_no='{adm}', skipping.")
            elements.append(PageBreak())
            continue
        
        details_data = [
            [Paragraph("<b>ADMISSION NO:</b>", style_label), adm, Paragraph("<b>GENDER:</b>", style_label), s_extra[1] or "-"],
            [Paragraph("<b>FULL NAME:</b>", style_label), s_extra[0] or "-", Paragraph("<b>STREAM:</b>", style_label), s_extra[2] or "-"]
        ]
        dt = Table(details_data, colWidths=[1.5*inch, 2*inch, 1.5*inch, 2*inch])
        dt.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
        elements.append(dt)
        elements.append(Spacer(1, 0.2 * inch))

        # --- SECTION 2: ACADEMIC RESULTS ---
        cur.execute("""
            SELECT subject_name, marks FROM results WHERE admission_no=? AND exam_id=?
        """, (adm, exam_id))
        marks_rows = cur.fetchall()
        
        res_header = ["SUBJECT", "MARKS", "GRADE", "POINTS"]
        res_data = [res_header]
        
        for m_name, m_val in marks_rows:
            g = get_grade(m_val, level=level)
            p = get_points(g, level=level)
            res_data.append([m_name, str(m_val), g, str(p)])
            
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
            [Paragraph("Class Teacher: .........................................................................................................................................................", style_value)],
            [Paragraph("Academic Master: .........................................................................................................................................................", style_value)],
            [Paragraph("Head Teacher: .........................................................................................................................................................", style_value)],
        ]
        ct = Table(comm_data, colWidths=[6*inch])
        ct.setStyle(TableStyle([('BOTTOMPADDING', (0,0), (-1,-1), 15)]))
        elements.append(ct)

        # --- SECTION 6: DATES ---
        dates_data = [
            [f"Closing Date: .................................", f"Opening Date: ................................."]
        ]
        dtbl = Table(dates_data, colWidths=[3*inch, 3*inch])
        elements.append(dtbl)
        elements.append(Spacer(1, 0.2 * inch))

        # --- SECTION 7: SIGNATURES ---
        sig_data = [
            ["Class Teacher", "Academic Master", "Head Teacher", "Parent/Guardian"],
            [".........................", ".........................", ".........................", "........................."]
        ]
        sigt = Table(sig_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
        sigt.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (1, 0), (1, -1), 20),
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
