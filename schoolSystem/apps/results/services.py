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
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image

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

    # ---- School logo, top-left ----
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

    # ---- School address: pulled from the School model, not hardcoded ----
    if school and school.address:
        c.setFont("Helvetica", 7.5)
        c.drawCentredString(x + CARD_WIDTH / 2, y + CARD_HEIGHT - 21 * mm, school.address)

    # ---- Student photo, vertically centered on the right edge ----
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

    # ---- Student details, left side ----
    full_name = f"{student.user.first_name} {student.user.last_name}".strip()
    display_name = full_name if full_name else student.user.email

    c.setFont("Helvetica", 8)
    c.drawString(x + 4 * mm, y + CARD_HEIGHT - 27 * mm, f"Student: {display_name}")
    c.drawString(x + 4 * mm, y + CARD_HEIGHT - 33 * mm, f"Class: {class_obj}")
    c.drawString(x + 4 * mm, y + CARD_HEIGHT - 39 * mm, f"Examination: {examination}")

    # ---- Principal's signature line, bottom-right ----
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
    """
    school = School.objects.first()
    students = Student.objects.filter(student_class=class_obj).select_related("user")

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=12 * mm, bottomMargin=12 * mm, leftMargin=15 * mm, rightMargin=15 * mm)

    story = []
    for i, student in enumerate(students):
        story.extend(_build_marksheet_flowables(student, class_obj, examination, academic_year, school))
        if i < len(students) - 1:
            story.append(PageBreak())

    doc.build(story, onFirstPage=_draw_page_border, onLaterPages=_draw_page_border)
    buffer.seek(0)
    return buffer.getvalue()


def _draw_page_border(canvas_obj, doc):
    """
    Draws a border around the full page, once per page. This is the
    only definition -- a duplicate of this function existed in the
    ChatGPT version and was silently overriding the first; removed.
    """
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


def _build_marksheet_flowables(student, class_obj, examination, academic_year, school):
    styles = getSampleStyleSheet()
    center_style = ParagraphStyle("center", parent=styles["Normal"], alignment=TA_CENTER)

    CONTENT_WIDTH = 180 * mm  # matches A4 (210mm) minus 15mm left + 15mm right margins

    flowables = []

    # ---- Header ----
    school_name = school.school_name if school else "School Name"
    school_address = school.address if (school and school.address) else ""
    school_contact = school.contact_email if (school and school.contact_email) else ""
    header_text = f"<b><font size=14>{school_name}</font></b><br/><font size=8.5>{school_address}</font><br/><font size=8.5>{school_contact}</font>"

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
    info_data = [
        ["Name:", full_name, "Roll No.:", student.roll_number or "N/A"],
        ["Class:", str(class_obj), "Academic Year:", academic_year],
    ]
    info_table = Table(info_data, colWidths=[22 * mm, 65 * mm, 28 * mm, 65 * mm])
    info_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
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

    # ---- Legend + Overall Summary, side by side, each exactly half of CONTENT_WIDTH ----
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
    flowables.append(Spacer(1, 6 * mm))

    # ---- Teacher's Remarks ----
    remarks_table = Table([["Teacher's Remarks:"], [""]], colWidths=[CONTENT_WIDTH], rowHeights=[6 * mm, 16 * mm])
    remarks_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#A8A8A8")),
        ("VALIGN", (0, 0), (0, 0), "TOP"),
        ("TOPPADDING", (0, 0), (0, 0), 4), ("LEFTPADDING", (0, 0), (0, 0), 4),
    ]))
    flowables.append(remarks_table)
    flowables.append(Spacer(1, 8 * mm))

    # ---- Signatures ----
    issue_date = datetime.date.today().strftime("%d-%m-%Y")
    sig_data = [["_______________________", issue_date, "_______________________"], ["Class Teacher", "Date", "Principal"]]
    sig_table = Table(sig_data, colWidths=[77.5 * mm, 25 * mm, 77.5 * mm])
    sig_table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    flowables.append(sig_table)

    return flowables