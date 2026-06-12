from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AuditViewSet, RunAuditView

router = DefaultRouter()
router.register(r'reports', AuditViewSet, basename='report')

urlpatterns = [
    path('audit/', RunAuditView.as_view(), name='run-audit'),
    path('', include(router.urls)),
]
