from decimal import Decimal
from django.db import transaction
from apps.academics.models import Examination, Subject
from .models import Result


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