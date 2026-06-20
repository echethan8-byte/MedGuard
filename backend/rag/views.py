"""
rag/views.py — Compliance audit endpoint and report management.
"""
import logging
import re
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView

from core.models import Document, ComplianceReport, Violation, AuditLog
from .serializers import ComplianceReportSerializer, RunAuditSerializer, QARequestSerializer

logger = logging.getLogger('medguard')


def _rank_chunks_for_query(chunks, query, limit):
    terms = [term for term in re.findall(r'\w+', query.lower()) if len(term) > 2]

    def score(chunk):
        text = chunk.get('text', '').lower()
        return sum(text.count(term) for term in terms)

    ranked = sorted(chunks, key=score, reverse=True)
    return ranked[:limit]


class AuditViewSet(viewsets.ReadOnlyModelViewSet):
    """List and retrieve compliance reports.

    For local development the list endpoint is open (AllowAny) so the
    frontend can display existing reports without requiring a JWT.
    """
    permission_classes = [AllowAny]
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


class DocumentQAView(APIView):
    """POST /api/rag/qa/ — Answer questions against an uploaded document."""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = QARequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        query = serializer.validated_data['query'].strip()
        document_id = serializer.validated_data.get('document_id')

        if not query:
            return Response({'error': 'Query text is required.'}, status=400)

        document = None
        if document_id:
            try:
                document = Document.objects.get(id=document_id)
            except Document.DoesNotExist:
                return Response({'error': 'Document not found.'}, status=404)
        else:
            document = Document.objects.filter(status=Document.Status.INDEXED).order_by('-created_at').first()
            if not document:
                return Response({'error': 'No indexed document available for QA.'}, status=404)

        if document.status != Document.Status.INDEXED:
            return Response({'error': 'Document is not indexed.'}, status=400)

        from django.conf import settings
        from core.utils import clean_text, chunk_text, extract_text
        from rag.retriever import retrieve_document_chunks
        from rag.analyzer import run_document_qa

        try:
            document_chunks = retrieve_document_chunks(query, doc_id=str(document.id), k=settings.RAG_TOP_K_RETRIEVE)
            # If Chroma returns an empty list (document not indexed in Chroma), fallback to file-based chunking
            if not document_chunks:
                raise ValueError('No chunks returned from Chroma')
        except Exception as exc:
            logger.warning(f"Chroma retrieval missing or failed for doc={document.id}: {exc}; falling back to file chunking")
            cleaned_text = clean_text(extract_text(document.file.path))
            chunks = chunk_text(
                cleaned_text,
                chunk_size=settings.CHUNK_SIZE,
                chunk_overlap=settings.CHUNK_OVERLAP,
            )
            document_chunks = [
                {
                    'text': chunk['text'],
                    'metadata': {
                        'source': document.name,
                        'doc_id': str(document.id),
                        'chunk_index': chunk['chunk_index'],
                    },
                    'score': None,
                }
                for chunk in _rank_chunks_for_query(chunks, query, settings.RAG_TOP_K_RETRIEVE)
            ]
        # If still no chunks after fallback, inform the caller
        if not document_chunks:
            return Response({'error': 'No document chunks found after fallback. Ensure the document file contains readable text.'}, status=400)

        result = run_document_qa(document, document_chunks, query)

        AuditLog.objects.create(
            user=request.user if request.user.is_authenticated else None,
            action=AuditLog.Action.QA,
            description=f'Document QA query for {document.name}',
            metadata={'document_id': str(document.id), 'query': query},
            ip_address=request.META.get('REMOTE_ADDR'),
        )

        return Response(result, status=200)
