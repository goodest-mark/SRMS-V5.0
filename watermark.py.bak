from reportlab.lib import colors

def draw_watermark(canvas, doc, school_name="SRMS V5", year="", watermark_text="CONFIDENTIAL"):
    """Renders a diagonal, semi-transparent watermark on the PDF page."""
    canvas.saveState()
    canvas.setFont('Helvetica-Bold', 60)
    canvas.setFillAlpha(0.1)  # Low opacity
    canvas.setStrokeColor(colors.grey)
    
    # Draw main watermark diagonally
    canvas.translate(300, 400)
    canvas.rotate(45)
    canvas.drawCentredString(0, 0, watermark_text)
    
    # Footer Version Mark
    canvas.setFont('Helvetica', 8)
    canvas.drawCentredString(0, -100, f"SRMS V5.0 | {school_name} {year}")
    canvas.restoreState()