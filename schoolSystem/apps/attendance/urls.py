from rest_framework.routers import DefaultRouter
from .views import AttendanceViewSet

router = DefaultRouter()
router.register("", AttendanceViewSet, basename="attendance")

app_name = "attendance"
urlpatterns = router.urls