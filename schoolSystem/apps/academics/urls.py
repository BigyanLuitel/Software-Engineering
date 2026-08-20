from rest_framework.routers import DefaultRouter
from .views import ClassViewSet, SubjectViewSet, ClassSubjectViewSet, ExaminationViewSet

router = DefaultRouter()
router.register("classes", ClassViewSet, basename="class")
router.register("subjects", SubjectViewSet, basename="subject")
router.register("class-subjects", ClassSubjectViewSet, basename="classsubject")
router.register("examinations", ExaminationViewSet, basename="examination")

app_name = "academics"
urlpatterns = router.urls