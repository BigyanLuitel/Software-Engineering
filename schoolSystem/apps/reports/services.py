from apps.students.models import Student
from apps.attendance.services import compute_attendance_percentage
from apps.results.services import compute_gpa
from apps.fees.models import FeeInvoice
from .models import Report


def generate_report(report_type, generated_by, class_obj=None, date_from=None, date_to=None, academic_year=None):
    """
    Dispatches to the right compute function and stores the result.
    Deliberately reuses attendance/results/fees SERVICE functions
    rather than re-querying those apps' models directly -- this is
    the actual payoff of the lego architecture: each app's business
    logic (grade calc, carry-forward dues, attendance %) lives in
    exactly one place, and Reports just composes those, rather than
    duplicating the math and risking it drifting out of sync.
    """
    students = Student.objects.filter(student_class=class_obj) if class_obj else Student.objects.all()

    if report_type == Report.ReportType.ATTENDANCE_SUMMARY:
        data = _attendance_summary(students, date_from, date_to)
    elif report_type == Report.ReportType.FEE_SUMMARY:
        data = _fee_summary(students)
    elif report_type == Report.ReportType.ACADEMIC_SUMMARY:
        data = _academic_summary(students, academic_year)
    else:
        raise ValueError(f"Unknown report_type: {report_type}")

    return Report.objects.create(
        report_type=report_type, generated_by=generated_by, class_obj=class_obj,
        date_from=date_from, date_to=date_to, data=data,
    )


def _attendance_summary(students, date_from, date_to):
    return [
        {"student_id": s.id, "email": s.user.email, "attendance_percentage": compute_attendance_percentage(s, date_from, date_to)}
        for s in students
    ]


def _fee_summary(students):
    result = []
    for s in students:
        outstanding = sum((inv.outstanding for inv in s.fee_invoices.exclude(status="PAID")), 0)
        result.append({"student_id": s.id, "email": s.user.email, "total_outstanding": float(outstanding)})
    return result


def _academic_summary(students, academic_year):
    result = []
    for s in students:
        try:
            gpa = float(compute_gpa(s, academic_year))
        except ValueError:
            gpa = None  # Final not yet computed for this student -- don't crash the whole report over one student
        result.append({"student_id": s.id, "email": s.user.email, "gpa": gpa})
    return result