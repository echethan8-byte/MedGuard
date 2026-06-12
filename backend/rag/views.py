"""
rag/views.py — Compliance audit endpoint and report management.
"""
import logging
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView

from core.models import Document, ComplianceReport, Violation, AuditLog
from .serializers import ComplianceReportSerializer, RunAuditSerializer

logger = logging.getLogger('medguard')


class AuditViewSet(viewsets.ReadOnlyModelViewSet):
    """List and retrieve compliance reports."""
    permission_classes = [IsAuthenticated]
    serializer_class = ComplianceReportSerializer

    def get_queryset(self):
        return ComplianceReport.objects.select_related('document', 'requested_by').all()

    @action(detail=True, methods=['get'], permission_classes=[AllowAny])
    def download(self, request, pk=None):
        """Download PDF report."""
        from django.conf import settings

        report = self.get_object()
        if not report.pdf_report:
            return Response({'error': 'PDF not yet generated.'}, status=404)

        if not request.user.is_authenticated and not settings.DEBUG:
            return Response({'detail': 'Authentication credentials were not provided.'}, status=401)

        AuditLog.objects.create(
            user=request.user if request.user.is_authenticated else None,
            action=AuditLog.Action.REPORT_DOWNLOAD,
            description=f'Downloaded report: {report.id}',
            ip_address=request.META.get('REMOTE_ADDR'),
        )

        with open(report.pdf_report.path, 'rb') as f:
            pdf_bytes = f.read()

        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="compliance_report_{report.id}.pdf"'
        return response


class RunAuditView(APIView):
    """POST /api/rag/audit/ — Run a new compliance audit."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = RunAuditSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        doc_id = serializer.validated_data['document_id']
        try:
            document = Document.objects.get(id=doc_id)
        except Document.DoesNotExist:
            return Response({'error': 'Document not found.'}, status=404)

        if document.status not in [Document.Status.INDEXED, 'ready']:
            return Response({'error': f'Document is not indexed (status={document.status}).'}, status=400)

        # Create report record
        report = ComplianceReport.objects.create(
            document=document,
            status=ComplianceReport.Status.RUNNING,
            requested_by=request.user,
            llm_model=serializer.validated_data.get('llm_model', 'gemini-2.5-flash'),
            top_k_retrieved=serializer.validated_data.get('top_k', 20),
            top_k_reranked=serializer.validated_data.get('rerank_k', 8),
        )

        try:
            self._run_analysis(report, document)
        except Exception as e:
            report.status = ComplianceReport.Status.FAILED
            report.error_message = str(e)
            report.save()
            logger.error(f"Audit failed for doc={doc_id}: {e}")
            return Response({'error': str(e)}, status=500)

        AuditLog.objects.create(
            user=request.user,
            action=AuditLog.Action.AUDIT,
            description=f'Ran compliance audit on: {document.name}',
            metadata={'report_id': str(report.id), 'score': report.compliance_score},
            ip_address=request.META.get('REMOTE_ADDR'),
        )

        return Response(ComplianceReportSerializer(report).data, status=201)

    def _run_analysis(self, report: ComplianceReport, document: Document):
        from django.conf import settings
        from rag.retriever import retrieve_policy_chunks, retrieve_document_chunks, rerank_chunks
        from rag.analyzer import run_compliance_analysis, mock_analysis_result
        from rag.report_generator import generate_pdf_report
        import tempfile, os
        from django.core.files.base import ContentFile

        # 1. Retrieve policy chunks
        query = f"healthcare compliance regulations infection control {document.name}"
        policy_chunks_raw = retrieve_policy_chunks(query, k=report.top_k_retrieved)
        doc_chunks = retrieve_document_chunks(query, doc_id=str(document.id), k=15)

        # 2. Rerank
        policy_chunks = rerank_chunks(query, policy_chunks_raw, top_k=report.top_k_reranked)

        # 3. LLM Analysis (or mock if no API key)
        has_llm_key = bool(settings.GEMINI_API_KEY or settings.OPENAI_API_KEY)
        if has_llm_key:
            result = run_compliance_analysis(document, policy_chunks, doc_chunks)
        else:
            logger.warning("No LLM API key — using mock analysis result")
            result = mock_analysis_result(document.name)

        # 4. Save violations
        for v_data in result.get('violations', []):
            Violation.objects.create(
                report=report,
                regulation_id=v_data.get('regulation_id', ''),
                title=v_data.get('title', ''),
                description=v_data.get('description', ''),
                risk=v_data.get('risk', 'low'),
                evidence=v_data.get('evidence', ''),
                citation=v_data.get('citation', ''),
                corrective_action=v_data.get('corrective_action', ''),
                category=v_data.get('category', ''),
            )

        # 5. Generate PDF
        pdf_bytes = generate_pdf_report(result, document.name)
        pdf_filename = f"report_{report.id}.pdf"
        report.pdf_report.save(pdf_filename, ContentFile(pdf_bytes), save=False)

        # 6. Update report
        report.status = ComplianceReport.Status.COMPLETED
        report.compliance_score = result.get('compliance_score', 0)
        report.summary = result.get('summary', '')
        report.violations_json = result.get('violations', [])
        report.citations_json = result.get('citations', [])
        report.cot_reasoning = result.get('cot_reasoning', '')
        report.llm_model = result.get('llm_model', '')
        report.embedding_model = result.get('embedding_model', '')
        report.processing_time_ms = result.get('processing_time_ms')
        report.completed_at = timezone.now()
        report.save()
        logger.info(f"Report {report.id} completed with score={report.compliance_score}")
