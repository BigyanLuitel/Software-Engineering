from rest_framework.routers import DefaultRouter
from .views import AssignmentViewSet

router = DefaultRouter()
router.register("", AssignmentViewSet, basename="assignment")

app_name = "assignments"
urlpatterns = router.urls