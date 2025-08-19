from rest_framework.routers import DefaultRouter
from .views import StoreViewSet, ReportViewSet

router = DefaultRouter()
router.register(r"stores", StoreViewSet, basename="store")
router.register(r"reports", ReportViewSet, basename="storereport")

urlpatterns = router.urls
