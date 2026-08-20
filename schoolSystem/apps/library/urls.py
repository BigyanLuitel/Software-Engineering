from rest_framework.routers import DefaultRouter
from .views import BookViewSet, CirculationViewSet

router = DefaultRouter()
router.register("books", BookViewSet, basename="book")
router.register("circulations", CirculationViewSet, basename="circulation")

app_name = "library"
urlpatterns = router.urls