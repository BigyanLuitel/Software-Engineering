from datetime import datetime
from decimal import Decimal, InvalidOperation
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.accounts.permissions import IsAdmin, IsAdminOrTeacher, IsStudent
from .models import FeeCategory, FeeStructure, FeeInvoice, StudentFeeAssignment
from .serializers import FeeCategorySerializer, FeeStructureSerializer, FeeInvoiceSerializer, StudentFeeAssignmentSerializer
from .services import generate_monthly_invoices, generate_student_monthly_bill, record_payment
from django.http import HttpResponse
from apps.students.models import Student
from .services import generate_monthly_invoices, record_payment, generate_student_monthly_bill

class FeeCategoryViewSet(viewsets.ModelViewSet):
    queryset = FeeCategory.objects.all()
    serializer_class = FeeCategorySerializer
    permission_classes = [IsAdmin]


class FeeStructureViewSet(viewsets.ModelViewSet):
    queryset = FeeStructure.objects.select_related("class_obj", "fee_category").all()
    serializer_class = FeeStructureSerializer
    permission_classes = [IsAdmin]


class FeeInvoiceViewSet(viewsets.ModelViewSet):
    queryset = FeeInvoice.objects.select_related("student__user", "fee_category").all()
    serializer_class = FeeInvoiceSerializer
    permission_classes = [IsAdmin]
    def get_permissions(self):
        if self.action == "me":
            return [IsStudent()]
        return [IsAdmin()]

    @action(detail=False, methods=["get"], url_path="me", permission_classes=[IsStudent])
    def me(self, request):
        """GET /api/fees/invoices/me/ -- a student's own invoices only."""
        try:
            student = Student.objects.get(user=request.user)
        except Student.DoesNotExist:
            return Response({"detail": "No student profile found for this account."}, status=status.HTTP_404_NOT_FOUND)

        invoices = FeeInvoice.objects.filter(student=student).select_related("fee_category")
        return Response(FeeInvoiceSerializer(invoices, many=True).data)

    @action(detail=False, methods=["post"], url_path="generate-monthly")
    def generate_monthly(self, request):
        """
        POST /api/fees/invoices/generate-monthly/
        Body: {"month": "2026-04", "due_date": "2026-04-10", "academic_year": "2025-2026"}
        """
        try:
            month = request.data["month"]
            due_date = datetime.strptime(request.data["due_date"], "%Y-%m-%d").date()
            academic_year = request.data["academic_year"]
        except (KeyError, ValueError):
            return Response({"detail": "month, due_date (YYYY-MM-DD), and academic_year are required."}, status=status.HTTP_400_BAD_REQUEST)

        invoices = generate_monthly_invoices(month, due_date, academic_year)
        return Response(FeeInvoiceSerializer(invoices, many=True).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="pay")
    def pay(self, request, pk=None):
        """
        POST /api/fees/invoices/{id}/pay/
        Body: {"amount": 2000}
        detail=True because this DOES operate on one specific
        existing invoice (identified by the URL's pk), unlike
        generate-monthly which isn't tied to any single record.
        """
        invoice = self.get_object()

        try:
            amount = Decimal(str(request.data.get("amount")))
        except (InvalidOperation, TypeError):
            return Response({"detail": "A valid numeric amount is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            updated_invoice = record_payment(invoice, amount)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(FeeInvoiceSerializer(updated_invoice).data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=["get"], url_path="bill")
    def bill(self, request):
        student_id = request.query_params.get("student_id")
        month = request.query_params.get("month")

        try:
            student = Student.objects.get(id=student_id)
        except Student.DoesNotExist:
            return Response({"detail": "Student not found."}, status=status.HTTP_404_NOT_FOUND)

        if not month:
            return Response({"detail": "month is required."}, status=status.HTTP_400_BAD_REQUEST)

        pdf_bytes = generate_student_monthly_bill(student, month)
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="bill_{student.id}_{month}.pdf"'
        return response

class StudentFeeAssignmentViewSet(viewsets.ModelViewSet):
    queryset = StudentFeeAssignment.objects.select_related("student__user", "fee_category").all()
    serializer_class = StudentFeeAssignmentSerializer
    permission_classes = [IsAdmin]

    @action(detail=False, methods=["get"], url_path="for-student")
    def for_student(self, request):
        """GET /api/fees/student-assignments/for-student/?student_id=1"""
        student_id = request.query_params.get("student_id")
        assignments = StudentFeeAssignment.objects.filter(student_id=student_id, is_active=True).select_related("fee_category")
        return Response(StudentFeeAssignmentSerializer(assignments, many=True).data)