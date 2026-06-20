from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AuditViewSet, RunAuditView, DocumentQAView

router = DefaultRouter()
router.register(r'reports', AuditViewSet, basename='report')

urlpatterns = [
    path('audit/', RunAuditView.as_view(), name='run-audit'),
    path('qa/', DocumentQAView.as_view(), name='document-qa'),
    path('', include(router.urls)),
]
