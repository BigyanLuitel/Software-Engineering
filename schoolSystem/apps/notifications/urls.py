from rest_framework.routers import DefaultRouter
from .views import NotificationViewSet, NotificationRecipientViewSet

router = DefaultRouter()
router.register("broadcast", NotificationViewSet, basename="notification")
router.register("inbox", NotificationRecipientViewSet, basename="notificationrecipient")

app_name = "notifications"
urlpatterns = router.urls