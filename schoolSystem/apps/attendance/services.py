from django.db import transaction
from apps.students.models import Student
from .models import Attendance
from datetime import date as date_cls


@transaction.atomic
def mark_class_attendance(class_obj, date, status_map: dict):
    """
    Marks attendance for every student in a class, in one call.

    status_map: {student_id: "PRESENT" | "ABSENT" | "LATE" | "EXCUSED"}
    This matches how a teacher actually works -- they see a full
    class roster and mark each student's status in one screen/submit,
    not one API call per student. update_or_create means re-submitting
    the same day (e.g. correcting a mistake) safely overwrites rather
    than creating duplicates or erroring on the unique_together constraint.
    """

    students = Student.objects.filter(student_class=class_obj)
    results = []

    for student in students:
        status = status_map.get(student.id, Attendance.Status.ABSENT)
        # Default to ABSENT if a student was left out of status_map --
        # forces an explicit choice rather than silently skipping
        # students the teacher forgot to mark.

        record, _ = Attendance.objects.update_or_create(
            student=student,
            date=date,
            defaults={"status": status},
        )
        results.append(record)

    return results

def compute_attendance_percentage(student, date_from: date_cls, date_to: date_cls) -> float:
    """
    Percentage of days marked PRESENT or LATE (both count as
    "attended") out of total marked days in the range. EXCUSED days
    are deliberately excluded from the denominator entirely -- an
    excused absence shouldn't count against a student's attendance
    rate, but it also isn't "attended," so it's neither a pass nor
    a fail day, just not counted at all.
    """
    records = Attendance.objects.filter(
        student=student, date__gte=date_from, date__lte=date_to
    ).exclude(status=Attendance.Status.EXCUSED)

    total = records.count()
    if total == 0:
        return 0.0

    attended = records.filter(status__in=[Attendance.Status.PRESENT, Attendance.Status.LATE]).count()
    return round((attended / total) * 100, 2)