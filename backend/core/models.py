import uuid
from django.db import models
from django.contrib.auth.models import User


class Document(models.Model):
    """Hospital document uploaded for compliance analysis."""

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PROCESSING = 'processing', 'Processing'
        INDEXED = 'indexed', 'Indexed'
        ERROR = 'error', 'Error'

    class DocType(models.TextChoices):
        PDF = 'pdf', 'PDF'
        DOCX = 'docx', 'DOCX'
        TXT = 'txt', 'TXT'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=512)
    file = models.FileField(upload_to='documents/%Y/%m/')
    doc_type = models.CharField(max_length=10, choices=DocType.choices)
    file_size = models.PositiveBigIntegerField(default=0)  # bytes
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    chunk_count = models.PositiveIntegerField(default=0)
    chroma_doc_id = models.CharField(max_length=255, blank=True)

    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='documents')
    hospital_name = models.CharField(max_length=255, blank=True)
    department = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)

    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['uploaded_by']),
        ]

    def __str__(self):
        return f'{self.name} ({self.status})'

    @property
    def file_size_display(self):
        if self.file_size < 1024:
            return f'{self.file_size} B'
        elif self.file_size < 1024 * 1024:
            return f'{self.file_size / 1024:.1f} KB'
        return f'{self.file_size / 1024 / 1024:.1f} MB'


class ComplianceReport(models.Model):
    """Generated compliance audit report."""

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        RUNNING = 'running', 'Running'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='reports')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    compliance_score = models.FloatField(null=True, blank=True)
    summary = models.TextField(blank=True)
    violations_json = models.JSONField(default=list)
    citations_json = models.JSONField(default=list)
    retrieved_chunks_json = models.JSONField(default=list)
    cot_reasoning = models.TextField(blank=True)

    llm_model = models.CharField(max_length=100, blank=True)
    embedding_model = models.CharField(max_length=100, blank=True)
    top_k_retrieved = models.PositiveSmallIntegerField(default=20)
    top_k_reranked = models.PositiveSmallIntegerField(default=8)
    processing_time_ms = models.PositiveIntegerField(null=True, blank=True)
    token_count = models.PositiveIntegerField(null=True, blank=True)

    pdf_report = models.FileField(upload_to='reports/%Y/%m/', null=True, blank=True)
    error_message = models.TextField(blank=True)

    requested_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='reports')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Report for {self.document.name} — Score: {self.compliance_score}'

    @property
    def violations_count(self):
        return len(self.violations_json)

    @property
    def processing_time_display(self):
        if self.processing_time_ms:
            return f'{self.processing_time_ms / 1000:.1f}s'
        return '—'


class Violation(models.Model):
    """Individual compliance violation within a report."""

    class Risk(models.TextChoices):
        CRITICAL = 'critical', 'Critical'
        HIGH = 'high', 'High'
        MEDIUM = 'medium', 'Medium'
        LOW = 'low', 'Low'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report = models.ForeignKey(ComplianceReport, on_delete=models.CASCADE, related_name='violations')
    regulation_id = models.CharField(max_length=100)
    title = models.CharField(max_length=512)
    description = models.TextField()
    risk = models.CharField(max_length=10, choices=Risk.choices)
    evidence = models.TextField()
    citation = models.TextField()
    corrective_action = models.TextField()
    category = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['report', 'risk']

    def __str__(self):
        return f'[{self.risk.upper()}] {self.title}'


class PolicyCorpusEntry(models.Model):
    """Metadata record for a policy document in the corpus."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source_file = models.CharField(max_length=512)
    title = models.CharField(max_length=512)
    organization = models.CharField(max_length=255)  # WHO, CDC, HHS, OSHA, TJC…
    version = models.CharField(max_length=50, blank=True)
    published_year = models.PositiveSmallIntegerField(null=True, blank=True)
    category = models.CharField(max_length=255, blank=True)
    chunk_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    indexed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['organization', 'title']
        verbose_name_plural = 'Policy corpus entries'

    def __str__(self):
        return f'[{self.organization}] {self.title}'


class AuditLog(models.Model):
    """System audit trail."""

    class Action(models.TextChoices):
        UPLOAD = 'upload', 'Document Upload'
        INDEX = 'index', 'Document Indexed'
        AUDIT = 'audit', 'Compliance Audit Run'
        QA = 'qa', 'Document QA Query'
        REPORT_DOWNLOAD = 'report_download', 'Report Downloaded'
        DELETE = 'delete', 'Document Deleted'
        LOGIN = 'login', 'User Login'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='audit_logs')
    action = models.CharField(max_length=30, choices=Action.choices)
    description = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f'{self.action} by {self.user} at {self.timestamp}'
