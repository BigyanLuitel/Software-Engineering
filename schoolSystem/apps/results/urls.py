from rest_framework.routers import DefaultRouter
from .views import ResultViewSet

router = DefaultRouter()
router.register("", ResultViewSet, basename="result")

app_name = "results"
urlpatterns = router.urls