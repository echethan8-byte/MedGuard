from django.contrib import admin
from .models import Document, ComplianceReport, Violation, PolicyCorpusEntry, AuditLog


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['name', 'doc_type', 'status', 'chunk_count', 'uploaded_by', 'created_at']
    list_filter = ['status', 'doc_type', 'created_at']
    search_fields = ['name', 'hospital_name', 'department']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(ComplianceReport)
class ComplianceReportAdmin(admin.ModelAdmin):
    list_display = ['document', 'compliance_score', 'violations_count', 'status', 'llm_model', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['document__name']
    readonly_fields = ['id', 'created_at', 'completed_at']


@admin.register(Violation)
class ViolationAdmin(admin.ModelAdmin):
    list_display = ['title', 'risk', 'regulation_id', 'category', 'report']
    list_filter = ['risk', 'category']
    search_fields = ['title', 'regulation_id', 'description']


@admin.register(PolicyCorpusEntry)
class PolicyCorpusEntryAdmin(admin.ModelAdmin):
    list_display = ['title', 'organization', 'category', 'chunk_count', 'is_active', 'indexed_at']
    list_filter = ['organization', 'is_active']
    search_fields = ['title', 'organization']


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['action', 'user', 'description', 'ip_address', 'timestamp']
    list_filter = ['action', 'timestamp']
    readonly_fields = ['id', 'timestamp']
