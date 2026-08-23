from decimal import Decimal
from io import BytesIO
import datetime

from django.db import transaction
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, FrameBreak,
    Table, TableStyle, Paragraph, Spacer, PageBreak, Image,
)
from reportlab.lib.enums import TA_LEFT
from apps.academics.models import Examination, Class
from apps.students.models import Student
from apps.school.models import School
from .models import Result, ConductRating


# ==================== GRADING ====================

GRADE_SCALE = [
    (90, "A+", Decimal("4.0")),
    (80, "A", Decimal("3.6")),
    (70, "B+", Decimal("3.2")),
    (60, "B", Decimal("2.8")),
    (50, "C+", Decimal("2.4")),
    (40, "C", Decimal("2.0")),
    (0, "NG", Decimal("0.0")),
]


def _grade_for_percentage(percentage: Decimal) -> tuple[str, Decimal]:
    for threshold, letter, point in GRADE_SCALE:
        if percentage >= threshold:
            return letter, point
    return "NG", Decimal("0.0")


@transaction.atomic
def compute_final_result(student, academic_year: str):
    term_exams = Examination.objects.filter(
        academic_year=academic_year,
        term__in=[Examination.Term.FIRST, Examination.Term.SECOND, Examination.Term.THIRD, Examination.Term.FOURTH],
    )
    if term_exams.count() != 4:
        raise ValueError(f"Cannot compute Final: expected 4 term examinations for {academic_year}, found {term_exams.count()}.")

    final_exam, _ = Examination.objects.get_or_create(
        term=Examination.Term.FINAL, academic_year=academic_year, defaults={"is_final": True},
    )

    term_results = Result.objects.filter(student=student, examination__in=term_exams)
    subject_ids = term_results.values_list("subject_id", flat=True).distinct()

    computed = []
    for subject_id in subject_ids:
        subject_results = term_results.filter(subject_id=subject_id)
        if subject_results.count() != 4:
            continue

        percentages = [(r.marks_obtained / r.full_marks) * 100 for r in subject_results]
        avg_percentage = sum(percentages) / len(percentages)

        result, _ = Result.objects.update_or_create(
            student=student, examination=final_exam, subject_id=subject_id,
            defaults={"marks_obtained": round(avg_percentage, 2), "full_marks": Decimal("100")},
        )
        computed.append(result)

    return computed


def compute_gpa(student, academic_year: str) -> Decimal:
    final_results = Result.objects.filter(
        student=student, examination__academic_year=academic_year, examination__is_final=True,
    )
    if not final_results.exists():
        raise ValueError(f"No Final results found for {student} in {academic_year}. Run compute_final_result() first.")

    points = [r.grade_point for r in final_results]
    return round(sum(points) / len(points), 2)


# ==================== ADMIT CARDS ====================

CARD_WIDTH = 90 * mm
CARD_HEIGHT = 55 * mm
CARDS_PER_ROW = 2
MARGIN = 10 * mm
GAP = 5 * mm


def generate_admit_cards(examination, class_obj: Class) -> bytes:
    """
    Packs multiple admit cards per A4 page in a grid (2 per row),
    wrapping to a new row/page once full -- the print-friendly
    layout a school would use to cut cards apart after printing.
    """
    school = School.objects.first()
    students = Student.objects.filter(student_class=class_obj).select_related("user")

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    page_width, page_height = A4

    rows_per_page = int((page_height - 2 * MARGIN) // (CARD_HEIGHT + GAP))
    cards_per_page = CARDS_PER_ROW * rows_per_page

    for index, student in enumerate(students):
        position_on_page = index % cards_per_page
        if position_on_page == 0 and index != 0:
            c.showPage()

        col = position_on_page % CARDS_PER_ROW
        row = position_on_page // CARDS_PER_ROW
        x = MARGIN + col * (CARD_WIDTH + GAP)
        y = page_height - MARGIN - (row + 1) * (CARD_HEIGHT + GAP) + GAP

        _draw_single_admit_card(c, x, y, student, class_obj, examination, school)

    c.save()
    buffer.seek(0)
    return buffer.getvalue()


def _draw_single_admit_card(c, x, y, student, class_obj, examination, school):
    c.rect(x, y, CARD_WIDTH, CARD_HEIGHT)

    logo_size = 12 * mm
    if school and school.logo:
        try:
            c.drawImage(
                school.logo.path, x + 3 * mm, y + CARD_HEIGHT - logo_size - 3 * mm,
                width=logo_size, height=logo_size, preserveAspectRatio=True, mask="auto",
            )
        except Exception:
            pass

    text_start_x = x + logo_size + 6 * mm if (school and school.logo) else x + 4 * mm

    c.setFont("Helvetica-Bold", 10)
    c.drawString(text_start_x, y + CARD_HEIGHT - 8 * mm, school.school_name if school else "School Name")

    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(x + CARD_WIDTH / 2, y + CARD_HEIGHT - 15 * mm, "ADMIT CARD")

    if school and school.address:
        c.setFont("Helvetica", 7.5)
        c.drawCentredString(x + CARD_WIDTH / 2, y + CARD_HEIGHT - 21 * mm, school.address)

    photo_size = 18 * mm
    photo_x = x + CARD_WIDTH - photo_size - 3 * mm
    photo_y = y + (CARD_HEIGHT - photo_size) / 2

    if student.photo:
        try:
            c.drawImage(student.photo.path, photo_x, photo_y, width=photo_size, height=photo_size, preserveAspectRatio=True, mask="auto")
        except Exception:
            c.rect(photo_x, photo_y, photo_size, photo_size)
    else:
        c.rect(photo_x, photo_y, photo_size, photo_size)

    full_name = f"{student.user.first_name} {student.user.last_name}".strip()
    display_name = full_name if full_name else student.user.email

    c.setFont("Helvetica", 8)
    c.drawString(x + 4 * mm, y + CARD_HEIGHT - 27 * mm, f"Student: {display_name}")
    c.drawString(x + 4 * mm, y + CARD_HEIGHT - 33 * mm, f"Class: {class_obj}")
    c.drawString(x + 4 * mm, y + CARD_HEIGHT - 39 * mm, f"Examination: {examination}")

    sig_line_width = 35 * mm
    sig_x = x + CARD_WIDTH - sig_line_width - 4 * mm
    sig_y = y + 8 * mm

    c.line(sig_x, sig_y, sig_x + sig_line_width, sig_y)
    c.setFont("Helvetica", 6)
    c.drawCentredString(sig_x + sig_line_width / 2, sig_y - 3 * mm, "Principal's Signature")


# ==================== MARKSHEET ====================

def generate_marksheets(class_obj: Class, examination, academic_year: str) -> bytes:
    """
    One PDF, one marksheet per student, for ONE SPECIFIC examination.
    Uses a two-frame page template: content_frame (header through
    performance insight) flows normally; footer_frame is a FIXED
    zone at the bottom of every page, so signatures always land in
    the same physical position regardless of how much content is
    above them.
    """
    school = School.objects.first()
    students = Student.objects.filter(student_class=class_obj).select_related("user")

    buffer = BytesIO()
    page_width, page_height = A4
    margin = 15 * mm
    footer_height = 30 * mm

    content_frame = Frame(
        margin, margin + footer_height,
        page_width - 2 * margin, page_height - 2 * margin - footer_height,
        id="content",
    )
    footer_frame = Frame(
        margin, margin,
        page_width - 2 * margin, footer_height,
        id="footer",
    )

    doc = BaseDocTemplate(buffer, pagesize=A4)
    doc.addPageTemplates([
        PageTemplate(id="marksheet", frames=[content_frame, footer_frame], onPage=_draw_page_border)
    ])

    story = []
    for i, student in enumerate(students):
        story.extend(_build_marksheet_content(student, class_obj, examination, academic_year, school))
        story.append(FrameBreak())
        story.extend(_build_signature_block())
        if i < len(students) - 1:
            story.append(PageBreak())

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


def _draw_page_border(canvas_obj, doc):
    canvas_obj.saveState()
    canvas_obj.setStrokeColor(colors.HexColor("#3B78A8"))
    canvas_obj.setLineWidth(0.9)
    border_margin = 8 * mm
    canvas_obj.rect(border_margin, border_margin, A4[0] - 2 * border_margin, A4[1] - 2 * border_margin, fill=0, stroke=1)
    canvas_obj.restoreState()


def _get_marksheet_rows(student, examination):
    results = Result.objects.filter(student=student, examination=examination).select_related("subject").order_by("subject__subject_name")

    rows = []
    overall_passed = True
    total_credit = Decimal("0")
    weighted_gp_sum = Decimal("0")

    for index, r in enumerate(results, start=1):
        practical_display = r.practical_grade if r.has_practical else "-"
        remarks = "Pass" if r.passed else "Fail"
        if not r.passed:
            overall_passed = False

        credit = r.subject.credit_hour
        total_credit += credit
        weighted_gp_sum += credit * r.grade_point

        rows.append([str(index), r.subject.subject_name.title(), str(credit), r.grade, practical_display, str(r.grade_point), remarks])

    return rows, overall_passed, total_credit, weighted_gp_sum


def _build_marksheet_content(student, class_obj, examination, academic_year, school):
    """
    Everything EXCEPT the signature block: header, student info,
    results table, GPA banner, legend+summary, performance insight,
    verification note. Rendered into content_frame; the footer
    (signatures) is built separately by _build_signature_block()
    and rendered into the fixed footer_frame.
    """
    styles = getSampleStyleSheet()
    center_style = ParagraphStyle("center", parent=styles["Normal"], alignment=TA_CENTER)
    CONTENT_WIDTH = 180 * mm  # A4 (210mm) minus 15mm left + 15mm right margins

    flowables = []

    # ---- Header ----
    school_name = school.school_name if school else "School Name"
    school_address = school.address if (school and school.address) else ""
    school_contact = school.contact_email if (school and school.contact_email) else ""
    school_quote = school.school_quote if (school and school.school_quote) else ""
    school_contact_number = school.school_contact_number if (school and school.school_contact_number) else ""
    
    header_text = f"<b><font size=14>{school_name}</font></b><br/><b><font size=8.5>Address: {school_address}</font></b><br/><b><font size=8.5>Email: {school_contact}</font></b><br/><b><font size=8.5>ContactNo: {school_contact_number}</font></b><br/><b><font size=8.5><i>{school_quote}</i></font></b>"
    exam_name = Examination.Term(examination.term).label
    
    
    header_text += f"<br/><br/><b><font size=12> {exam_name} Marksheet </font></b>"
    logo_cell = ""
    if school and school.logo:
        try:
            logo_cell = Image(school.logo.path, width=17 * mm, height=17 * mm)
        except Exception:
            pass

    photo_cell = ""
    if student.photo:
        try:
            photo_cell = Image(student.photo.path, width=18 * mm, height=18 * mm)
        except Exception:
            pass

    header_table = Table([[logo_cell, Paragraph(header_text, center_style), photo_cell]], colWidths=[20 * mm, 138 * mm, 22 * mm])
    header_table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("ALIGN", (0, 0), (0, 0), "LEFT"), ("ALIGN", (2, 0), (2, 0), "RIGHT")]))
    flowables.append(header_table)
    flowables.append(Spacer(1, 7 * mm))

    # ---- Student info ----
    full_name = f"{student.user.first_name} {student.user.last_name}".strip() or student.user.email
    date_of_birth = student.date_of_birth.strftime("%d-%m-%Y") if student.date_of_birth else "N/A"
    parent_name = student.parent_name if student.parent_name else "N/A"
    parent_contact = student.parent_contact if student.parent_contact else "N/A"
    
    info_label_style = ParagraphStyle("InfoLabel", fontName="Helvetica-Bold", fontSize=8.5, leading=10, alignment=TA_LEFT)
    info_value_style = ParagraphStyle("InfoValue", fontName="Helvetica", fontSize=8.5, leading=10, alignment=TA_LEFT)

    info_data = [
    [Paragraph("Name:", info_label_style), Paragraph(full_name, info_value_style), Paragraph("Roll No.:", info_label_style), Paragraph(str(student.roll_number or "N/A"), info_value_style), Paragraph("Date of Birth:", info_label_style), Paragraph(date_of_birth, info_value_style)],
    [Paragraph("Class:", info_label_style), Paragraph(str(class_obj), info_value_style), Paragraph("Academic Year:", info_label_style), Paragraph(academic_year, info_value_style), Paragraph("Gender:", info_label_style), Paragraph(str(student.gender or "N/A"), info_value_style)],
    [Paragraph("Parent Name:", info_label_style), Paragraph(str(parent_name), info_value_style), Paragraph("Parent Contact:", info_label_style), Paragraph(str(parent_contact), info_value_style), "", ""],
]

    info_table = Table(info_data, colWidths=[21 * mm, 37 * mm, 26 * mm, 37 * mm, 29 * mm, 26 * mm], hAlign="LEFT")
    info_table.setStyle(TableStyle([
    ("BOX", (0, 0), (-1, -1), 0.6, colors.grey),
    ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.lightgrey),
    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F2F2F2")),
    ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#F2F2F2")),
    ("BACKGROUND", (4, 0), (4, -1), colors.HexColor("#F2F2F2")),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ("LEFTPADDING", (0, 0), (-1, -1), 4),
    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ("TOPPADDING", (0, 0), (-1, -1), 3),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    flowables.append(info_table)
    flowables.append(Spacer(1, 5 * mm))

    # ---- Results table ----
    rows, overall_passed, total_credit, weighted_gp_sum = _get_marksheet_rows(student, examination)
    header_row = ["SN", "Subjects", "Credit\nHour", "TH", "PR", "Grade Point", "Remarks"]
    table_data = [header_row] + rows

    results_table = Table(table_data, colWidths=[10 * mm, 65 * mm, 18 * mm, 15 * mm, 15 * mm, 27 * mm, 30 * mm], repeatRows=1)
    results_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2C6FA6")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("ALIGN", (1, 1), (1, -1), "LEFT"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#A8A8A8")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
    ]))
    flowables.append(results_table)
    flowables.append(Spacer(1, 4 * mm))

    # ---- GPA banner ----
    overall_gpa = round(weighted_gp_sum / total_credit, 2) if total_credit else "N/A"
    gpa_table = Table([[f"Grade Point Average: {overall_gpa}"]], colWidths=[CONTENT_WIDTH])
    gpa_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#9E9E9E")),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    flowables.append(gpa_table)
    flowables.append(Spacer(1, 6 * mm))

    # ---- Legend + Overall Summary, side by side ----
    legend_data = [
        ["Mark Range", "GPA", "Grade"],
        ["90 - 100", "4.0", "A+"], ["80 - 89", "3.6", "A"], ["70 - 79", "3.2", "B+"],
        ["60 - 69", "2.8", "B"], ["50 - 59", "2.4", "C+"], ["40 - 49", "2.0", "C"], ["Below 40", "0.0", "NG"],
    ]
    legend_table = Table(legend_data, colWidths=[36 * mm, 27 * mm, 27 * mm])
    legend_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EAF4FA")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#A8A8A8")),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))

    conduct = ConductRating.objects.filter(student=student, examination=examination).first()
    hygiene = conduct.hygiene if conduct else "N/A"
    discipline = conduct.discipline if conduct else "N/A"
    attendance = f"{conduct.attendance_percentage}%" if (conduct and conduct.attendance_percentage is not None) else "N/A"

    summary_data = [["Overall Summary", ""], ["GPA", str(overall_gpa)], ["Hygiene", hygiene], ["Discipline", discipline], ["Attendance", attendance]]
    summary_table = Table(summary_data, colWidths=[50 * mm, 40 * mm])
    summary_table.setStyle(TableStyle([
        ("SPAN", (0, 0), (1, 0)),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EAF4FA")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7.5),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#A8A8A8")),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
    ]))

    side_by_side = Table([[legend_table, summary_table]], colWidths=[90 * mm, 90 * mm])
    side_by_side.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    flowables.append(side_by_side)

   
   

    return flowables


def _build_signature_block():
    """Rendered into the fixed footer_frame -- always at the same page position, regardless of content length above."""
    issue_date = datetime.date.today().strftime("%d-%m-%Y")
    sig_data = [["_______________________", issue_date, "_______________________"], ["Class Teacher", "Date", "Principal"]]
    sig_table = Table(sig_data, colWidths=[77.5 * mm, 25 * mm, 77.5 * mm])
    sig_table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    return [Spacer(1, 12 * mm), sig_table]