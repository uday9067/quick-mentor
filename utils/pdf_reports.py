from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime


def pending_fees_pdf(data, file_path):
    doc = SimpleDocTemplate(file_path, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    title = Paragraph(
        f"<b>Students with Pending Fees</b><br/><font size=9>Generated on: {datetime.now().strftime('%d-%m-%Y')}</font>",
        styles["Title"]
    )
    elements.append(title)

    table_data = [
        ["Roll", "Name", "Semester", "Pending Amount"]
    ]

    for r in data:
        table_data.append([
            r.roll,
            r.name,
            f"Sem {r.semester}",
            f"₹{r.pending_amount}",
        
        ])

    table = Table(table_data, colWidths=[70, 120, 80, 100, 80])

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4aa2b1")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),

        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ALIGN", (2, 1), (-1, -1), "CENTER"),
        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold"),

        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("TOPPADDING", (0, 0), (-1, 0), 8),
    ]))

    elements.append(table)
    doc.build(elements)


def low_attendance_pdf(data, file_path):
    doc = SimpleDocTemplate(file_path, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    title = Paragraph(
        f"<b>Students with Low Attendance</b><br/><font size=9>Generated on: {datetime.now().strftime('%d-%m-%Y')}</font>",
        styles["Title"]
    )
    elements.append(title)

    table_data = [
        ["Roll", "Name", "Department", "Year", "Attendance (%)"]
    ]

    for s in data:
        table_data.append([
            s.roll,
            s.name,
            s.department,
            s.year,
            f"{s.attendance}%"
        ])

    table = Table(table_data, colWidths=[70, 120, 100, 60, 90])

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4aa2b1")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),

        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ALIGN", (3, 1), (-1, -1), "CENTER"),
        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold"),

        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("TOPPADDING", (0, 0), (-1, 0), 8),
    ]))

    elements.append(table)
    doc.build(elements)
