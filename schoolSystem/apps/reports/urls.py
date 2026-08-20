from rest_framework.routers import DefaultRouter
from .views import ReportViewSet

router = DefaultRouter()
router.register("", ReportViewSet, basename="report")

app_name = "reports"
urlpatterns = router.urls