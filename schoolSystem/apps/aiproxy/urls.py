from django.urls import path
from .views import AssistantView, QuestionPaperView, NLToSQLView

app_name = "aiproxy"

urlpatterns = [
    path("assistant/", AssistantView.as_view(), name="assistant"),
    path("question-paper/", QuestionPaperView.as_view(), name="question-paper"),
    path("query/", NLToSQLView.as_view(), name="nl-to-sql"),
]