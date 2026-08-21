from decimal import Decimal
from django.db import transaction
from apps.academics.models import Examination, Subject
from .models import Result

from apps.academics.models import Examination, Subject, Class
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from apps.students.models import Student
from apps.school.models import School


# (min_percentage, grade_letter, grade_point) -- checked highest-first
GRADE_SCALE = [
    (90, "A+", Decimal("4.0")),
    (80, "A", Decimal("3.6")),
    (70, "B+", Decimal("3.2")),
    (60, "B", Decimal("2.8")),
    (50, "C+", Decimal("2.4")),
    (40, "C", Decimal("2.0")),
    (0, "NG", Decimal("0.0")),   # anything below 40% is a fail -- pass mark is 40
]


def _grade_for_percentage(percentage: Decimal) -> tuple[str, Decimal]:
    """Returns (letter_grade, grade_point) for a given percentage."""
    for threshold, letter, point in GRADE_SCALE:
        if percentage >= threshold:
            return letter, point
    return "NG", Decimal("0.0")


@transaction.atomic
def compute_final_result(student, academic_year: str):
    """
    Computes and writes the Final (aggregate) Result for a student,
    for every subject they have complete term results in. Also
    computes grade_point (0.0-4.0 scale) and passed (bool, >= 40%)
    alongside the letter grade.
    """

    term_exams = Examination.objects.filter(
        academic_year=academic_year,
        term__in=[
            Examination.Term.FIRST, Examination.Term.SECOND,
            Examination.Term.THIRD, Examination.Term.FOURTH,
        ],
    )
    if term_exams.count() != 4:
        raise ValueError(
            f"Cannot compute Final: expected 4 term examinations for "
            f"{academic_year}, found {term_exams.count()}."
        )

    final_exam, _ = Examination.objects.get_or_create(
        term=Examination.Term.FINAL,
        academic_year=academic_year,
        defaults={"is_final": True},
    )

    term_results = Result.objects.filter(student=student, examination__in=term_exams)
    subject_ids = term_results.values_list("subject_id", flat=True).distinct()

    computed = []
    for subject_id in subject_ids:
        subject_results = term_results.filter(subject_id=subject_id)

        if subject_results.count() != 4:
            continue  # incomplete term data for this subject -- skip, don't guess

        percentages = [(r.marks_obtained / r.full_marks) * 100 for r in subject_results]
        avg_percentage = sum(percentages) / len(percentages)
        letter, point = _grade_for_percentage(avg_percentage)

        result, _ = Result.objects.update_or_create(
    student=student,
    examination=final_exam,
    subject_id=subject_id,
    defaults={
        "marks_obtained": round(avg_percentage, 2),
        "full_marks": Decimal("100"),
    },
)
        computed.append(result)

    return computed


def compute_gpa(student, academic_year: str) -> Decimal:
    """
    Overall GPA = simple average of grade_point across every subject's
    Final result, on the standard 0.0-4.0 scale. Requires
    compute_final_result() to have been run first for this student/year.
    """
    final_results = Result.objects.filter(
        student=student,
        examination__academic_year=academic_year,
        examination__is_final=True,
    )

    if not final_results.exists():
        raise ValueError(
            f"No Final results found for {student} in {academic_year}. "
            f"Run compute_final_result() first."
        )

    points = [r.grade_point for r in final_results]
    return round(sum(points) / len(points), 2)

CARD_WIDTH = 90 * mm
CARD_HEIGHT = 55 * mm
CARDS_PER_ROW = 2
MARGIN = 10 * mm
GAP = 5 * mm

def generate_admit_cards(examination, class_obj: Class) -> bytes:
    """
    Packs multiple admit cards per A4 page in a grid (2 per row),
    wrapping to a new row -- and a new page once a page fills up --
    rather than one card per page. This is the actual print-friendly
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
            c.showPage()  # current page is full -- start a new one

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
                school.logo.path,
                x + 3 * mm, y + CARD_HEIGHT - logo_size - 3 * mm,
                width=logo_size, height=logo_size,
                preserveAspectRatio=True, mask="auto",
            )
        except Exception:
            pass  

    # ---- Header Text ----
    # 1. School name left-aligned (shifted to make room for logo)
    text_start_x = x + logo_size + 6 * mm if (school and school.logo) else x + 4 * mm

    c.setFont("Helvetica-Bold", 10)
    c.drawString(text_start_x, y + CARD_HEIGHT - 8 * mm, school.school_name if school else "School Name")

    # 2. "ADMIT CARD" centered horizontally across the whole card width
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(x + CARD_WIDTH / 2, y + CARD_HEIGHT - 15 * mm, "ADMIT CARD")

#3. "Dhankuta, Nepal" centered horizontally across the whole card width
    c.setFont("Helvetica-Bold", 8)
    c.drawCentredString(x + CARD_WIDTH / 2, y + CARD_HEIGHT - 22 * mm, "Dhankuta-7, Nepal")
    # ---- Student photo, middle-right ----
    photo_size = 18 * mm
    photo_x = x + CARD_WIDTH - photo_size - 3 * mm
    
    # Vertically centered on the right edge
    photo_y = y + (CARD_HEIGHT - photo_size) / 2

    if student.photo:
        try:
            c.drawImage(
                student.photo.path,
                photo_x, photo_y,
                width=photo_size, height=photo_size,
                preserveAspectRatio=True, mask="auto",
            )
        except Exception:
            c.rect(photo_x, photo_y, photo_size, photo_size)  
    else:
        c.rect(photo_x, photo_y, photo_size, photo_size)  

    # ---- Student details, left side ----
    full_name = f"{student.user.first_name} {student.user.last_name}".strip()
    display_name = full_name if full_name else student.user.email

    c.setFont("Helvetica", 8)
    c.drawString(x + 4 * mm, y + CARD_HEIGHT - 24 * mm, f"Student: {display_name}")
    c.drawString(x + 4 * mm, y + CARD_HEIGHT - 30 * mm, f"Class: {class_obj}")
    c.drawString(x + 4 * mm, y + CARD_HEIGHT - 36 * mm, f"Examination: {examination}")

    # ---- Principal's signature line, bottom-right ----
    sig_line_width = 35 * mm
    sig_x = x + CARD_WIDTH - sig_line_width - 4 * mm
    sig_y = y + 8 * mm

    c.line(sig_x, sig_y, sig_x + sig_line_width, sig_y)
    c.setFont("Helvetica", 6)
    c.drawCentredString(sig_x + sig_line_width / 2, sig_y - 3 * mm, "Principal's Signature")