from datetime import date
from decimal import Decimal
from django.db import transaction
from apps.students.models import Student

from django.db.models import Sum
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from apps.school.models import School
from .models import FeeCategory, FeeStructure, FeeInvoice, StudentFeeAssignment


@transaction.atomic
def generate_monthly_invoices(month: str, due_date: date, academic_year: str):
    """
    Generates this month's FeeInvoice for every Student, for every
    RECURRING FeeCategory -- from TWO sources: the class-wide
    FeeStructure rate, AND any active per-student StudentFeeAssignment
    (bus, computer, etc.) for that same category. If a student has
    BOTH a class-wide rate and a personal assignment for the same
    category, the personal assignment's amount is used instead of
    the class-wide one -- it's more specific, so it wins.
    """

    recurring_categories = FeeCategory.objects.filter(is_recurring=True)
    created = []

    for student in Student.objects.select_related("student_class"):
        if not student.student_class:
            continue

        student_assignments = {
            a.fee_category_id: a.amount
            for a in StudentFeeAssignment.objects.filter(student=student, is_active=True)
        }

        for category in recurring_categories:
            if FeeInvoice.objects.filter(student=student, fee_category=category, month=month).exists():
                continue

            amount = student_assignments.get(category.id)

            if amount is None:
                structure = FeeStructure.objects.filter(
                    class_obj=student.student_class,
                    fee_category=category,
                    academic_year=academic_year,
                ).first()
                if not structure:
                    continue
                amount = structure.amount

            previous_outstanding = _sum_prior_outstanding(student, category, before_month=month)

            invoice = FeeInvoice.objects.create(
                student=student,
                fee_category=category,
                month=month,
                amount_due=amount,
                previous_due=previous_outstanding,
                due_date=due_date,
                status=FeeInvoice.Status.UNPAID,
            )
            created.append(invoice)

    return created


def _sum_prior_outstanding(student, category, before_month: str) -> Decimal:
    """
    Computes true outstanding balance as (total ever charged) minus
    (total ever paid), across all prior invoices in this category.

    This must NOT sum each prior invoice's .outstanding property --
    that value already includes THAT invoice's own previous_due,
    so chaining them across months double-counts old debt every
    time it gets carried forward again. Summing raw amount_due and
    amount_paid avoids any compounding, because each is only ever
    counted once, at its original source.
    """
    prior = FeeInvoice.objects.filter(
        student=student, fee_category=category, month__lt=before_month,
    )
    total_charged = prior.aggregate(t=Sum("amount_due"))["t"] or Decimal("0")
    total_paid = prior.aggregate(t=Sum("amount_paid"))["t"] or Decimal("0")

    return max(total_charged - total_paid, Decimal("0"))

@transaction.atomic
def record_payment(invoice: FeeInvoice, amount: Decimal):
    if amount <= 0:
        raise ValueError("Payment amount must be positive.")

    if invoice.status == FeeInvoice.Status.PAID:
        raise ValueError("This invoice is already fully paid.")

    invoice.amount_paid += amount

    if invoice.amount_paid >= invoice.total_due:
        invoice.status = FeeInvoice.Status.PAID
    elif invoice.amount_paid > 0:
        invoice.status = FeeInvoice.Status.PARTIALLY_PAID
    else:
        invoice.status = FeeInvoice.Status.UNPAID

    invoice.save()
    return invoice
from io import BytesIO
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.platypus import Table, TableStyle, Paragraph, Spacer, Image
from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame, FrameBreak
from reportlab.lib.pagesizes import landscape
from apps.school.models import School
import datetime
from functools import partial

def _draw_bill_borders(canvas_obj, doc, margin, half_width, gap, page_height):
    canvas_obj.saveState()
    canvas_obj.setStrokeColor(colors.HexColor("#1769AA"))
    canvas_obj.setLineWidth(0.8)

    canvas_obj.roundRect(
        margin,
        margin,
        half_width,
        page_height - 2 * margin,
        1.5 * mm
    )

    canvas_obj.roundRect(
        margin + half_width + gap,
        margin,
        half_width,
        page_height - 2 * margin,
        1.5 * mm
    )

    # Signature - fixed at the bottom of each bill
    signature_y = margin + 18 * mm
    signature_width = 35 * mm

    left_signature_x = margin + half_width - signature_width
    right_signature_x = margin + half_width + gap + half_width - signature_width

    canvas_obj.setStrokeColor(colors.HexColor("#222222"))
    canvas_obj.setLineWidth(0.5)

    canvas_obj.line(
        left_signature_x,
        signature_y,
        left_signature_x + signature_width,
        signature_y
    )

    canvas_obj.line(
        right_signature_x,
        signature_y,
        right_signature_x + signature_width,
        signature_y
    )

    canvas_obj.setFont("Helvetica", 6.5)
    canvas_obj.setFillColor(colors.HexColor("#222222"))

    canvas_obj.drawRightString(
        left_signature_x + signature_width,
        signature_y - 4 * mm,
        "Authorized Signature"
    )

    canvas_obj.drawRightString(
        right_signature_x + signature_width,
        signature_y - 4 * mm,
        "Authorized Signature"
    )

    canvas_obj.restoreState()

def _build_bill_copy(student, month, invoices, school, copy_label, content_width):
    styles = getSampleStyleSheet()

    school_name_style = ParagraphStyle(
        "SchoolName",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=10,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#111111")
    )

    bill_title_style = ParagraphStyle(
        "BillTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=9,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#1769AA")
    )

    issue_style = ParagraphStyle(
        "Issue",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=6.5,
        leading=8,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#222222")
    )

    info_label_style = ParagraphStyle(
        "InfoLabel",
        fontName="Helvetica-Bold",
        fontSize=6.5,
        leading=7.5,
        textColor=colors.HexColor("#111111")
    )

    info_value_style = ParagraphStyle(
        "InfoValue",
        fontName="Helvetica",
        fontSize=6.5,
        leading=7.5,
        textColor=colors.HexColor("#222222")
    )

    table_header_style = ParagraphStyle(
        "TableHeader",
        fontName="Helvetica-Bold",
        fontSize=6.2,
        leading=7,
        alignment=TA_CENTER,
        textColor=colors.white
    )

    table_text_style = ParagraphStyle(
        "TableText",
        fontName="Helvetica",
        fontSize=6.2,
        leading=7,
        textColor=colors.HexColor("#222222")
    )

    table_bold_style = ParagraphStyle(
        "TableBold",
        fontName="Helvetica-Bold",
        fontSize=6.2,
        leading=7,
        textColor=colors.HexColor("#111111")
    )

    flowables = []

    school_name = school.school_name if school else "School Name"
    issue_date = datetime.date.today().strftime("%d-%m-%Y")

    logo_cell = ""

    if school and school.logo:
        try:
            logo_cell = Image(
                school.logo.path,
                width=9 * mm,
                height=9 * mm
            )
        except Exception:
            pass

    header_text = [
        Paragraph(school_name, school_name_style),
        Paragraph(f"FEE BILL — {copy_label}", bill_title_style),
        Paragraph(f"Issued: {issue_date}", issue_style)
    ]

    header_table = Table(
        [[logo_cell, header_text]],
        colWidths=[
            11 * mm,
            content_width - 11 * mm
        ]
    )

    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0)
    ]))

    flowables.append(header_table)
    flowables.append(Spacer(1, 3 * mm))

    full_name = (
        f"{student.user.first_name} {student.user.last_name}".strip()
        or student.user.email
    )

    parent_name = student.parent_name or "N/A"
    parent_contact = student.parent_contact or "N/A"

    info_col_widths = [
        content_width * 0.155,
        content_width * 0.345,
        content_width * 0.155,
        content_width * 0.345
    ]

    info_data = [
        [
            Paragraph("Name:", info_label_style),
            Paragraph(full_name, info_value_style),
            Paragraph("Class:", info_label_style),
            Paragraph(str(student.student_class or "N/A"), info_value_style)
        ],
        [
            Paragraph("Month:", info_label_style),
            Paragraph(month, info_value_style),
            Paragraph("Parent:", info_label_style),
            Paragraph(parent_name, info_value_style)
        ],
        [
            Paragraph("Contact:", info_label_style),
            Paragraph(parent_contact, info_value_style),
            "",
            ""
        ]
    ]

    info_table = Table(
        info_data,
        colWidths=info_col_widths
    )

    info_table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#999999")),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#D0D0D0")),

        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F3F3F3")),
        ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#F3F3F3")),

        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),

        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),

        ("SPAN", (1, 2), (3, 2))
    ]))

    flowables.append(info_table)
    flowables.append(Spacer(1, 4 * mm))

    rows = [
        [
            Paragraph("Category", table_header_style),
            Paragraph("Due Date", table_header_style),
            Paragraph("Due", table_header_style),
            Paragraph("Paid", table_header_style),
            Paragraph("Owed", table_header_style)
        ]
    ]

    grand_total_due = 0
    grand_total_paid = 0
    grand_total_outstanding = 0

    for inv in invoices:
        rows.append([
            Paragraph(str(inv.fee_category.name), table_text_style),
            Paragraph(str(inv.due_date), table_text_style),
            Paragraph(f"{inv.total_due:.2f}", table_text_style),
            Paragraph(f"{inv.amount_paid:.2f}", table_text_style),
            Paragraph(f"{inv.outstanding:.2f}", table_text_style)
        ])

        grand_total_due += inv.total_due
        grand_total_paid += inv.amount_paid
        grand_total_outstanding += inv.outstanding

    rows.append([
        Paragraph("TOTAL", table_bold_style),
        "",
        Paragraph(f"{grand_total_due:.2f}", table_bold_style),
        Paragraph(f"{grand_total_paid:.2f}", table_bold_style),
        Paragraph(f"{grand_total_outstanding:.2f}", table_bold_style)
    ])

    table_col_widths = [
        content_width * 0.27,
        content_width * 0.18,
        content_width * 0.18,
        content_width * 0.18,
        content_width * 0.19
    ]

    table = Table(
        rows,
        colWidths=table_col_widths,
        repeatRows=1
    )

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1769AA")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),

        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),

        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#EAF4FA")),

        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#A8A8A8")),

        ("ALIGN", (0, 0), (0, -1), "LEFT"),
        ("ALIGN", (1, 0), (1, -1), "CENTER"),
        ("ALIGN", (2, 0), (4, -1), "RIGHT"),

        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),

        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3)
    ]))

    flowables.append(table)

    return flowables

def generate_student_monthly_bill(student, month) -> bytes:
    school = School.objects.first()

    invoices = (
        student.fee_invoices
        .filter(month=month)
        .select_related("fee_category")
    )

    PAGE_WIDTH = 210 * mm
    PAGE_HEIGHT = 90 * mm

    margin = 8 * mm
    gap = 15 * mm

    half_width = (
        PAGE_WIDTH - 2 * margin - gap
    ) / 2

    # Space between the blue border and content
    content_padding = 4 * mm

    content_width = half_width - 2 * content_padding

    buffer = BytesIO()

    frame_height = PAGE_HEIGHT - 2 * margin

    left_frame = Frame(
        margin + content_padding,
        margin + content_padding,
        content_width,
        frame_height - 2 * content_padding,
        id="left",
        leftPadding=0,
        rightPadding=0,
        topPadding=0,
        bottomPadding=0
    )

    right_frame = Frame(
        margin + half_width + gap + content_padding,
        margin + content_padding,
        content_width,
        frame_height - 2 * content_padding,
        id="right",
        leftPadding=0,
        rightPadding=0,
        topPadding=0,
        bottomPadding=0
    )

    doc = BaseDocTemplate(
        buffer,
        pagesize=(PAGE_WIDTH, PAGE_HEIGHT),
        leftMargin=0,
        rightMargin=0,
        topMargin=0,
        bottomMargin=0
    )

    border_fn = partial(
        _draw_bill_borders,
        margin=margin,
        half_width=half_width,
        gap=gap,
        page_height=PAGE_HEIGHT
    )

    doc.addPageTemplates([
        PageTemplate(
            id="bill",
            frames=[
                left_frame,
                right_frame
            ],
            onPage=border_fn
        )
    ])

    story = []

    story.extend(
        _build_bill_copy(
            student,
            month,
            invoices,
            school,
            "School Copy",
            content_width
        )
    )

    story.append(FrameBreak())

    story.extend(
        _build_bill_copy(
            student,
            month,
            invoices,
            school,
            "Parent Copy",
            content_width
        )
    )

    doc.build(story)

    buffer.seek(0)

    return buffer.getvalue()