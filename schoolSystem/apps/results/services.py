from decimal import Decimal
from django.db import transaction
from apps.academics.models import Examination, Subject
from .models import Result


GRADE_SCALE = [
    (90, "A+"), (80, "A"), (70, "B+"), (60, "B"),
    (50, "C+"), (40, "C"), (0, "D"),
]


def _grade_for_percentage(percentage: Decimal) -> str:
    for threshold, grade in GRADE_SCALE:
        if percentage >= threshold:
            return grade
    return "D"


@transaction.atomic
def compute_final_result(student, academic_year: str):
    """
    Computes and writes the Final (aggregate) Result for a student,
    for every subject they have term results in.

    Design decision: this REQUIRES all 4 real terms (1st-4th) to
    exist for the student before computing Final. A Final based on
    only 2 or 3 terms would be silently misleading -- better to fail
    loudly here than produce a number that looks authoritative but
    isn't actually complete.

    Averaging is done on PERCENTAGE, not raw marks_obtained -- this
    matters if full_marks ever differs between terms (e.g. Term 1
    out of 100, Term 3 out of 50 for some reason). Averaging raw
    marks would silently produce a wrong result in that case;
    averaging percentage is correct regardless.
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
            # This subject wasn't marked in all 4 terms for this student --
            # skip it rather than average an incomplete set silently.
            continue

        percentages = [
            (r.marks_obtained / r.full_marks) * 100 for r in subject_results
        ]
        avg_percentage = sum(percentages) / len(percentages)

        result, _ = Result.objects.update_or_create(
            student=student,
            examination=final_exam,
            subject_id=subject_id,
            defaults={
                "marks_obtained": round(avg_percentage, 2),
                "full_marks": Decimal("100"),
                "grade": _grade_for_percentage(avg_percentage),
            },
        )
        computed.append(result)

    return computed