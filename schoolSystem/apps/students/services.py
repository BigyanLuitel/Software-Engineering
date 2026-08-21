from io import BytesIO
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white
from reportlab.pdfgen import canvas
from apps.academics.models import Class
from apps.students.models import Student
from apps.school.models import School
from reportlab.pdfbase.pdfmetrics import stringWidth


ID_CARD_WIDTH = 62 * mm
ID_CARD_HEIGHT = 85.6 * mm  # portrait orientation, standard ID card proportions rotated

SKY_BLUE = HexColor("#4FA8E0")
DEEP_BLUE = HexColor("#2C6FA6")   # darker accent band
ACCENT_CIRCLE = HexColor("#7FC1EA")  # subtle decorative circle, slightly lighter than main bg

CARDS_PER_ROW = 3
MARGIN = 10 * mm
GAP = 6 * mm


def generate_id_cards(class_obj: Class, academic_year: str) -> bytes:
    """
    Generates one PDF with a sky-blue ID card per student in
    class_obj, arranged in a grid (3 per row on A4), same grid-page
    approach as generate_admit_cards -- reusing that proven pattern
    rather than inventing a new layout algorithm.
    """
    from reportlab.lib.pagesizes import A4

    school = School.objects.first()
    students = Student.objects.filter(student_class=class_obj).select_related("user")

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    page_width, page_height = A4

    rows_per_page = int((page_height - 2 * MARGIN) // (ID_CARD_HEIGHT + GAP))
    cards_per_page = CARDS_PER_ROW * rows_per_page

    for index, student in enumerate(students):
        position_on_page = index % cards_per_page
        if position_on_page == 0 and index != 0:
            c.showPage()

        col = position_on_page % CARDS_PER_ROW
        row = position_on_page // CARDS_PER_ROW

        x = MARGIN + col * (ID_CARD_WIDTH + GAP)
        y = page_height - MARGIN - (row + 1) * (ID_CARD_HEIGHT + GAP) + GAP

        _draw_single_id_card(c, x, y, student, class_obj, academic_year, school)

    c.save()
    buffer.seek(0)
    return buffer.getvalue()


def _wrap_text(text, font_name, font_size, max_width):
    """
    Splits text into lines that each fit within max_width, breaking
    on word boundaries. Needed because a school's full name/address
    can't just be truncated -- it must remain fully readable, so it
    wraps onto as many lines as it needs instead.
    """
    words = text.split()
    lines = []
    current = ""
    for word in words:
        trial = f"{current} {word}".strip()
        if stringWidth(trial, font_name, font_size) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines
def _draw_curved_band(c, x, y, width, height, curve_depth, color, curve_at="bottom"):
    """
    Draws a rectangle where one edge (top or bottom) is a smooth
    curve instead of a straight line -- used for the header (curves
    at its bottom, dipping into the body) and footer (curves at its
    top, rising into the body). curve_depth controls how pronounced
    the curve is; a Bezier curve is used since ReportLab has no
    built-in "half-curved rectangle" primitive.
    """
    c.setFillColor(color)
    p = c.beginPath()

    if curve_at == "bottom":
        # Header band: flat top/sides, curved bottom edge dipping downward in the middle
        p.moveTo(x, y + height)
        p.lineTo(x + width, y + height)
        p.lineTo(x + width, y + curve_depth)
        p.curveTo(
            x + width, y - curve_depth * 0.5,
            x, y - curve_depth * 0.5,
            x, y + curve_depth,
        )
        p.close()
    else:
        # Footer band: flat bottom/sides, curved top edge rising upward in the middle
        p.moveTo(x, y)
        p.lineTo(x + width, y)
        p.lineTo(x + width, y + height - curve_depth)
        p.curveTo(
            x + width, y + height + curve_depth * 0.5,
            x, y + height + curve_depth * 0.5,
            x, y + height - curve_depth,
        )
        p.close()

    c.drawPath(p, fill=1, stroke=0)

def _draw_single_id_card(c, x, y, student, class_obj, academic_year, school):
    # ---- Background ----
    c.setFillColor(SKY_BLUE)
    c.roundRect(x, y, ID_CARD_WIDTH, ID_CARD_HEIGHT, 3 * mm, fill=1, stroke=0)

    c.setFillColor(ACCENT_CIRCLE)
    c.circle(x + ID_CARD_WIDTH - 4 * mm, y + ID_CARD_HEIGHT - 4 * mm, 14 * mm, fill=1, stroke=0)

    # ---- Header band: curved bottom edge ----
    logo_size = 14 * mm
    logo_x = x + 3 * mm
    text_x = logo_x + logo_size + 3 * mm
    usable_width = ID_CARD_WIDTH - (text_x - x) - 3 * mm

    name_lines = _wrap_text(school.school_name if school else "School Name", "Helvetica-Bold", 8, usable_width)
    address_lines = _wrap_text(school.address, "Helvetica", 6, usable_width) if (school and school.address) else []

    header_height = 6 * mm + len(name_lines) * 3.2 * mm + len(address_lines) * 2.6 * mm + (3.5 * mm if school and school.established_year else 0)
    header_height = max(header_height, logo_size + 6 * mm)

    header_bottom_y = y + ID_CARD_HEIGHT - header_height
    _draw_curved_band(c, x, header_bottom_y, ID_CARD_WIDTH, header_height, curve_depth=4 * mm, color=DEEP_BLUE, curve_at="bottom")

    # ---- Logo, left-aligned, vertically centered within the header band ----
    if school and school.logo:
        try:
            c.drawImage(
                school.logo.path,
                logo_x, y + ID_CARD_HEIGHT - header_height + (header_height - logo_size) / 2,
                width=logo_size, height=logo_size,
                preserveAspectRatio=True, mask="auto",
            )
        except Exception:
            pass

    # ---- School name / address / established year ----
    text_top = y + ID_CARD_HEIGHT - 5 * mm

    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 8)
    for line in name_lines:
        c.drawString(text_x, text_top, line)
        text_top -= 3.2 * mm

    c.setFont("Helvetica", 6)
    for line in address_lines:
        c.drawString(text_x, text_top, line)
        text_top -= 2.6 * mm

    if school and school.established_year:
        c.setFont("Helvetica", 5.5)
        c.drawString(text_x, text_top, f"Estd. {school.established_year}")

    # ---- Student photo ----
    photo_size = 22 * mm
    photo_x = x + (ID_CARD_WIDTH - photo_size) / 2
    photo_y = header_bottom_y - photo_size - 9 * mm  # extra clearance since the curve dips below header_bottom_y

    c.setFillColor(white)
    c.roundRect(photo_x - 1.2 * mm, photo_y - 1.2 * mm, photo_size + 2.4 * mm, photo_size + 2.4 * mm, 2 * mm, fill=1, stroke=0)

    if student.photo:
        try:
            c.drawImage(student.photo.path, photo_x, photo_y, width=photo_size, height=photo_size, preserveAspectRatio=True, mask="auto")
        except Exception:
            c.setFillColor(SKY_BLUE)
            c.rect(photo_x, photo_y, photo_size, photo_size, fill=1, stroke=0)
    else:
        c.setFillColor(SKY_BLUE)
        c.rect(photo_x, photo_y, photo_size, photo_size, fill=1, stroke=0)

    # ---- Labeled detail rows ----
    full_name = f"{student.user.first_name} {student.user.last_name}".strip()
    display_name = full_name if full_name else "N/A"

    rows = [
        ("Name:", display_name[:22]),
        ("Class:", str(class_obj)),
        ("Roll No:", student.roll_number or "N/A"),
        ("Email:", student.user.email[:24]),
        ("Contact:", student.parent_contact or "N/A"),
    ]

    label_x = x + 4 * mm
    value_x = x + 20 * mm
    row_y = photo_y - 6 * mm
    row_gap = 4.6 * mm

    for label, value in rows:
        c.setFillColor(white)
        c.setFont("Helvetica-Bold", 6)
        c.drawString(label_x, row_y, label)
        c.setFont("Helvetica", 6)
        c.drawString(value_x, row_y, value)
        row_y -= row_gap

    # ---- Footer band: curved top edge ----
    footer_height = 10 * mm
    _draw_curved_band(c, x, y, ID_CARD_WIDTH, footer_height, curve_depth=3 * mm, color=DEEP_BLUE, curve_at="top")

    c.setFillColor(white)
    c.setFont("Helvetica", 6)
    c.drawCentredString(x + ID_CARD_WIDTH / 2, y + 3 * mm, f"Valid: {academic_year}")

    # ---- Outer border ----
    c.setStrokeColor(DEEP_BLUE)
    c.setLineWidth(0.75)
    c.roundRect(x, y, ID_CARD_WIDTH, ID_CARD_HEIGHT, 3 * mm, fill=0, stroke=1)