
from django.db import models
from django.conf import settings
from apps.academics.models import Class


class Report(models.Model):
    """
    A generated report snapshot. `data` stores the computed result as
    JSON at generation time -- reports are point-in-time snapshots,
    not live views, so a report generated today still shows today's
    numbers even if attendance/fees change tomorrow. That's the
    correct behavior for a report someone might print or reference
    later, versus a live dashboard which should always show current data.
    """

    class ReportType(models.TextChoices):
        ATTENDANCE_SUMMARY = "ATTENDANCE_SUMMARY", "Attendance Summary"
        FEE_SUMMARY = "FEE_SUMMARY", "Fee Summary"
        ACADEMIC_SUMMARY = "ACADEMIC_SUMMARY", "Academic Summary"

    report_type = models.CharField(max_length=30, choices=ReportType.choices)
    generated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    class_obj = models.ForeignKey(Class, on_delete=models.SET_NULL, null=True, blank=True)
    date_from = models.DateField(null=True, blank=True)
    date_to = models.DateField(null=True, blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    data = models.JSONField(default=dict)

    def __str__(self):
        return f"{self.get_report_type_display()} \u2013 {self.class_obj or 'All Classes'} ({self.generated_at:%Y-%m-%d})"