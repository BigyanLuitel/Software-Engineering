from io import BytesIO

from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white
from reportlab.pdfgen import canvas
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.lib.pagesizes import A4

from apps.academics.models import Class
from apps.students.models import Student
from apps.school.models import School


# ============================================================
# ID CARD CONFIGURATION
# ============================================================

ID_CARD_WIDTH = 62 * mm
ID_CARD_HEIGHT = 85.6 * mm

SKY_BLUE = HexColor("#4FA8E0")
DEEP_BLUE = HexColor("#2C6FA6")

# Decorative colors
LIGHT_BLUE = HexColor("#68B5E5")
LIGHTER_BLUE = HexColor("#61B0E2")

CARDS_PER_ROW = 3

MARGIN = 10 * mm
GAP = 6 * mm


# ============================================================
# MAIN PDF GENERATOR
# ============================================================

def generate_id_cards(class_obj: Class, academic_year: str) -> bytes:
    """
    Generates a PDF containing student ID cards for a class.

    Cards are arranged in a 3-column grid on A4 paper.
    """

    school = School.objects.first()

    students = (
        Student.objects
        .filter(student_class=class_obj)
        .select_related("user")
    )

    buffer = BytesIO()

    c = canvas.Canvas(
        buffer,
        pagesize=A4
    )

    page_width, page_height = A4

    # Number of rows that fit on an A4 page
    rows_per_page = int(
        (page_height - 2 * MARGIN)
        // (ID_CARD_HEIGHT + GAP)
    )

    cards_per_page = (
        CARDS_PER_ROW * rows_per_page
    )

    for index, student in enumerate(students):

        position_on_page = (
            index % cards_per_page
        )

        # Start a new page
        if position_on_page == 0 and index != 0:
            c.showPage()

        col = (
            position_on_page
            % CARDS_PER_ROW
        )

        row = (
            position_on_page
            // CARDS_PER_ROW
        )

        # Horizontal position
        x = (
            MARGIN
            + col * (ID_CARD_WIDTH + GAP)
        )

        # Vertical position
        y = (
            page_height
            - MARGIN
            - (row + 1) * ID_CARD_HEIGHT
            - row * GAP
        )

        _draw_single_id_card(
            c,
            x,
            y,
            student,
            class_obj,
            academic_year,
            school
        )

    c.save()

    buffer.seek(0)

    return buffer.getvalue()


# ============================================================
# TEXT WRAPPING
# ============================================================

def _wrap_text(
    text,
    font_name,
    font_size,
    max_width
):
    """
    Wraps text into multiple lines so that it fits
    inside the specified width.
    """

    words = str(text).split()

    lines = []

    current = ""

    for word in words:

        trial = (
            f"{current} {word}"
        ).strip()

        if (
            stringWidth(
                trial,
                font_name,
                font_size
            )
            <= max_width
        ):
            current = trial

        else:

            if current:
                lines.append(current)

            current = word

    if current:
        lines.append(current)

    return lines


# ============================================================
# CURVED HEADER / FOOTER
# ============================================================

def _draw_wave_band(
    c,
    x,
    y,
    width,
    height,
    curve_depth,
    color,
    curve_at="bottom"
):
    """
    Draws a smooth curved band.

    curve_at="bottom":
        Header with a curved bottom edge.

    curve_at="top":
        Footer with a curved top edge.

    The curve begins exactly at the left edge and
    finishes exactly at the right edge.
    """

    c.setFillColor(color)

    p = c.beginPath()

    if curve_at == "bottom":

        # Top-left
        p.moveTo(
            x,
            y + height
        )

        # Top-right
        p.lineTo(
            x + width,
            y + height
        )

        # Right side
        p.lineTo(
            x + width,
            y
        )

        # Curved bottom edge
        p.curveTo(
            x + width * 0.75,
            y + curve_depth,

            x + width * 0.25,
            y + curve_depth,

            x,
            y
        )

        p.close()

    else:

        # Bottom-left
        p.moveTo(
            x,
            y
        )

        # Bottom-right
        p.lineTo(
            x + width,
            y
        )

        # Right side
        p.lineTo(
            x + width,
            y + height - curve_depth
        )

        # Curved top edge
        p.curveTo(
            x + width * 0.75,
            y + height + curve_depth * 0.35,

            x + width * 0.25,
            y + height + curve_depth * 0.35,

            x,
            y + height - curve_depth
        )

        p.close()

    c.drawPath(
        p,
        fill=1,
        stroke=0
    )


# ============================================================
# SINGLE ID CARD
# ============================================================

def _draw_single_id_card(
    c,
    x,
    y,
    student,
    class_obj,
    academic_year,
    school
):

    card_w = ID_CARD_WIDTH
    card_h = ID_CARD_HEIGHT

    radius = 3 * mm

    # ========================================================
    # CARD BACKGROUND
    # ========================================================

    c.setFillColor(SKY_BLUE)

    c.roundRect(
        x,
        y,
        card_w,
        card_h,
        radius,
        fill=1,
        stroke=0
    )

    # ========================================================
    # DECORATIVE CIRCLES
    #
    # IMPORTANT:
    # The clipping path keeps the circles INSIDE
    # the rounded card.
    # ========================================================

    clip = c.beginPath()

    clip.roundRect(
        x,
        y,
        card_w,
        card_h,
        radius
    )

    c.saveState()

    c.clipPath(
        clip,
        stroke=0,
        fill=0
    )

    # --------------------------------------------------------
    # Top-right decorative circle
    # --------------------------------------------------------

    c.setFillColor(
        LIGHT_BLUE
    )

    c.circle(
        x + card_w - 2 * mm,
        y + card_h - 2 * mm,
        16 * mm,
        fill=1,
        stroke=0
    )

    # --------------------------------------------------------
    # Bottom-left decorative circle
    # --------------------------------------------------------

    c.setFillColor(
        LIGHTER_BLUE
    )

    c.circle(
        x + 2 * mm,
        y + 7 * mm,
        9 * mm,
        fill=1,
        stroke=0
    )

    c.restoreState()

    # ========================================================
    # HEADER
    # ========================================================

    logo_size = 13 * mm

    logo_x = (
        x + 3.5 * mm
    )

    text_x = (
        logo_x
        + logo_size
        + 3 * mm
    )

    usable_width = (
        card_w
        - (text_x - x)
        - 3 * mm
    )

    # --------------------------------------------------------
    # School name
    # --------------------------------------------------------

    school_name = (
        school.school_name
        if school
        else "School Name"
    )

    name_lines = _wrap_text(
        school_name,
        "Helvetica-Bold",
        7.5,
        usable_width
    )

    # --------------------------------------------------------
    # School address
    # --------------------------------------------------------

    address_lines = []

    if school and school.address:

        address_lines = _wrap_text(
            school.address,
            "Helvetica",
            5.5,
            usable_width
        )

    # --------------------------------------------------------
    # Header height
    # --------------------------------------------------------

    header_height = (
        6 * mm
        + len(name_lines) * 3 * mm
        + len(address_lines) * 2.4 * mm
        + 3 * mm
    )

    header_height = max(
        header_height,
        logo_size + 5 * mm
    )

    header_bottom_y = (
        y
        + card_h
        - header_height
    )

    # --------------------------------------------------------
    # Draw header
    # --------------------------------------------------------

    _draw_wave_band(
        c,
        x,
        header_bottom_y,
        card_w,
        header_height,
        curve_depth=4.5 * mm,
        color=DEEP_BLUE,
        curve_at="bottom"
    )

    # ========================================================
    # SCHOOL LOGO
    # ========================================================

    logo_y = (
        header_bottom_y
        + (header_height - logo_size) / 2
    )

    if school and school.logo:

        try:

            # White logo container
            c.setFillColor(white)

            c.roundRect(
                logo_x - 0.8 * mm,
                logo_y - 0.8 * mm,
                logo_size + 1.6 * mm,
                logo_size + 1.6 * mm,
                1.5 * mm,
                fill=1,
                stroke=0
            )

            c.drawImage(
                school.logo.path,
                logo_x,
                logo_y,
                width=logo_size,
                height=logo_size,
                preserveAspectRatio=True,
                mask="auto"
            )

        except Exception:
            pass

    # ========================================================
    # SCHOOL INFORMATION
    # ========================================================

    text_top = (
        y
        + card_h
        - 5 * mm
    )

    c.setFillColor(white)

    # --------------------------------------------------------
    # School name
    # --------------------------------------------------------

    c.setFont(
        "Helvetica-Bold",
        7.5
    )

    for line in name_lines:

        c.drawString(
            text_x,
            text_top,
            line
        )

        text_top -= 3 * mm

    # --------------------------------------------------------
    # Address
    # --------------------------------------------------------

    if address_lines:

        c.setFont(
            "Helvetica",
            5.5
        )

        for line in address_lines:

            c.drawString(
                text_x,
                text_top,
                line
            )

            text_top -= 2.4 * mm

    # --------------------------------------------------------
    # Established year
    # --------------------------------------------------------

    if (
        school
        and school.established_year
    ):

        c.setFont(
            "Helvetica",
            5.2
        )

        c.drawString(
            text_x,
            text_top,
            f"Estd. {school.established_year}"
        )

    # ========================================================
    # CARD TITLE
    # ========================================================

    title_y = (
        header_bottom_y
        - 5 * mm
    )

    c.setFillColor(
        DEEP_BLUE
    )

    c.setFont(
        "Helvetica-Bold",
        7
    )

    c.drawCentredString(
        x + card_w / 2,
        title_y,
        "STUDENT ID CARD"
    )

    # ========================================================
    # TITLE SEPARATOR
    # ========================================================

    c.setStrokeColor(
        HexColor("#D8F0FA")
    )

    c.setLineWidth(
        0.5
    )

    c.line(
        x + 12 * mm,
        title_y - 2 * mm,
        x + card_w - 12 * mm,
        title_y - 2 * mm
    )

    # ========================================================
    # STUDENT PHOTO
    # ========================================================

    photo_size = 22 * mm

    photo_x = (
        x
        + (card_w - photo_size) / 2
    )

    photo_y = (
        title_y
        - photo_size
        - 5 * mm
    )

    # --------------------------------------------------------
    # Photo white frame
    # --------------------------------------------------------

    c.setFillColor(
        white
    )

    c.roundRect(
        photo_x - 1.5 * mm,
        photo_y - 1.5 * mm,
        photo_size + 3 * mm,
        photo_size + 3 * mm,
        2 * mm,
        fill=1,
        stroke=0
    )

    # --------------------------------------------------------
    # Student photo
    # --------------------------------------------------------

    if student.photo:

        try:

            c.drawImage(
                student.photo.path,
                photo_x,
                photo_y,
                width=photo_size,
                height=photo_size,
                preserveAspectRatio=True,
                mask="auto"
            )

        except Exception:

            c.setFillColor(
                HexColor("#D6EEF9")
            )

            c.rect(
                photo_x,
                photo_y,
                photo_size,
                photo_size,
                fill=1,
                stroke=0
            )

    else:

        c.setFillColor(
            HexColor("#D6EEF9")
        )

        c.rect(
            photo_x,
            photo_y,
            photo_size,
            photo_size,
            fill=1,
            stroke=0
        )

    # ========================================================
    # STUDENT NAME
    # ========================================================

    full_name = (
        f"{student.user.first_name} "
        f"{student.user.last_name}"
    ).strip()

    display_name = (
        full_name
        if full_name
        else "N/A"
    )

    name_y = (
        photo_y
        - 5 * mm
    )

    c.setFillColor(
        HexColor("#173F5F")
    )

    c.setFont(
        "Helvetica-Bold",
        8
    )

    # Keep name from becoming too wide
    name_font_size = 8

    while (
        stringWidth(
            display_name,
            "Helvetica-Bold",
            name_font_size
        )
        > card_w - 8 * mm
        and name_font_size > 5
    ):

        name_font_size -= 0.5

    c.setFont(
        "Helvetica-Bold",
        name_font_size
    )

    c.drawCentredString(
        x + card_w / 2,
        name_y,
        display_name
    )

    # ========================================================
    # STUDENT DETAILS
    # ========================================================

    rows = [
        (
            "Class",
            str(class_obj)
        ),
        (
            "Roll No.",
            student.roll_number or "N/A"
        ),
        (
            "Email",
            student.user.email or "N/A"
        ),
        (
            "Contact",
            student.parent_contact or "N/A"
        ),
    ]

    label_x = (
        x + 5 * mm
    )

    value_x = (
        x + 20 * mm
    )

    row_y = (
        name_y
        - 5 * mm
    )

    row_gap = 4.2 * mm

    max_value_width = (
        card_w
        - 22 * mm
        - 5 * mm
    )

    for label, value in rows:

        value = str(value)

        # ----------------------------------------------------
        # Label
        # ----------------------------------------------------

        c.setFillColor(
            DEEP_BLUE
        )

        c.setFont(
            "Helvetica-Bold",
            5.8
        )

        c.drawString(
            label_x,
            row_y,
            label
        )

        # ----------------------------------------------------
        # Value
        # ----------------------------------------------------

        c.setFillColor(
            HexColor("#173F5F")
        )

        c.setFont(
            "Helvetica",
            5.8
        )

        # Shorten long text safely
        while (
            len(value) > 1
            and stringWidth(
                value,
                "Helvetica",
                5.8
            )
            > max_value_width
        ):

            value = value[:-1]

        c.drawString(
            value_x,
            row_y,
            value
        )

        row_y -= row_gap

    # ========================================================
    # FOOTER
    # ========================================================

    footer_height = 10 * mm

    _draw_wave_band(
        c,
        x,
        y,
        card_w,
        footer_height,
        curve_depth=3.5 * mm,
        color=DEEP_BLUE,
        curve_at="top"
    )

    # ========================================================
    # FOOTER TEXT
    # ========================================================

    c.setFillColor(
        white
    )

    c.setFont(
        "Helvetica-Bold",
        5.8
    )

    c.drawCentredString(
        x + card_w / 2,
        y + 3 * mm,
        f"VALID FOR ACADEMIC YEAR {academic_year}"
    )

    # ========================================================
    # OUTER BORDER
    # ========================================================

    c.setStrokeColor(
        HexColor("#245C87")
    )

    c.setLineWidth(
        0.8
    )

    c.roundRect(
        x,
        y,
        card_w,
        card_h,
        radius,
        fill=0,
        stroke=1
    )