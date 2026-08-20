from rest_framework.routers import DefaultRouter
from .views import TeacherViewSet

router = DefaultRouter()
router.register("", TeacherViewSet, basename="teacher")

app_name = "teachers"
urlpatterns = router.urls