from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.urls import path
from core.models import AuditLog
from rest_framework import serializers


class AuditLogSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = AuditLog
        fields = ['id', 'action', 'description', 'user_name', 'ip_address', 'timestamp']

    def get_user_name(self, obj):
        return obj.user.username if obj.user else 'System'


class AuditLogsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        logs = AuditLog.objects.select_related('user').all()[:100]
        return Response(AuditLogSerializer(logs, many=True).data)


class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'full_name': user.get_full_name(),
            'is_admin': user.is_staff,
            'date_joined': user.date_joined,
        })


urlpatterns = [
    path('audit-logs/', AuditLogsView.as_view(), name='audit-logs'),
    path('profile/', UserProfileView.as_view(), name='user-profile'),
]
