from rest_framework import serializers
from core.models import ComplianceReport, Violation


class ViolationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Violation
        fields = ['id', 'regulation_id', 'title', 'description', 'risk',
                  'evidence', 'citation', 'corrective_action', 'category', 'created_at']


class ComplianceReportSerializer(serializers.ModelSerializer):
    violations = ViolationSerializer(many=True, read_only=True)
    document_name = serializers.SerializerMethodField()
    violations_count = serializers.ReadOnlyField()
    processing_time_display = serializers.ReadOnlyField()
    requested_by_name = serializers.SerializerMethodField()

    class Meta:
        model = ComplianceReport
        fields = [
            'id', 'document', 'document_name', 'status',
            'compliance_score', 'summary', 'violations', 'violations_count',
            'citations_json', 'cot_reasoning', 'llm_model', 'embedding_model',
            'top_k_retrieved', 'top_k_reranked', 'processing_time_ms',
            'processing_time_display', 'token_count', 'requested_by_name',
            'created_at', 'completed_at',
        ]
        read_only_fields = ['id', 'status', 'created_at', 'completed_at']

    def get_document_name(self, obj):
        return obj.document.name if obj.document else None

    def get_requested_by_name(self, obj):
        if obj.requested_by:
            return obj.requested_by.get_full_name() or obj.requested_by.username
        return None


class RunAuditSerializer(serializers.Serializer):
    document_id = serializers.UUIDField()
    llm_model = serializers.ChoiceField(
        choices=['gemini-2.5-flash', 'gemini-1.5-pro', 'gpt-4o'],
        default='gemini-2.5-flash',
        required=False,
    )
    top_k = serializers.IntegerField(min_value=5, max_value=30, default=20, required=False)
    rerank_k = serializers.IntegerField(min_value=3, max_value=15, default=8, required=False)


class QARequestSerializer(serializers.Serializer):
    query = serializers.CharField()
    document_id = serializers.UUIDField(required=False, allow_null=True)
