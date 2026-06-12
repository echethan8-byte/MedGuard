from rest_framework import serializers
from core.models import Document


class DocumentSerializer(serializers.ModelSerializer):
    file_size_display = serializers.ReadOnlyField()
    uploaded_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = [
            'id', 'name', 'doc_type', 'file_size', 'file_size_display',
            'status', 'chunk_count', 'hospital_name', 'department',
            'notes', 'error_message', 'uploaded_by_name',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'status', 'chunk_count', 'created_at', 'updated_at']

    def get_uploaded_by_name(self, obj):
        if obj.uploaded_by:
            return obj.uploaded_by.get_full_name() or obj.uploaded_by.username
        return None


class DocumentUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    hospital_name = serializers.CharField(max_length=255, required=False, default='')
    department = serializers.CharField(max_length=255, required=False, default='')
    notes = serializers.CharField(required=False, default='')
