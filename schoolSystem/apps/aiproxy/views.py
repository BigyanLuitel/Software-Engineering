from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from apps.accounts.permissions import IsAdminOrTeacher, IsAdmin, IsStudent
from .serializers import AssistantQuerySerializer, QuestionPaperSerializer, NLQuerySerializer
from .client import ask_assistant, generate_question_paper, ask_nl_to_sql, AIServiceError


class AssistantView(APIView):
    """
    POST /api/ai/assistant/
    Available to Students (asking questions) -- Admin/Teacher aren't
    excluded here since testing/oversight is reasonable, but the
    primary intended user is Student.
    """
    permission_classes = [IsStudent]

    def post(self, request):
        serializer = AssistantQuerySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            response_text = ask_assistant(
                student_id=data["student_id"],
                class_id=data["class_id"],
                query_text=data["query_text"],
                subject_id=data.get("subject_id"),
                interaction_mode=data.get("interaction_mode", "chat"),
            )
        except AIServiceError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        return Response({"response_text": response_text})


class QuestionPaperView(APIView):
    """POST /api/ai/question-paper/ -- Teacher-facing."""
    permission_classes = [IsAdminOrTeacher]

    def post(self, request):
        serializer = QuestionPaperSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            questions = generate_question_paper(
                class_id=data["class_id"], subject_id=data["subject_id"],
                topic=data["topic"], difficulty=data["difficulty"],
                question_count=data.get("question_count", 10),
            )
        except AIServiceError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        return Response({"questions": questions})


class NLToSQLView(APIView):
    """POST /api/ai/query/ -- Admin-only, matches the read-only safety design from the FastAPI side."""
    permission_classes = [IsAdmin]

    def post(self, request):
        serializer = NLQuerySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            result = ask_nl_to_sql(admin_id=request.user.id, query_text=data["query_text"])
        except AIServiceError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        return Response(result)