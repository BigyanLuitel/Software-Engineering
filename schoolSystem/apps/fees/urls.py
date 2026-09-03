from rest_framework.routers import DefaultRouter
from .views import FeeCategoryViewSet, FeeStructureViewSet, FeeInvoiceViewSet, StudentFeeAssignmentViewSet

router = DefaultRouter()
router.register("categories", FeeCategoryViewSet, basename="feecategory")
router.register("structures", FeeStructureViewSet, basename="feestructure")
router.register("invoices", FeeInvoiceViewSet, basename="feeinvoice")
router.register("student-assignments", StudentFeeAssignmentViewSet, basename="studentfeeassignment")


app_name = "fees"
urlpatterns = router.urls